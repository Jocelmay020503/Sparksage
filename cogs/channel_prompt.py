"""
Channel Prompt Cog - Custom System Prompts Per Channel

Provides commands to set and manage channel-specific AI system prompts.
"""

from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import config
import db as database


class ChannelPrompt(commands.Cog):
    """Commands for managing channel-specific AI prompts."""

    prompt_group = app_commands.Group(
        name="prompt",
        description="Manage custom AI prompts for this channel"
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @prompt_group.command(name="set", description="Set a custom AI prompt for this channel")
    @app_commands.describe(prompt_text="The custom system prompt")
    async def prompt_set(
        self,
        interaction: discord.Interaction,
        prompt_text: str,
    ):
        """Set a custom AI prompt for this channel."""
        # Check if user has manage channels permission
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "❌ You need the 'Manage Channels' permission to use this command.",
                ephemeral=True
            )
            return

        channel_id = str(interaction.channel_id)
        guild_id = str(interaction.guild_id) if interaction.guild else None

        if len(prompt_text) > 2000:
            await interaction.response.send_message(
                "❌ Prompt text must be 2000 characters or less.",
                ephemeral=True
            )
            return

        try:
            await database.set_channel_prompt(channel_id, guild_id, prompt_text)
            
            # Create a preview embed
            embed = discord.Embed(
                title="✅ Channel Prompt Updated",
                description="This channel now has a custom AI personality!",
                color=discord.Color.green()
            )
            
            preview = prompt_text[:300] + "..." if len(prompt_text) > 300 else prompt_text
            embed.add_field(
                name="Custom Prompt",
                value=f"```\n{preview}\n```",
                inline=False
            )
            embed.add_field(
                name="Effect",
                value="All AI responses in this channel will now use this custom prompt.",
                inline=False
            )
            embed.set_footer(text=f"Set by {interaction.user.display_name}")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to set channel prompt: {str(e)}",
                ephemeral=True
            )

    @prompt_group.command(name="reset", description="Reset to the global AI prompt")
    async def prompt_reset(
        self,
        interaction: discord.Interaction,
    ):
        """Reset this channel to use the global system prompt."""
        # Check if user has manage channels permission
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "❌ You need the 'Manage Channels' permission to use this command.",
                ephemeral=True
            )
            return

        channel_id = str(interaction.channel_id)

        try:
            # Check if channel has a custom prompt
            current_prompt = await database.get_channel_prompt(channel_id)
            
            if not current_prompt:
                await interaction.response.send_message(
                    "ℹ️ This channel is already using the global system prompt.",
                    ephemeral=True
                )
                return

            await database.remove_channel_prompt(channel_id)

            embed = discord.Embed(
                title="🔄 Channel Prompt Reset",
                description="This channel will now use the global system prompt.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Global Prompt",
                value=f"```\n{config.SYSTEM_PROMPT[:300]}...\n```",
                inline=False
            )
            embed.set_footer(text=f"Reset by {interaction.user.display_name}")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to reset channel prompt: {str(e)}",
                ephemeral=True
            )

    @prompt_group.command(name="show", description="Show the current AI prompt for this channel")
    async def prompt_show(
        self,
        interaction: discord.Interaction,
    ):
        """Show the current AI prompt for this channel."""
        channel_id = str(interaction.channel_id)

        try:
            current_prompt = await database.get_channel_prompt(channel_id)

            if current_prompt:
                embed = discord.Embed(
                    title="🎨 Current Channel Prompt",
                    description="This channel has a custom AI personality:",
                    color=discord.Color.purple()
                )
                
                preview = current_prompt[:1900] + "..." if len(current_prompt) > 1900 else current_prompt
                embed.add_field(
                    name="Custom Prompt",
                    value=f"```\n{preview}\n```",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="🌐 Current Channel Prompt",
                    description="This channel uses the global system prompt:",
                    color=discord.Color.blue()
                )
                
                preview = config.SYSTEM_PROMPT[:1900] + "..." if len(config.SYSTEM_PROMPT) > 1900 else config.SYSTEM_PROMPT
                embed.add_field(
                    name="Global Prompt",
                    value=f"```\n{preview}\n```",
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to retrieve channel prompt: {str(e)}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Load the ChannelPrompt cog."""
    await bot.add_cog(ChannelPrompt(bot))
