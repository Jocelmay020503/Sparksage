"""
Command permission management cog for role-based access control.
"""

from discord.ext import commands
from discord import app_commands
import discord
import db


class Permissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="permissions-set", description="Require a role to use a command")
    @app_commands.describe(
        command="Command name (e.g., 'ask', 'review', 'summarize')",
        role="Role required to use this command"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def permissions_set(self, interaction: discord.Interaction, command: str, role: discord.Role):
        """Set a role permission for a command."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        role_id = str(role.id)
        
        # Check if command exists
        bot_commands = [cmd.name for cmd in self.bot.tree.get_commands()]
        if command not in bot_commands:
            await interaction.response.send_message(
                f"❌ Command `{command}` not found. Available commands: {', '.join(f'`{c}`' for c in bot_commands)}",
                ephemeral=True
            )
            return

        await db.add_permission(command, guild_id, role_id)
        await interaction.response.send_message(
            f"✅ Role {role.mention} is now required to use `/{command}`",
            ephemeral=True
        )

    @app_commands.command(name="permissions-remove", description="Remove a role requirement from a command")
    @app_commands.describe(
        command="Command name",
        role="Role to remove"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def permissions_remove(self, interaction: discord.Interaction, command: str, role: discord.Role):
        """Remove a role permission for a command."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        role_id = str(role.id)

        deleted = await db.delete_permission(command, guild_id, role_id)
        if deleted:
            await interaction.response.send_message(
                f"✅ Role {role.mention} no longer required for `/{command}`",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ No permission found for `/{command}` with role {role.mention}",
                ephemeral=True
            )

    @app_commands.command(name="permissions-list", description="List all command permissions")
    async def permissions_list(self, interaction: discord.Interaction):
        """List all command permissions for this server."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        perms = await db.list_permissions(guild_id=guild_id)

        if not perms:
            await interaction.response.send_message(
                "No command restrictions set. All commands are available to everyone.",
                ephemeral=True
            )
            return

        # Group by command
        by_command = {}
        for perm in perms:
            cmd = perm["command_name"]
            if cmd not in by_command:
                by_command[cmd] = []
            by_command[cmd].append(perm["role_id"])

        # Build response
        lines = ["**Command Permissions:**\n"]
        for cmd, role_ids in sorted(by_command.items()):
            role_mentions = []
            for role_id in role_ids:
                role = interaction.guild.get_role(int(role_id))
                role_mentions.append(role.mention if role else f"`{role_id}`")
            lines.append(f"`/{cmd}` → {', '.join(role_mentions)}")

        await interaction.response.send_message("\n".join(lines), ephemeral=True)


async def setup(bot):
    await bot.add_cog(Permissions(bot))
