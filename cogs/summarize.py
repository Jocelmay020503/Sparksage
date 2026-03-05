"""
Summarize Cog - Conversation Summarization

Contains commands for summarizing discussions:
- /summarize: Summarize recent channel conversation
"""

from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import config
from utils import ask_ai, get_history, check_command_permission


class Summarize(commands.Cog):
    """Commands for summarizing conversations."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="summarize",
        description="Summarize the recent conversation in this channel",
    )
    async def summarize(self, interaction: discord.Interaction):
        """Create a summary of the channel's recent conversation."""
        # Check permissions
        if not await check_command_permission(interaction, "summarize"):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return
        
        await interaction.response.defer()
        history = await get_history(interaction.channel_id)
        if not history:
            await interaction.followup.send("No conversation history to summarize.")
            return

        summary_prompt = "Please summarize the key points from this conversation so far in a concise bullet-point format."
        response, provider_name = await ask_ai(
            interaction.channel_id,
            interaction.user.display_name,
            summary_prompt,
            guild_id=str(interaction.guild_id) if interaction.guild_id else None,
            user_id=str(interaction.user.id),
        )
        await interaction.followup.send(f"**Conversation Summary:**\n{response}")


async def setup(bot: commands.Bot):
    """Load the Summarize cog."""
    await bot.add_cog(Summarize(bot))
