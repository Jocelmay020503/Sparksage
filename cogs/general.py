"""
General Cog - Core SparkSage Commands

Contains the fundamental interaction commands:
- /ask: Ask SparkSage any question
- /clear: Clear conversation history for a channel
- /provider: Show active AI provider and fallback chain
"""

from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import config
import providers
import db as database
from utils import ask_ai, check_command_permission


class General(commands.Cog):
    """General commands for SparkSage interactions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ask", description="Ask SparkSage a question")
    @app_commands.describe(question="Your question for SparkSage")
    async def ask(self, interaction: discord.Interaction, question: str):
        """Ask SparkSage a question and get a response."""
        # Check permissions
        if not await check_command_permission(interaction, "ask"):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return
        
        await interaction.response.defer()
        response, provider_name = await ask_ai(
            interaction.channel_id,
            interaction.user.display_name,
            question,
            guild_id=str(interaction.guild_id) if interaction.guild_id else None,
            user_id=str(interaction.user.id),
        )
        provider_label = config.PROVIDERS.get(provider_name, {}).get("name", provider_name)
        footer = f"\n-# Powered by {provider_label}"

        for i in range(0, len(response), 1900):
            chunk = response[i : i + 1900]
            if i + 1900 >= len(response):
                chunk += footer
            await interaction.followup.send(chunk)

    @app_commands.command(
        name="clear", description="Clear SparkSage's conversation memory for this channel"
    )
    async def clear(self, interaction: discord.Interaction):
        """Clear the conversation history for the current channel."""
        # Check permissions
        if not await check_command_permission(interaction, "clear"):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return
        
        await database.clear_messages(str(interaction.channel_id))
        await interaction.response.send_message("Conversation history cleared!")

    @app_commands.command(
        name="provider",
        description="Show which AI provider SparkSage is currently using",
    )
    async def provider(self, interaction: discord.Interaction):
        """Display the current AI provider and fallback chain."""
        primary = config.AI_PROVIDER
        provider_info = config.PROVIDERS.get(primary, {})
        available = providers.get_available_providers()

        msg = f"**Current Provider:** {provider_info.get('name', primary)}\n"
        msg += f"**Model:** `{provider_info.get('model', '?')}`\n"
        msg += f"**Free:** {'Yes' if provider_info.get('free') else 'No (paid)'}\n"
        msg += f"**Fallback Chain:** {' -> '.join(available)}"
        await interaction.response.send_message(msg)


async def setup(bot: commands.Bot):
    """Load the General cog."""
    await bot.add_cog(General(bot))
