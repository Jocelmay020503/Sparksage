"""
Command permission management cog for role-based access control.
"""

from discord.ext import commands
from discord import app_commands
import discord
import db


def _normalize_permission_command(command_name: str) -> str:
    """Canonical permission command name used across API and bot checks."""
    normalized = " ".join((command_name or "").strip().split()).lower()
    while normalized.startswith("/"):
        normalized = normalized[1:].lstrip()
    return normalized


class Permissions(commands.Cog):
    """Manage command permissions and role-based access control."""
    
    permissions_group = app_commands.Group(name="permissions", description="Manage command permissions")

    def __init__(self, bot):
        self.bot = bot

    @permissions_group.command(name="set", description="Require a role to use a command")
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
        normalized_command = _normalize_permission_command(command)
        if not normalized_command:
            await interaction.response.send_message("❌ Command name cannot be empty.", ephemeral=True)
            return
        
        # Check if command exists
        available_commands = {cmd.name.lower() for cmd in self.bot.tree.get_commands()}
        available_commands.update(
            cmd.qualified_name.lower()
            for cmd in self.bot.tree.walk_commands()
            if isinstance(cmd, app_commands.Command)
        )

        if normalized_command not in available_commands:
            available_display = ", ".join(f"`{c}`" for c in sorted(available_commands))
            await interaction.response.send_message(
                f"❌ Command `{normalized_command}` not found. Available commands: {available_display}",
                ephemeral=True
            )
            return

        await db.add_permission(normalized_command, guild_id, role_id)
        await interaction.response.send_message(
            f"✅ Role {role.mention} is now required to use `/{normalized_command}`",
            ephemeral=True
        )

    @permissions_group.command(name="remove", description="Remove a role requirement from a command")
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
        normalized_command = _normalize_permission_command(command)
        if not normalized_command:
            await interaction.response.send_message("❌ Command name cannot be empty.", ephemeral=True)
            return

        deleted = await db.delete_permission(normalized_command, guild_id, role_id)
        if deleted:
            await interaction.response.send_message(
                f"✅ Role {role.mention} no longer required for `/{normalized_command}`",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ No permission found for `/{normalized_command}` with role {role.mention}",
                ephemeral=True
            )

    @permissions_group.command(name="list", description="List all command permissions")
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
