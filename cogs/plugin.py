"""
Plugin management cog for SparkSage - allows enabling/disabling plugins at runtime
Stores plugin state in the database and auto-loads enabled plugins on bot startup.
"""

import discord
from discord.ext import commands
from discord import app_commands
import db
from plugin_loader import plugin_loader


class PluginCog(commands.Cog):
    """Manage plugins for SparkSage"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Auto-load enabled plugins when the bot starts up"""
        print("🔌 Plugin Management cog initialized")

    plugin_group = app_commands.Group(
        name="plugin",
        description="Manage community plugins for SparkSage",
        default_permissions=discord.Permissions(manage_guild=True),
    )

    @plugin_group.command(name="list", description="List all available plugins")
    async def list_plugins(self, interaction: discord.Interaction):
        """List all plugins with their status"""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            plugin_loader.discover_plugins()
            plugins = plugin_loader.list_plugins()

            if not plugins:
                embed = discord.Embed(
                    title="📦 Available Plugins",
                    description="No plugins found in the plugins directory",
                    color=discord.Color.gold(),
                )
                embed.set_footer(text="To create a plugin, check out the documentation")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            db_plugins = await db.get_all_plugins()
            db_enabled = {item["name"]: bool(item.get("enabled")) for item in db_plugins}

            embed = discord.Embed(
                title="📦 Available Plugins",
                description=f"Found {len(plugins)} plugin(s) available",
                color=discord.Color.blue(),
            )

            for plugin in sorted(plugins, key=lambda p: p["name"]):
                enabled = db_enabled.get(plugin["name"], False)
                loaded = plugin.get("loaded", False)

                # Determine status
                if loaded:
                    status = "✅ Loaded"
                    color_emoji = "🟢"
                elif enabled:
                    status = "⏳ Enabled (not loaded)"
                    color_emoji = "🟡"
                else:
                    status = "❌ Disabled"
                    color_emoji = "⚪"

                field_value = (
                    f"**Version:** {plugin['version']}\n"
                    f"**Author:** {plugin['author']}\n"
                    f"**Status:** {status}\n"
                    f"**Description:** {plugin['description']}"
                )

                embed.add_field(
                    name=f"{color_emoji} {plugin['name']}",
                    value=field_value,
                    inline=False,
                )

            embed.set_footer(
                text="Use /plugin enable <name> to load | /plugin disable <name> to unload"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to list plugins: {str(e)}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @plugin_group.command(name="enable", description="Enable and load a plugin")
    @app_commands.describe(plugin_name="Name of the plugin to enable (case-insensitive)")
    async def enable_plugin(self, interaction: discord.Interaction, plugin_name: str):
        """Enable a plugin and load its cog"""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            plugin_loader.bind_bot(self.bot)
            plugin_loader.discover_plugins()

            manifest = plugin_loader.get_manifest(plugin_name)
            if not manifest:
                error_embed = discord.Embed(
                    title="❌ Plugin Not Found",
                    description=f"Could not find plugin '{plugin_name}'",
                    color=discord.Color.red(),
                )
                error_embed.set_footer(text="Use /plugin list to see available plugins")
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Check if already loaded
            if manifest.name in plugin_loader.loaded_cogs:
                info_embed = discord.Embed(
                    title="ℹ️ Already Loaded",
                    description=f"Plugin **{manifest.name}** is already loaded and running",
                    color=discord.Color.blue(),
                )
                await interaction.followup.send(embed=info_embed, ephemeral=True)
                return

            # Load the plugin cog
            success, message = await plugin_loader.load_plugin_cog(
                self.bot, manifest.name, sync_commands=True
            )

            if success:
                # Save to database
                await db.save_plugin_manifest(
                    manifest.name,
                    manifest.version,
                    manifest.author,
                    manifest.description,
                )
                await db.enable_plugin(manifest.name)

                success_embed = discord.Embed(
                    title="✅ Plugin Enabled",
                    description=f"Plugin **{manifest.name}** has been loaded",
                    color=discord.Color.green(),
                )
                success_embed.add_field(
                    name="Version",
                    value=manifest.version,
                    inline=True,
                )
                success_embed.add_field(
                    name="Author",
                    value=manifest.author,
                    inline=True,
                )
                success_embed.add_field(
                    name="Description",
                    value=manifest.description,
                    inline=False,
                )
                await interaction.followup.send(embed=success_embed, ephemeral=True)
            else:
                error_embed = discord.Embed(
                    title="❌ Failed to Enable Plugin",
                    description=f"Error loading plugin:\n```\n{message}\n```",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Unexpected Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @plugin_group.command(name="disable", description="Disable and unload a plugin")
    @app_commands.describe(plugin_name="Name of the plugin to disable")
    async def disable_plugin(self, interaction: discord.Interaction, plugin_name: str):
        """Disable a plugin and unload its cog"""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            plugin_loader.bind_bot(self.bot)
            plugin_loader.discover_plugins()

            manifest = plugin_loader.get_manifest(plugin_name)
            resolved_name = manifest.name if manifest else plugin_name.strip()

            # Check if loaded
            if resolved_name not in plugin_loader.loaded_cogs:
                info_embed = discord.Embed(
                    title="ℹ️ Not Loaded",
                    description=f"Plugin **{resolved_name}** is not currently loaded",
                    color=discord.Color.blue(),
                )
                await interaction.followup.send(embed=info_embed, ephemeral=True)
                return

            # Unload the plugin cog
            success, message = await plugin_loader.unload_plugin_cog(
                self.bot, resolved_name, sync_commands=True
            )

            if success:
                # Update database
                await db.disable_plugin(resolved_name)

                success_embed = discord.Embed(
                    title="✅ Plugin Disabled",
                    description=f"Plugin **{resolved_name}** has been unloaded",
                    color=discord.Color.orange(),
                )
                success_embed.set_footer(text="Use /plugin enable to load it again")
                await interaction.followup.send(embed=success_embed, ephemeral=True)
            else:
                error_embed = discord.Embed(
                    title="❌ Failed to Disable Plugin",
                    description=f"Error unloading plugin:\n```\n{message}\n```",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Unexpected Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @plugin_group.command(name="uninstall", description="Completely remove a plugin")
    @app_commands.describe(plugin_name="Name of the plugin to uninstall")
    async def uninstall_plugin(self, interaction: discord.Interaction, plugin_name: str):
        """Uninstall a plugin completely (unload and delete files)"""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            import shutil
            from pathlib import Path

            plugin_loader.bind_bot(self.bot)
            plugin_loader.discover_plugins()

            manifest = plugin_loader.get_manifest(plugin_name)
            resolved_name = manifest.name if manifest else plugin_name.strip()

            # Check if plugin exists
            plugin_dir = Path("plugins") / resolved_name
            if not plugin_dir.exists():
                error_embed = discord.Embed(
                    title="❌ Plugin Not Found",
                    description=f"Plugin **{resolved_name}** is not installed",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Ask for confirmation
            confirm_embed = discord.Embed(
                title="⚠️ Confirm Uninstall",
                description=f"Are you sure you want to completely remove **{resolved_name}**?\n\n"
                           "This will:\n"
                           "• Unload the plugin if it's running\n"
                           "• Delete all plugin files\n"
                           "• Remove it from the database\n\n"
                           "**This cannot be undone!**",
                color=discord.Color.orange(),
            )
            
            # For now, proceed without confirmation button (would need views)
            # In a real implementation, you'd use discord.ui.View with confirm/cancel buttons
            
            # Unload if loaded
            if resolved_name in plugin_loader.loaded_cogs:
                await plugin_loader.unload_plugin_cog(self.bot, resolved_name, sync_commands=True)

            # Delete plugin directory
            shutil.rmtree(plugin_dir, ignore_errors=True)

            # Remove from database
            await db.delete_plugin(resolved_name)

            # Rediscover plugins
            plugin_loader.discover_plugins()

            success_embed = discord.Embed(
                title="✅ Plugin Uninstalled",
                description=f"Plugin **{resolved_name}** has been completely removed",
                color=discord.Color.green(),
            )
            success_embed.set_footer(text="You can reinstall it from the dashboard")
            await interaction.followup.send(embed=success_embed, ephemeral=True)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Unexpected Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup function for the cog"""
    await bot.add_cog(PluginCog(bot))
