"""Channel provider override management cog."""

from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import config
import db


class ChannelProvider(commands.Cog):
    """Commands for managing per-channel AI provider overrides."""

    channel_provider_group = app_commands.Group(
        name="channel-provider",
        description="Manage per-channel AI provider override",
        default_permissions=discord.Permissions(manage_channels=True)
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @channel_provider_group.command(name="set", description="Set AI provider for this channel")
    @app_commands.describe(provider="Provider to use for this channel")
    @app_commands.choices(provider=[
        app_commands.Choice(name="Gemini", value="gemini"),
        app_commands.Choice(name="Groq", value="groq"),
        app_commands.Choice(name="OpenRouter", value="openrouter"),
        app_commands.Choice(name="Anthropic", value="anthropic"),
        app_commands.Choice(name="OpenAI", value="openai"),
    ])
    async def channel_provider_set(
        self,
        interaction: discord.Interaction,
        provider: app_commands.Choice[str],
    ):
        """Set a specific AI provider for this channel."""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        channel_id = str(interaction.channel_id)
        guild_id = str(interaction.guild_id)
        provider_name = provider.value

        if provider_name not in config.PROVIDERS:
            await interaction.response.send_message(
                f"❌ Unknown provider: `{provider_name}`",
                ephemeral=True,
            )
            return

        try:
            await db.set_channel_provider(channel_id, guild_id, provider_name)
            display_name = config.PROVIDERS[provider_name]["name"]
            
            embed = discord.Embed(
                title="✅ Channel Provider Override Set",
                description=f"This channel now uses **{display_name}** as the preferred AI provider.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Provider",
                value=f"`{provider_name}`",
                inline=True
            )
            embed.add_field(
                name="Effect",
                value="All AI responses in this channel will prioritize this provider.",
                inline=False
            )
            embed.set_footer(text=f"Set by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to set channel provider: {str(e)}",
                ephemeral=True,
            )

    @channel_provider_group.command(name="reset", description="Reset to global provider settings")
    async def channel_provider_reset(
        self,
        interaction: discord.Interaction,
    ):
        """Remove channel-specific provider override."""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        channel_id = str(interaction.channel_id)

        try:
            # Check if channel has an override
            current = await db.get_channel_provider(channel_id)
            
            if not current:
                await interaction.response.send_message(
                    "ℹ️ This channel is already using the global provider settings.",
                    ephemeral=True,
                )
                return

            await db.remove_channel_provider(channel_id)
            
            global_provider = config.AI_PROVIDER
            global_name = config.PROVIDERS.get(global_provider, {}).get("name", global_provider)
            
            embed = discord.Embed(
                title="🔄 Channel Provider Override Reset",
                description="This channel will now follow global provider settings.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Global Provider",
                value=f"**{global_name}** (`{global_provider}`)",
                inline=False
            )
            embed.set_footer(text=f"Reset by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to reset channel provider: {str(e)}",
                ephemeral=True,
            )

    @channel_provider_group.command(name="show", description="Show current provider for this channel")
    async def channel_provider_show(
        self,
        interaction: discord.Interaction,
    ):
        """Display the current AI provider for this channel."""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        channel_id = str(interaction.channel_id)

        try:
            current = await db.get_channel_provider(channel_id)
            
            if current:
                display_name = config.PROVIDERS.get(current, {}).get("name", current)
                embed = discord.Embed(
                    title="🎯 Channel Provider Override",
                    description=f"This channel has a custom provider override:",
                    color=discord.Color.purple()
                )
                embed.add_field(
                    name="Current Provider",
                    value=f"**{display_name}** (`{current}`)",
                    inline=False
                )
            else:
                global_provider = config.AI_PROVIDER
                global_name = config.PROVIDERS.get(global_provider, {}).get("name", global_provider)
                embed = discord.Embed(
                    title="🌐 Global Provider",
                    description="This channel uses the global provider settings:",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Current Provider",
                    value=f"**{global_name}** (`{global_provider}`)",
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to retrieve channel provider: {str(e)}",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelProvider(bot))
