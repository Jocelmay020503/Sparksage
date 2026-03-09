"""Unified launcher: starts FastAPI in a background thread and the Discord bot in the main thread."""

import asyncio
import threading
import os
import time
import uvicorn


def _resolve_api_port() -> int:
    """Resolve API port for local/dev and Railway deployments."""
    return int(os.getenv("PORT") or os.getenv("DASHBOARD_PORT", "8000"))


def start_api_server():
    """Run the FastAPI server in a background thread."""
    from api.main import create_app

    app = create_app()
    port = _resolve_api_port()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


async def _init_database():
    """Initialize the database and seed config from .env."""
    import db
    await db.init_db()
    await db.sync_env_to_db()


def _is_discord_rate_limit_error(error: Exception) -> bool:
    """Detect Discord/Cloudflare login throttling errors."""
    status = getattr(error, "status", None)
    message = str(error).lower()
    return (
        status == 429
        or "too many requests" in message
        or "error 1015" in message
        or "cloudflare" in message and "rate" in message
    )


def _run_bot_with_retry(token: str):
    """Run Discord bot with retry/backoff so API stays alive during temporary login bans."""
    from bot import bot

    initial_wait = int(os.getenv("DISCORD_RETRY_INITIAL_SECONDS", "60"))
    max_wait = int(os.getenv("DISCORD_RETRY_MAX_SECONDS", "1800"))
    wait_seconds = max(5, initial_wait)

    while True:
        try:
            bot.run(token)
            # If bot.run exits without exception, stop retry loop.
            return
        except KeyboardInterrupt:
            print("\nShutting down...")
            return
        except Exception as exc:
            if _is_discord_rate_limit_error(exc):
                print(
                    "  Discord login is temporarily rate-limited (429/1015). "
                    f"Retrying in {wait_seconds} second(s)..."
                )
                time.sleep(wait_seconds)
                wait_seconds = min(wait_seconds * 2, max_wait)
                continue

            print(f"  Discord bot crashed: {exc}")
            print("  Retrying bot startup in 30 seconds...")
            time.sleep(30)


def main():
    import config
    import providers

    # Initialize database synchronously before anything else
    asyncio.run(_init_database())

    available = providers.get_available_providers()

    print("=" * 50)
    print("  SparkSage — Bot + Dashboard Launcher")
    print("=" * 50)

    # Start FastAPI in background thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    port = _resolve_api_port()
    print(f"  API server starting on http://localhost:{port}")

    # Start Discord bot in main thread
    if not config.DISCORD_TOKEN:
        print("  WARNING: DISCORD_TOKEN not set — bot will not start.")
        print("  API server is running. Use the dashboard to configure the bot.")
        # Keep main thread alive for the API server
        try:
            api_thread.join()
        except KeyboardInterrupt:
            print("\nShutting down...")
            return

    if not available:
        print("  WARNING: No AI providers configured. Add at least one API key.")
        print("  You can configure providers through the dashboard.")

    print(f"  Primary provider: {config.AI_PROVIDER}")
    print(f"  Fallback chain: {' -> '.join(available) if available else 'none'}")
    print("=" * 50)

    _run_bot_with_retry(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
