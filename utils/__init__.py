"""
Shared utilities for SparkSage bot

Contains common helper functions used across cogs and the main bot module.
"""

from __future__ import annotations
import time


import config
import providers
import db as database
from utils.rate_limiter import rate_limiter

MAX_HISTORY = 20


async def get_history(channel_id: int) -> list[dict]:
    """Get conversation history for a channel from the database."""
    messages = await database.get_messages(str(channel_id), limit=MAX_HISTORY)
    return [{"role": m["role"], "content": m["content"]} for m in messages]


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
        response, provider_name = providers.chat(
            history,
            system_prompt,
            preferred_provider=channel_provider,
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
            latency_ms=latency_ms,
        )

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
    user_role_ids = [str(role.id) for role in interaction.user.roles]
    
    # Admins always have access
    if interaction.user.guild_permissions.administrator:
        return True
    
    return await database.check_permission(command_name, guild_id, user_role_ids)
