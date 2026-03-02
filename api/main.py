from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth, config, providers, bot, conversations, wizard, faqs, permissions, channel_prompts, channel_providers, plugins, costs
import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    await db.sync_env_to_db()
    yield
    await db.close_db()


def create_app() -> FastAPI:
    app = FastAPI(title="SparkSage API", version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
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

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    return app
