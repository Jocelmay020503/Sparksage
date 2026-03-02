"""
FAQ Cog - FAQ management and auto-response.

Commands:
- /faq add <question> <answer>
- /faq list
- /faq remove <id>
"""

from __future__ import annotations

import re
import discord
from discord import app_commands
from discord.ext import commands

import db as database


def _normalize_words(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9']+", text.lower())
    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "to",
        "for",
        "of",
        "in",
        "on",
        "and",
        "or",
        "with",
        "how",
        "what",
        "when",
        "where",
        "why",
        "can",
        "i",
        "we",
        "you",
    }
    return {t for t in tokens if len(t) > 2 and t not in stopwords}


def _build_keywords(question: str) -> str:
    words = sorted(_normalize_words(question))
    return ",".join(words[:12])


def _faq_confidence(message_content: str, faq_keywords: str) -> float:
    message_words = _normalize_words(message_content)
    keyword_words = {k.strip().lower() for k in faq_keywords.split(",") if k.strip()}
    if not message_words or not keyword_words:
        return 0.0
    overlap = message_words.intersection(keyword_words)
    return len(overlap) / max(1, len(keyword_words))


class FAQ(commands.Cog):
    """FAQ command group and automatic FAQ responses."""

    faq_group = app_commands.Group(name="faq", description="Manage server FAQs")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @faq_group.command(name="add", description="Add a new FAQ entry")
    @app_commands.describe(question="FAQ question", answer="FAQ answer")
    @app_commands.default_permissions(manage_guild=True)
    async def faq_add(self, interaction: discord.Interaction, question: str, answer: str):
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        keywords = _build_keywords(question)
        faq_id = await database.add_faq(
            guild_id=str(interaction.guild_id),
            question=question,
            answer=answer,
            match_keywords=keywords,
            created_by=str(interaction.user.id),
        )
        await interaction.response.send_message(
            f"FAQ added (ID: {faq_id}). Keywords: `{keywords or 'none'}`",
            ephemeral=True,
        )

    @faq_group.command(name="list", description="List all FAQs for this server")
    @app_commands.default_permissions(manage_guild=True)
    async def faq_list(self, interaction: discord.Interaction):
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        faqs = await database.list_faqs(guild_id=str(interaction.guild_id))
        if not faqs:
            await interaction.response.send_message("No FAQs found for this server.", ephemeral=True)
            return

        lines = ["**Server FAQs**"]
        for faq in faqs[:20]:
            lines.append(
                f"`#{faq['id']}` {faq['question']} (used: {faq['times_used']})"
            )

        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @faq_group.command(name="remove", description="Remove an FAQ by ID")
    @app_commands.describe(id="FAQ ID to remove")
    @app_commands.default_permissions(manage_guild=True)
    async def faq_remove(self, interaction: discord.Interaction, id: int):
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        deleted = await database.delete_faq(id, guild_id=str(interaction.guild_id))
        if not deleted:
            await interaction.response.send_message(
                f"FAQ #{id} not found.", ephemeral=True
            )
            return

        await interaction.response.send_message(f"Removed FAQ #{id}.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        if not message.content.strip():
            return

        faqs = await database.list_faqs(guild_id=str(message.guild.id))
        if not faqs:
            return

        best_match: dict | None = None
        best_score = 0.0
        for faq in faqs:
            score = _faq_confidence(message.content, faq["match_keywords"])
            if score > best_score:
                best_score = score
                best_match = faq

        if best_match is None:
            return

        keyword_count = len([k for k in best_match["match_keywords"].split(",") if k.strip()])
        threshold = 0.5 if keyword_count <= 3 else 0.35
        if best_score < threshold:
            return

        await database.increment_faq_usage(best_match["id"])
        await message.reply(best_match["answer"], mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(FAQ(bot))
