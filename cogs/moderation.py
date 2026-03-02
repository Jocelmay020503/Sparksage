"""
Moderation Cog - Content Moderation Pipeline

Flags potentially problematic messages for human moderator review.
Never auto-deletes; always posts to mod-log for human judgment.
"""

from __future__ import annotations

import discord
from discord.ext import commands
import json
import asyncio

import config
import providers
import db as database


class Moderation(commands.Cog):
    """Content moderation and message flagging."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen to all messages and flag suspicious ones."""
        # Check if moderation is enabled
        if not config.MODERATION_ENABLED:
            return

        # Skip bot messages, DMs, and the mod-log channel itself
        if message.author.bot:
            return

        if not message.guild:
            return

        mod_log_id = config.MOD_LOG_CHANNEL_ID
        if not mod_log_id:
            return

        try:
            mod_log_channel = self.bot.get_channel(int(mod_log_id))
            if not mod_log_channel:
                return

            # Skip messages in the mod-log channel itself
            if message.channel.id == mod_log_channel.id:
                return

            # Don't check very short messages
            if len(message.content) < 5:
                return

            # Run moderation check (non-blocking)
            await self._check_and_flag(message, mod_log_channel)

        except Exception as e:
            print(f"❌ Error in moderation check: {e}")

    async def _check_and_flag(
        self, message: discord.Message, mod_log_channel: discord.TextChannel
    ):
        """Check a message and flag if needed."""
        moderation_prompt = f"""Rate the following Discord message for potential policy violations.

USER: {message.author.display_name}
CHANNEL: #{message.channel.name}
CONTENT: "{message.content}"

Check for:
1. Toxicity, hate speech, or harassment
2. Spam or scams
3. Sexual or NSFW content
4. Violence or threats
5. Server rule violations (if known)

Respond ONLY with valid JSON (no markdown, no extra text):
{{"flagged": true/false, "reason": "brief explanation if flagged, empty if clean", "severity": "low/medium/high or none"}}

Examples:
{{"flagged": false, "reason": "", "severity": "none"}}
{{"flagged": true, "reason": "Contains hate speech targeting a protected group", "severity": "high"}}
"""

        try:
            system_prompt = "You are a content moderation assistant. Rate messages objectively and fairly. Respond ONLY with valid JSON."
            response, provider_name = providers.chat(
                [{"role": "user", "content": moderation_prompt}],
                system_prompt,
            )

            # Parse the JSON response
            try:
                # Clean up response in case AI added markdown code blocks
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                cleaned = cleaned.strip()

                moderation_data = json.loads(cleaned)
            except (json.JSONDecodeError, IndexError):
                print(f"⚠️ Failed to parse moderation response: {response}")
                return

            if not moderation_data.get("flagged", False):
                # Message is clean
                return

            # Message was flagged - post to mod-log
            reason = moderation_data.get("reason", "No reason provided")
            severity = moderation_data.get("severity", "unknown").lower()

            # Color based on severity
            colors = {
                "low": discord.Color.yellow(),
                "medium": discord.Color.orange(),
                "high": discord.Color.red(),
            }
            embed_color = colors.get(severity, discord.Color.greyple())

            # Create embed for the flagged message
            embed = discord.Embed(
                title="🚩 Content Flagged for Review",
                description=f"A message was flagged by the moderation system.",
                color=embed_color,
            )
            embed.add_field(
                name="👤 User", value=f"{message.author.mention} ({message.author.display_name})", inline=False
            )
            embed.add_field(
                name="📍 Channel", value=f"#{message.channel.name}", inline=False
            )
            embed.add_field(
                name="💬 Message", value=f"```\n{message.content}\n```", inline=False
            )
            embed.add_field(
                name="⚠️ Reason", value=reason, inline=False
            )
            embed.add_field(
                name="📊 Severity",
                value=f"`{severity.upper()}`",
                inline=True,
            )
            embed.add_field(
                name="🤖 Provider",
                value=f"`{provider_name}`",
                inline=True,
            )
            embed.add_field(
                name="🔗 Jump to Message",
                value=f"[View](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id})",
                inline=True,
            )
            embed.set_footer(text="SparkSage Moderation System")

            # Post to mod-log
            try:
                await mod_log_channel.send(embed=embed)
                print(f"🚩 Message flagged from {message.author.display_name}: {severity}")
            except discord.Forbidden:
                print(f"⚠️ No permission to post to mod-log channel {mod_log_channel.id}")

            # Track moderation event in database
            await self._log_moderation_event(
                message.guild.id,
                message.channel.id,
                message.author.id,
                message.id,
                severity,
                reason,
                provider_name,
            )

        except Exception as e:
            print(f"❌ Error during moderation check: {e}")

    async def _log_moderation_event(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        message_id: int,
        severity: str,
        reason: str,
        provider: str,
    ):
        """Log a moderation event to the database."""
        try:
            await database.add_moderation_log(
                str(guild_id),
                str(channel_id),
                str(user_id),
                str(message_id),
                severity,
                reason,
                provider,
            )
        except Exception as e:
            print(f"⚠️ Failed to log moderation event: {e}")


async def setup(bot: commands.Bot):
    """Load the Moderation cog."""
    await bot.add_cog(Moderation(bot))
