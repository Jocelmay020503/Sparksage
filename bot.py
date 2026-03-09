from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands
import config
import providers
import db as database
from utils import ask_ai, get_history, check_command_permission, safe_ephemeral
from plugin_loader import plugin_loader

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True


def _resolve_interaction_command_names(interaction: discord.Interaction) -> list[str]:
    """Return qualified and root command names from an interaction payload."""
    names: list[str] = []

    def add_name(value: str | None):
        if not value:
            return
        cleaned = " ".join(value.strip().split())
        if cleaned and cleaned not in names:
            names.append(cleaned)

    command = interaction.command
    if command is not None:
        qualified = getattr(command, "qualified_name", None) or getattr(command, "name", "")
        add_name(qualified)
        add_name(qualified.split(" ", 1)[0] if qualified else None)

    # Fallback for cases where interaction.command is not populated.
    data = getattr(interaction, "data", None)
    if isinstance(data, dict):
        root = data.get("name")
        parts: list[str] = []
        if isinstance(root, str) and root.strip():
            parts.append(root.strip())

            options = data.get("options")
            while isinstance(options, list) and options:
                first = options[0]
                if not isinstance(first, dict):
                    break
                option_type = first.get("type")
                if option_type not in (1, 2):
                    break
                option_name = first.get("name")
                if not isinstance(option_name, str) or not option_name.strip():
                    break
                parts.append(option_name.strip())
                options = first.get("options")

        add_name(" ".join(parts))
        add_name(parts[0] if parts else None)

    return names


class SparkSageCommandTree(app_commands.CommandTree):
    """Application command tree with global role-based permission enforcement."""

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.type != discord.InteractionType.application_command:
            return True

        command_names = _resolve_interaction_command_names(interaction)
        if not command_names:
            return True

        try:
            for command_name in command_names:
                allowed = await check_command_permission(interaction, command_name)
                if allowed:
                    continue

                await safe_ephemeral(interaction, "❌ You don't have permission to use this command.")
                return False
        except Exception as e:
            joined_names = " | ".join(command_names)
            print(f"❌ Permission check failed for '{joined_names}': {e}")
            await safe_ephemeral(
                interaction,
                "❌ Unable to verify command permissions right now. Please try again.",
            )
            return False

        return True


bot = commands.Bot(command_prefix=config.BOT_PREFIX, intents=intents, tree_cls=SparkSageCommandTree)


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
    
    # Reload config from database (to pick up any dashboard changes)
    all_config = await database.get_all_config()
    config.reload_from_db(all_config)

    # Load built-in cogs
    try:
        await bot.load_extension("cogs.general")
        await bot.load_extension("cogs.summarize")
        await bot.load_extension("cogs.code_review")
        await bot.load_extension("cogs.faq")
        await bot.load_extension("cogs.onboarding")
        await bot.load_extension("cogs.permissions")
        await bot.load_extension("cogs.digest")
        await bot.load_extension("cogs.moderation")
        await bot.load_extension("cogs.translate")
        await bot.load_extension("cogs.channel_prompt")
        await bot.load_extension("cogs.channel_provider")
        await bot.load_extension("cogs.plugin")
        print("Loaded cogs: general, summarize, code_review, faq, onboarding, permissions, digest, moderation, translate, channel_prompt, channel_provider, plugin")
    except Exception as e:
        print(f"Failed to load cogs: {e}")

    # Load enabled plugins
    try:
        plugin_loader.bind_bot(bot)
        plugin_loader.discover_plugins()

        for manifest in plugin_loader.manifests.values():
            await database.save_plugin_manifest(
                manifest.name,
                manifest.version,
                manifest.author,
                manifest.description,
            )

        all_plugins = await database.get_all_plugins()
        for plugin in all_plugins:
            if plugin.get("enabled", False):
                success, message = await plugin_loader.load_plugin_cog(bot, plugin["name"])
                if success:
                    print(f"  ✅ {message}")
                else:
                    print(f"  ⚠️  {message}")
    except Exception as e:
        print(f"Error loading plugins: {e}")

    available = providers.get_available_providers()
    primary = config.AI_PROVIDER
    provider_info = config.PROVIDERS.get(primary, {})

    print(f"SparkSage is online as {bot.user}")
    print(f"Primary provider: {provider_info.get('name', primary)} ({provider_info.get('model', '?')})")
    print(f"Fallback chain: {' -> '.join(available)}")

    try:
        scope = (getattr(config, "COMMAND_SYNC_SCOPE", "global") or "global").lower()
        sync_guild = scope in {"guild", "both"}
        sync_global = scope in {"global", "both"}

        if sync_guild:
            if config.DISCORD_GUILD_ID:
                try:
                    guild_id = int(config.DISCORD_GUILD_ID)
                    guild_obj = discord.Object(id=guild_id)
                    bot.tree.copy_global_to(guild=guild_obj)
                    guild_synced = await bot.tree.sync(guild=guild_obj)
                    print(f"✅ Synced {len(guild_synced)} command(s) to guild {guild_id} (scope={scope})")
                except ValueError:
                    print(f"❌ Invalid DISCORD_GUILD_ID: {config.DISCORD_GUILD_ID} - must be an integer")
                except Exception as ge:
                    print(f"❌ Failed to sync to guild {config.DISCORD_GUILD_ID}: {ge}")
            else:
                print("ℹ️ COMMAND_SYNC_SCOPE includes guild, but DISCORD_GUILD_ID is not set.")

        if sync_global:
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} command(s) globally (scope={scope})")

            # Prevent duplicates when previously using guild sync by clearing guild-scoped copies.
            if scope == "global" and config.DISCORD_GUILD_ID:
                try:
                    guild_id = int(config.DISCORD_GUILD_ID)
                    guild_obj = discord.Object(id=guild_id)
                    bot.tree.clear_commands(guild=guild_obj)
                    cleared = await bot.tree.sync(guild=guild_obj)
                    print(f"🧹 Cleared guild-only command copies for guild {guild_id} (remaining guild commands: {len(cleared)})")
                except Exception as ce:
                    print(f"⚠️ Failed to clear guild command copies: {ce}")

        if not sync_guild and not sync_global:
            print(f"⚠️ COMMAND_SYNC_SCOPE='{scope}' disables both guild and global sync. No command sync performed.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")


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
                message.channel.id,
                message.author.display_name,
                clean_content,
                guild_id=str(message.guild.id) if message.guild else None,
                user_id=str(message.author.id),
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
