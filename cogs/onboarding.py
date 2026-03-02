"""Onboarding Cog - welcome flow for new members."""

from __future__ import annotations

import discord
from discord.ext import commands

import config


def _build_rules_summary(guild: discord.Guild) -> str:
    rules_channel = next(
        (ch for ch in guild.text_channels if "rule" in ch.name.lower()),
        None,
    )
    if rules_channel:
        return f"Please review the server rules in {rules_channel.mention}."
    return "Please review the server rules and community guidelines."


def _build_key_channels(guild: discord.Guild) -> str:
    preferred = []
    for text_channel in guild.text_channels:
        name = text_channel.name.lower()
        if any(keyword in name for keyword in ["general", "help", "intro", "start"]):
            preferred.append(text_channel)

    channels = preferred[:3] if preferred else guild.text_channels[:3]
    if not channels:
        return ""

    mentions = ", ".join(ch.mention for ch in channels)
    return f"Key channels to get started: {mentions}."


class Onboarding(commands.Cog):
    """Handles new member onboarding messages."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not config.WELCOME_ENABLED:
            return

        template = config.WELCOME_MESSAGE or "Welcome {user} to **{server}**! 👋"
        try:
            welcome = template.format(user=member.mention, server=member.guild.name)
        except Exception:
            welcome = f"Welcome {member.mention} to **{member.guild.name}**! 👋"

        rules_summary = _build_rules_summary(member.guild)
        key_channels = _build_key_channels(member.guild)
        ask_line = "If you have setup questions, ask me in chat by mentioning the bot."

        sections = [welcome, rules_summary]
        if key_channels:
            sections.append(key_channels)
        sections.append(ask_line)
        message = "\n\n".join(sections)

        target_channel: discord.TextChannel | None = None
        if config.WELCOME_CHANNEL_ID:
            configured = member.guild.get_channel(int(config.WELCOME_CHANNEL_ID))
            if isinstance(configured, discord.TextChannel):
                target_channel = configured

        if target_channel is not None:
            await target_channel.send(message)
            return

        try:
            await member.send(message)
        except discord.Forbidden:
            fallback = member.guild.system_channel
            if fallback is not None:
                await fallback.send(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(Onboarding(bot))
