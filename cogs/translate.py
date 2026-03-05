"""
Translation Cog - Multi-Language Support

Provides `/translate` command for translating text between languages.
Uses AI provider with specialized translation system prompt.
"""

from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import config
import providers
import db as database
from utils import check_command_permission


# Common languages for autocomplete
COMMON_LANGUAGES = [
    "Spanish",
    "French",
    "German",
    "Italian",
    "Portuguese",
    "Dutch",
    "Russian",
    "Japanese",
    "Chinese",
    "Korean",
    "Arabic",
    "Hindi",
    "Thai",
    "Vietnamese",
    "Turkish",
    "Greek",
    "Polish",
    "Swedish",
    "Norwegian",
    "Danish",
    "Finnish",
    "Hebrew",
    "Swahili",
]


async def language_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Provide language suggestions for autocomplete."""
    if not current:
        return [
            app_commands.Choice(name=lang, value=lang)
            for lang in COMMON_LANGUAGES[:25]
        ]

    filtered = [
        lang for lang in COMMON_LANGUAGES
        if current.lower() in lang.lower()
    ]

    return [
        app_commands.Choice(name=lang, value=lang)
        for lang in filtered[:25]
    ]


class Translate(commands.Cog):
    """Translation commands for multilingual support."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="translate", description="Translate text to a target language")
    @app_commands.describe(
        text="The text to translate",
        language="Target language (e.g., Spanish, French, German)"
    )
    @app_commands.autocomplete(language=language_autocomplete)
    async def translate(
        self,
        interaction: discord.Interaction,
        text: str,
        language: str,
    ):
        """Translate text to a specified language."""
        if not await check_command_permission(interaction, "translate"):
            return

        await interaction.response.defer()

        try:
            translation = await self._translate_text(interaction, text, language)

            if len(translation) <= 2000:
                await interaction.followup.send(translation)
            else:
                # Split long translations
                for i in range(0, len(translation), 1900):
                    await interaction.followup.send(translation[i : i + 1900])

        except Exception as e:
            await interaction.followup.send(f"❌ Translation failed: {str(e)}")

    async def _translate_text(
        self, 
        interaction: discord.Interaction, 
        text: str, 
        target_language: str
    ) -> str:
        """Translate text using AI provider."""
        # Detect source language if not provided
        detection_prompt = f"Detect the language of this text and respond with ONLY the language name (e.g., 'English', 'Spanish'):\n\n{text}"

        try:
            source_lang_result, _ = providers.chat(
                [{"role": "user", "content": detection_prompt}],
                "You are a language detection assistant. Respond with ONLY the language name."
            )
            source_lang = source_lang_result.strip()
        except Exception:
            source_lang = "Unknown"

        # Translation prompt
        translation_prompt = f"""Translate the following text from {source_lang} to {target_language}.

Original text:
{text}

Provide ONLY the translation, no explanations or additional text."""

        system_prompt = f"You are a professional translator. Translate text accurately while preserving meaning, tone, and formatting. Always respond with ONLY the translated text."

        try:
            translation, provider_name = providers.chat(
                [{"role": "user", "content": translation_prompt}],
                system_prompt
            )

            # Format the response with language headers
            result = f"**Original** ({source_lang}):\n```\n{text}\n```\n\n"
            result += f"**Translation** ({target_language}):\n```\n{translation}\n```\n"
            result += f"-# Translated via {config.PROVIDERS.get(provider_name, {}).get('name', provider_name)}"

            # Log translation if enabled
            if config.TRANSLATION_LOGGING_ENABLED:
                await self._log_translation(
                    str(interaction.guild_id) if interaction.guild else "DM",
                    str(interaction.channel_id),
                    str(interaction.user_id),
                    source_lang,
                    target_language,
                    provider_name,
                )

            return result

        except Exception as e:
            raise RuntimeError(f"AI provider error: {e}")

    async def _log_translation(
        self,
        guild_id: str,
        channel_id: str,
        user_id: str,
        source_language: str,
        target_language: str,
        provider: str,
    ):
        """Log translation event to database."""
        try:
            await database.add_translation_log(
                guild_id,
                channel_id,
                user_id,
                source_language,
                target_language,
                provider,
            )
        except Exception as e:
            print(f"⚠️ Failed to log translation: {e}")


async def setup(bot: commands.Bot):
    """Load the Translate cog."""
    await bot.add_cog(Translate(bot))
