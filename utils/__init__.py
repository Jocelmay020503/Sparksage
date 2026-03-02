"""
Shared utilities for SparkSage bot

Contains common helper functions used across cogs and the main bot module.
"""

from __future__ import annotations

import config
import providers
import db as database

MAX_HISTORY = 20


async def get_history(channel_id: int) -> list[dict]:
    """Get conversation history for a channel from the database."""
    messages = await database.get_messages(str(channel_id), limit=MAX_HISTORY)
    return [{"role": m["role"], "content": m["content"]} for m in messages]


async def ask_ai(channel_id: int, user_name: str, message: str) -> tuple[str, str]:
    """Send a message to AI and return (response, provider_name).
    
    Args:
        channel_id: Discord channel ID
        user_name: Display name of the user
        message: The message content
        
    Returns:
        Tuple of (response text, provider name used)
    """
    # Store user message in DB
    await database.add_message(str(channel_id), "user", f"{user_name}: {message}")

    history = await get_history(channel_id)

    # Check for channel-specific system prompt, fall back to global
    channel_prompt = await database.get_channel_prompt(str(channel_id))
    system_prompt = channel_prompt if channel_prompt else config.SYSTEM_PROMPT

    # Check for channel-specific provider override
    channel_provider = await database.get_channel_provider(str(channel_id))

    try:
        response, provider_name = providers.chat(
            history,
            system_prompt,
            preferred_provider=channel_provider,
        )
        # Store assistant response in DB
        await database.add_message(str(channel_id), "assistant", response, provider=provider_name)
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
