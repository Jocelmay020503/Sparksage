from discord.ext import commands
from discord import app_commands
import discord

import db
from utils.plugin_loader import get_plugin_loader


class PluginManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="plugin-list", description="List available plugins")
    async def plugin_list(self, interaction: discord.Interaction):
        loader = get_plugin_loader()
        discovered = loader.discover_plugins()
        installed = await db.list_plugins()
        installed_by_name = {plugin["name"]: plugin for plugin in installed}

        if not discovered:
            await interaction.response.send_message(
                "No plugins found in the `plugins/` directory.",
                ephemeral=True,
            )
            return

        lines = ["**Available Plugins**\n"]
        for name in discovered:
            info = loader.get_plugin_info(name)
            if not info:
                continue
            state = installed_by_name.get(name)
            if state and state.get("enabled"):
                badge = "🟢 enabled"
            elif state:
                badge = "🟡 installed"
            else:
                badge = "⚪ available"
            lines.append(
                f"- `{name}` v{info.get('version', '1.0.0')} by {info.get('author', 'Unknown')} — {badge}"
            )

        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="plugin-install", description="Install a plugin")
    @app_commands.describe(name="Plugin folder name inside plugins/")
    @app_commands.default_permissions(manage_guild=True)
    async def plugin_install(self, interaction: discord.Interaction, name: str):
        loader = get_plugin_loader()
        info = loader.get_plugin_info(name)
        if not info:
            await interaction.response.send_message(
                f"❌ Plugin `{name}` not found.",
                ephemeral=True,
            )
            return

        await db.upsert_plugin(
            name,
            info.get("version", "1.0.0"),
            info.get("author", "Unknown"),
            info.get("description", ""),
            enabled=False,
        )
        await interaction.response.send_message(
            f"✅ Installed `{name}`. Use `/plugin-enable name:{name}` to enable it.",
            ephemeral=True,
        )

    @app_commands.command(name="plugin-enable", description="Enable an installed plugin")
    @app_commands.describe(name="Installed plugin name")
    @app_commands.default_permissions(manage_guild=True)
    async def plugin_enable(self, interaction: discord.Interaction, name: str):
        plugin = await db.get_plugin(name)
        if not plugin:
            await interaction.response.send_message(
                f"❌ Plugin `{name}` is not installed.",
                ephemeral=True,
            )
            return

        await db.set_plugin_enabled(name, True)
        await interaction.response.send_message(
            f"✅ Enabled `{name}`. Restart the bot to load this plugin.",
            ephemeral=True,
        )

    @app_commands.command(name="plugin-disable", description="Disable an installed plugin")
    @app_commands.describe(name="Installed plugin name")
    @app_commands.default_permissions(manage_guild=True)
    async def plugin_disable(self, interaction: discord.Interaction, name: str):
        updated = await db.set_plugin_enabled(name, False)
        if not updated:
            await interaction.response.send_message(
                f"❌ Plugin `{name}` is not installed.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ Disabled `{name}`. Restart the bot to unload this plugin.",
            ephemeral=True,
        )

    @app_commands.command(name="plugin-uninstall", description="Uninstall a plugin")
    @app_commands.describe(name="Installed plugin name")
    @app_commands.default_permissions(manage_guild=True)
    async def plugin_uninstall(self, interaction: discord.Interaction, name: str):
        deleted = await db.delete_plugin(name)
        if not deleted:
            await interaction.response.send_message(
                f"❌ Plugin `{name}` is not installed.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ Uninstalled `{name}`. Restart the bot if it is currently loaded.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(PluginManager(bot))
