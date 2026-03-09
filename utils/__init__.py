"""
Shared utilities for SparkSage bot

Contains common helper functions used across cogs and the main bot module.
"""

from __future__ import annotations
import time
import discord


import config
import providers
import db as database
from utils.cost_calculator import calculate_cost
from utils.rate_limiter import rate_limiter

MAX_HISTORY = 20


async def get_history(channel_id: int) -> list[dict]:
    """Get conversation history for a channel from the database."""
    messages = await database.get_messages(str(channel_id), limit=MAX_HISTORY)
    return [{"role": m["role"], "content": m["content"]} for m in messages]


async def log_cost_usage_event(
    provider_name: str,
    usage: dict[str, int] | None,
    guild_id: str | None,
    user_id: str | None,
):
    """Persist cost usage to the database for dashboard reporting."""
    if not guild_id or not user_id or not usage:
        return

    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens))
    cost_usd = calculate_cost(provider_name, input_tokens, output_tokens)

    try:
        await database.log_cost_usage(
            provider=provider_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            guild_id=guild_id,
            user_id=user_id,
        )
    except Exception as e:
        # Cost logging must not block normal bot responses.
        print(f"⚠️ Failed to log cost usage: {e}")


async def ask_ai(
    channel_id: int,
    user_name: str,
    message: str,
    custom_system_prompt: str | None = None,
    interaction_type: str | None = None,
    guild_id: str | None = None,
    user_id: str | None = None,
) -> tuple[str, str]:
    """Send a message to AI and return (response_text, provider_name).
    
    Args:
        channel_id: Discord channel ID
        user_name: Display name of the user
        message: The message content
        custom_system_prompt: Optional custom system prompt to override default/channel-specific prompts
        interaction_type: Optional type of interaction (e.g., "code_review", "translation")
            guild_id: Optional guild/server ID for analytics
            user_id: Optional user ID for analytics
        
    Returns:
        Tuple of (response text, provider name used)
    """
    # Rate limiting (per user and per guild per minute)
    allowed, limit_message = await rate_limiter.check_and_record(
        user_id=user_id,
        guild_id=guild_id,
        user_limit=config.RATE_LIMIT_USER,
        guild_limit=config.RATE_LIMIT_GUILD,
    )
    if not allowed:
        await database.record_analytics_event(
            event_type="rate_limited",
            guild_id=guild_id,
            channel_id=str(channel_id),
            user_id=user_id,
        )
        return limit_message or "⏳ Rate limit reached. Please try again shortly.", "rate-limit"

    # Store user message in DB
    await database.add_message(
        str(channel_id), 
        "user", 
        f"{user_name}: {message}",
        interaction_type=interaction_type
    )

    history = await get_history(channel_id)

    # Determine system prompt priority: custom > channel-specific > global
    if custom_system_prompt:
        system_prompt = custom_system_prompt
    else:
        channel_prompt = await database.get_channel_prompt(str(channel_id))
        system_prompt = channel_prompt if channel_prompt else config.SYSTEM_PROMPT

    # Check for channel-specific provider override
    channel_provider = await database.get_channel_provider(str(channel_id))
    start_time = time.time()


    try:
        response, provider_name, usage = providers.chat(
            history,
            system_prompt,
            preferred_provider=channel_provider,
            include_usage=True,
        )
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Store assistant response in DB
        await database.add_message(
            str(channel_id), 
            "assistant", 
            response, 
            provider=provider_name,
            interaction_type=interaction_type
        )

        # Record analytics event
        event_type = interaction_type if interaction_type else "command"
        await database.record_analytics_event(
            event_type=event_type,
            guild_id=guild_id,
            channel_id=str(channel_id),
            user_id=user_id,
            provider=provider_name,
            tokens_used=usage.get("total_tokens"),
            latency_ms=latency_ms,
        )

        # Persist cost usage for cost dashboard metrics.
        await log_cost_usage_event(provider_name, usage, guild_id, user_id)

        return response, provider_name
    except RuntimeError as e:
        return f"Sorry, all AI providers failed:\n{e}", "none"


async def check_command_permission(interaction, command_name: str) -> bool:
    """Check if a user has permission to use a command based on roles.
    
    Args:
        interaction: Discord interaction object
        command_name: Name of the command to check
        
    Returns:
        True if user has permission, False otherwise
    """
    if not interaction.guild:
        # DMs are always allowed
        return True
    
    guild_id = str(interaction.guild_id)

    member = interaction.user
    member_roles = list(getattr(member, "roles", []))

    # Fallback for partial interaction members where roles may be missing.
    if not member_roles and interaction.guild and getattr(member, "id", None):
        cached_member = interaction.guild.get_member(member.id)
        if cached_member is not None:
            member_roles = list(getattr(cached_member, "roles", []))

    user_role_ids = [str(role.id) for role in member_roles if getattr(role, "id", None) is not None]

    # Command restrictions are strict: users must match configured roles.
    return await database.check_permission(command_name, guild_id, user_role_ids)


async def safe_defer(interaction, *, ephemeral: bool = False):
    """Defer an interaction only if it has not already been acknowledged."""
    if interaction.response.is_done():
        return
    try:
        await interaction.response.defer(ephemeral=ephemeral)
    except discord.HTTPException as e:
        # Another handler/process may have already acknowledged this interaction.
        if getattr(e, "code", None) == 40060:
            return
        raise


async def safe_ephemeral(interaction, content: str):
    """Send an ephemeral response regardless of interaction response state."""
    if interaction.response.is_done():
        await interaction.followup.send(content, ephemeral=True)
        return
    try:
        await interaction.response.send_message(content, ephemeral=True)
    except discord.HTTPException as e:
        if getattr(e, "code", None) == 40060:
            await interaction.followup.send(content, ephemeral=True)
            return
        raise
