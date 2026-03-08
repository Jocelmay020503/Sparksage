import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth, config, providers, bot, conversations, wizard, faqs, permissions, channel_prompts, channel_providers, costs, analytics, rate_limits, plugins
import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    await db.sync_env_to_db()
    yield
    await db.close_db()


def _get_cors_origins() -> list[str]:
    """Build CORS allowlist from defaults plus optional env override."""
    origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    raw = os.getenv("CORS_ALLOW_ORIGINS", "")
    extra = [origin.strip() for origin in raw.split(",") if origin.strip()]
    for origin in extra:
        if origin not in origins:
            origins.append(origin)
    return origins


def create_app() -> FastAPI:
    app = FastAPI(title="SparkSage API", version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(config.router, prefix="/api/config", tags=["config"])
    app.include_router(providers.router, prefix="/api/providers", tags=["providers"])
    app.include_router(bot.router, prefix="/api/bot", tags=["bot"])
    app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
    app.include_router(faqs.router, prefix="/api/faqs", tags=["faqs"])
    app.include_router(permissions.router, prefix="/api/permissions", tags=["permissions"])
    app.include_router(channel_prompts.router, prefix="/api/channel-prompts", tags=["channel-prompts"])
    app.include_router(channel_providers.router, prefix="/api/channel-providers", tags=["channel-providers"])
    app.include_router(wizard.router, prefix="/api/wizard", tags=["wizard"])
    app.include_router(costs.router, prefix="/api/costs", tags=["costs"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(rate_limits.router, prefix="/api/rate-limits", tags=["rate-limits"])
    app.include_router(plugins.router)

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    @app.get("/")
    async def root():
        return {
            "service": "SparkSage API",
            "status": "ok",
            "health": "/api/health",
            "docs": "/docs",
        }

    @app.get("/favicon.ico")
    async def favicon():
        # Return no-content to avoid noisy 404 logs for browser favicon requests.
        return Response(status_code=204)

    return app
