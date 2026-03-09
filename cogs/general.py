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
from utils import ask_ai, check_command_permission, safe_defer, safe_ephemeral


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
            await safe_ephemeral(interaction, "❌ You don't have permission to use this command.")
            return
        
        await safe_defer(interaction)
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
            await safe_ephemeral(interaction, "❌ You don't have permission to use this command.")
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

    @app_commands.command(
        name="help",
        description="Display all available commands and their descriptions",
    )
    async def help(self, interaction: discord.Interaction):
        """Display a help message with commands based on user permissions."""
        # Check if user has admin/manage server permissions
        is_admin = False
        if interaction.guild and isinstance(interaction.user, discord.Member):
            is_admin = (
                interaction.user.guild_permissions.administrator
                or interaction.user.guild_permissions.manage_guild
                or interaction.user.guild_permissions.manage_channels
            )

        embed = discord.Embed(
            title="🤖 SparkSage Help Menu",
            description="A multi-AI Discord bot with powerful features. Here are your available commands:",
            color=discord.Color.blue()
        )

        # General Commands (Always visible)
        embed.add_field(
            name="💬 General Commands",
            value=(
                "`/ask <question>` - Ask SparkSage any question\n"
                "`/clear` - Clear conversation history for this channel\n"
                "`/provider` - Show current AI provider and fallback chain\n"
                "`/help` - Show this help menu"
            ),
            inline=False
        )

        # AI Features (Always visible)
        embed.add_field(
            name="🧠 AI Features",
            value=(
                "`/summarize [limit]` - Summarize recent messages in this channel\n"
                "`/review <code> [language]` - Get code review and suggestions\n"
                "`/translate <text> <target_language>` - Translate text to another language"
            ),
            inline=False
        )

        # Additional Info for basic users
        if not is_admin:
            embed.add_field(
                name="ℹ️ Additional Information",
                value=(
                    "**Mention me**: You can also mention @SparkSage to ask questions!\n"
                    "**More Features**: Contact your server admin for advanced features like channel prompts, FAQs, and plugins.\n"
                    "**Support**: For issues, contact your server admin."
                ),
                inline=False
            )
            embed.set_footer(text="SparkSage - Multi-AI Discord Bot | Basic User View")
        else:
            # Admin-only commands
            # Channel Management
            embed.add_field(
                name="⚙️ Channel Management",
                value=(
                    "`/prompt set <prompt>` - Set custom AI prompt for this channel\n"
                    "`/prompt show` - Show current channel prompt\n"
                    "`/prompt clear` - Remove custom prompt (use default)\n"
                    "`/channelprovider set <provider>` - Set AI provider for this channel\n"
                    "`/channelprovider show` - Show current channel provider\n"
                    "`/channelprovider clear` - Use default provider"
                ),
                inline=False
            )

            # FAQ Management
            embed.add_field(
                name="❓ FAQ Management",
                value=(
                    "`/faq add <question> <answer>` - Add a new FAQ entry\n"
                    "`/faq list` - List all FAQs for this server\n"
                    "`/faq get <question>` - Get answer for a specific FAQ\n"
                    "`/faq delete <faq_id>` - Delete a FAQ entry"
                ),
                inline=False
            )

            # Permission System
            embed.add_field(
                name="🔒 Permissions",
                value=(
                    "`/permissions set <command> <roles>` - Restrict command to specific roles\n"
                    "`/permissions remove <command> <role>` - Remove role restriction\n"
                    "`/permissions list` - List all command permissions"
                ),
                inline=False
            )

            # Plugin Management
            embed.add_field(
                name="🔌 Plugins",
                value=(
                    "`/plugin list` - List all available plugins\n"
                    "`/plugin enable <name>` - Enable a plugin\n"
                    "`/plugin disable <name>` - Disable a plugin\n"
                    "`/plugin info <name>` - Show plugin details"
                ),
                inline=False
            )

            # Moderation
            embed.add_field(
                name="🛡️ Moderation",
                value=(
                    "`/digest` - Generate and post daily activity summary\n"
                    "`/moderate <text>` - Check if text violates server rules"
                ),
                inline=False
            )

            # Additional Info for admins
            embed.add_field(
                name="ℹ️ Additional Information",
                value=(
                    "**Mention me**: You can also mention @SparkSage to ask questions!\n"
                    "**Dashboard**: Visit the web dashboard to manage settings, view analytics, and more.\n"
                    "**Admin View**: You're seeing all available commands."
                ),
                inline=False
            )
            embed.set_footer(text="SparkSage - Multi-AI Discord Bot | Admin View")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Load the General cog."""
    await bot.add_cog(General(bot))
