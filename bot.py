from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands
import config
import providers
import db as database
from utils import ask_ai, get_history

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=config.BOT_PREFIX, intents=intents)


def get_bot_status() -> dict:
    """Return bot status info for the dashboard API."""
    if bot.is_ready():
        return {
            "online": True,
            "latency": round(bot.latency * 1000, 1),
            "guilds": len(bot.guilds),
            "uptime": None,
        }
    return {"online": False, "latency": None, "guilds": 0, "uptime": None}


# --- Events ---


@bot.event
async def on_ready():
    # Initialize database when bot is ready
    await database.init_db()
    await database.sync_env_to_db()

    # Load cogs
    try:
        await bot.load_extension("cogs.general")
        await bot.load_extension("cogs.summarize")
        await bot.load_extension("cogs.code_review")
        print("Loaded cogs: general, summarize, code_review")
    except Exception as e:
        print(f"Failed to load cogs: {e}")

    available = providers.get_available_providers()
    primary = config.AI_PROVIDER
    provider_info = config.PROVIDERS.get(primary, {})

    print(f"SparkSage is online as {bot.user}")
    print(f"Primary provider: {provider_info.get('name', primary)} ({provider_info.get('model', '?')})")
    print(f"Fallback chain: {' -> '.join(available)}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    # Respond when mentioned
    if bot.user in message.mentions:
        clean_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not clean_content:
            clean_content = "Hello!"

        async with message.channel.typing():
            response, provider_name = await ask_ai(
                message.channel.id, message.author.display_name, clean_content
            )

        # Split long responses (Discord 2000 char limit)
        for i in range(0, len(response), 2000):
            await message.reply(response[i : i + 2000])

    await bot.process_commands(message)


# --- Commands are now in cogs ---


# --- Run ---


def main():
    if not config.DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not set. Copy .env.example to .env and fill in your tokens.")
        return

    available = providers.get_available_providers()
    if not available:
        print("Error: No AI providers configured. Add at least one API key to .env")
        print("Free options: GEMINI_API_KEY, GROQ_API_KEY, or OPENROUTER_API_KEY")
        return

    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
