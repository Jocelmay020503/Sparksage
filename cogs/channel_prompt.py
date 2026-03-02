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

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="prompt", description="Manage custom AI prompts for this channel")
    @app_commands.describe(
        action="Action to perform: set or reset",
        prompt_text="The custom system prompt (required for 'set')"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="set", value="set"),
        app_commands.Choice(name="reset", value="reset"),
        app_commands.Choice(name="show", value="show"),
    ])
    async def prompt(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        prompt_text: str | None = None,
    ):
        """Set, reset, or show custom AI prompt for this channel."""
        # Check if user has manage channels permission
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "❌ You need the 'Manage Channels' permission to use this command.",
                ephemeral=True
            )
            return

        channel_id = str(interaction.channel_id)
        guild_id = str(interaction.guild_id) if interaction.guild else None

        if action.value == "set":
            if not prompt_text:
                await interaction.response.send_message(
                    "❌ Please provide a custom prompt text when using the 'set' action.",
                    ephemeral=True
                )
                return

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

        elif action.value == "reset":
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

        elif action.value == "show":
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
