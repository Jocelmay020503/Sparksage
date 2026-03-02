"""Channel provider override management cog."""

from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import config
import db


class ChannelProvider(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="channel-provider", description="Manage per-channel AI provider override")
    @app_commands.describe(
        action="Action to perform",
        provider="Provider to use for this channel (required for set)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="set", value="set"),
            app_commands.Choice(name="reset", value="reset"),
            app_commands.Choice(name="show", value="show"),
        ],
        provider=[
            app_commands.Choice(name="Gemini", value="gemini"),
            app_commands.Choice(name="Groq", value="groq"),
            app_commands.Choice(name="OpenRouter", value="openrouter"),
            app_commands.Choice(name="Anthropic", value="anthropic"),
            app_commands.Choice(name="OpenAI", value="openai"),
        ],
    )
    @app_commands.default_permissions(manage_channels=True)
    async def channel_provider(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        provider: app_commands.Choice[str] | None = None,
    ):
        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        channel_id = str(interaction.channel_id)
        guild_id = str(interaction.guild_id)

        if action.value == "set":
            if provider is None:
                await interaction.response.send_message(
                    "Please choose a provider when using `set`.",
                    ephemeral=True,
                )
                return

            provider_name = provider.value
            if provider_name not in config.PROVIDERS:
                await interaction.response.send_message(
                    f"Unknown provider: `{provider_name}`",
                    ephemeral=True,
                )
                return

            await db.set_channel_provider(channel_id, guild_id, provider_name)
            display_name = config.PROVIDERS[provider_name]["name"]
            await interaction.response.send_message(
                f"✅ This channel now uses **{display_name}** as the preferred provider.",
                ephemeral=True,
            )
            return

        if action.value == "reset":
            await db.remove_channel_provider(channel_id)
            await interaction.response.send_message(
                "✅ Channel provider override removed. This channel now follows global provider settings.",
                ephemeral=True,
            )
            return

        current = await db.get_channel_provider(channel_id)
        if current:
            display_name = config.PROVIDERS.get(current, {}).get("name", current)
            await interaction.response.send_message(
                f"Current channel provider override: **{display_name}** (`{current}`)",
                ephemeral=True,
            )
        else:
            global_name = config.PROVIDERS.get(config.AI_PROVIDER, {}).get("name", config.AI_PROVIDER)
            await interaction.response.send_message(
                f"No channel override set. Using global provider: **{global_name}** (`{config.AI_PROVIDER}`).",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelProvider(bot))
