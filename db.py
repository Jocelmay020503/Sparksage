from __future__ import annotations

import os
import json
import aiosqlite

DATABASE_PATH = os.getenv("DATABASE_PATH", "sparksage.db")

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """Return the shared database connection, creating it if needed."""
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DATABASE_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
    return _db


async def init_db():
    """Create tables if they don't exist."""
    db = await get_db()
    await db.executescript(
        """
        CREATE TABLE IF NOT EXISTS config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT    NOT NULL,
            role       TEXT    NOT NULL,
            content    TEXT    NOT NULL,
            provider   TEXT,
            created_at TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_conv_channel ON conversations(channel_id);

        CREATE TABLE IF NOT EXISTS sessions (
            token      TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS wizard_state (
            id           INTEGER PRIMARY KEY CHECK (id = 1),
            completed    INTEGER NOT NULL DEFAULT 0,
            current_step INTEGER NOT NULL DEFAULT 0,
            data         TEXT    NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS faqs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id       TEXT    NOT NULL,
            question       TEXT    NOT NULL,
            answer         TEXT    NOT NULL,
            match_keywords TEXT    NOT NULL,
            times_used     INTEGER NOT NULL DEFAULT 0,
            created_by     TEXT,
            created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_faqs_guild ON faqs(guild_id);

        CREATE TABLE IF NOT EXISTS command_permissions (
            command_name TEXT NOT NULL,
            guild_id     TEXT NOT NULL,
            role_id      TEXT NOT NULL,
            PRIMARY KEY (command_name, guild_id, role_id)
        );
        CREATE INDEX IF NOT EXISTS idx_cmd_perms_guild ON command_permissions(guild_id);

        CREATE TABLE IF NOT EXISTS moderation_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id   TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            user_id    TEXT NOT NULL,
            message_id TEXT NOT NULL,
            severity   TEXT NOT NULL,
            reason     TEXT NOT NULL,
            provider   TEXT,
            reviewed   INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_mod_guild ON moderation_logs(guild_id);
        CREATE INDEX IF NOT EXISTS idx_mod_user ON moderation_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_mod_severity ON moderation_logs(severity);

        CREATE TABLE IF NOT EXISTS translation_logs (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id         TEXT NOT NULL,
            channel_id       TEXT NOT NULL,
            user_id          TEXT NOT NULL,
            source_language  TEXT NOT NULL,
            target_language  TEXT NOT NULL,
            provider         TEXT,
            created_at       TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_trans_guild ON translation_logs(guild_id);
        CREATE INDEX IF NOT EXISTS idx_trans_user ON translation_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_trans_languages ON translation_logs(source_language, target_language);

        CREATE TABLE IF NOT EXISTS channel_prompts (
            channel_id   TEXT PRIMARY KEY,
            guild_id     TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            created_at   TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_channel_prompts_guild ON channel_prompts(guild_id);

        CREATE TABLE IF NOT EXISTS channel_providers (
            channel_id   TEXT PRIMARY KEY,
            guild_id     TEXT NOT NULL,
            provider     TEXT NOT NULL,
            created_at   TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_channel_providers_guild ON channel_providers(guild_id);

        CREATE TABLE IF NOT EXISTS plugins (
            name         TEXT PRIMARY KEY,
            version      TEXT NOT NULL,
            author       TEXT NOT NULL,
            description  TEXT NOT NULL,
            enabled      INTEGER NOT NULL DEFAULT 0,
            installed_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        INSERT OR IGNORE INTO wizard_state (id) VALUES (1);
        """
    )
    await db.commit()


# --- Config helpers ---


async def get_config(key: str, default: str | None = None) -> str | None:
    """Get a config value from the database."""
    db = await get_db()
    cursor = await db.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = await cursor.fetchone()
    return row["value"] if row else default


async def get_all_config() -> dict[str, str]:
    """Return all config key-value pairs."""
    db = await get_db()
    cursor = await db.execute("SELECT key, value FROM config")
    rows = await cursor.fetchall()
    return {row["key"]: row["value"] for row in rows}


async def set_config(key: str, value: str):
    """Set a config value in the database."""
    db = await get_db()
    await db.execute(
        "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    await db.commit()


async def set_config_bulk(data: dict[str, str]):
    """Set multiple config values at once."""
    db = await get_db()
    await db.executemany(
        "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        list(data.items()),
    )
    await db.commit()


async def sync_env_to_db():
    """Seed the DB config table from current environment / .env values."""
    import config as cfg

    env_keys = {
        "DISCORD_TOKEN": cfg.DISCORD_TOKEN or "",
        "AI_PROVIDER": cfg.AI_PROVIDER,
        "GEMINI_API_KEY": cfg.GEMINI_API_KEY or "",
        "GEMINI_MODEL": cfg.GEMINI_MODEL,
        "GROQ_API_KEY": cfg.GROQ_API_KEY or "",
        "GROQ_MODEL": cfg.GROQ_MODEL,
        "OPENROUTER_API_KEY": cfg.OPENROUTER_API_KEY or "",
        "OPENROUTER_MODEL": cfg.OPENROUTER_MODEL,
        "ANTHROPIC_API_KEY": cfg.ANTHROPIC_API_KEY or "",
        "ANTHROPIC_MODEL": cfg.ANTHROPIC_MODEL,
        "OPENAI_API_KEY": cfg.OPENAI_API_KEY or "",
        "OPENAI_MODEL": cfg.OPENAI_MODEL,
        "BOT_PREFIX": cfg.BOT_PREFIX,
        "MAX_TOKENS": str(cfg.MAX_TOKENS),
        "SYSTEM_PROMPT": cfg.SYSTEM_PROMPT,
        "WELCOME_CHANNEL_ID": cfg.WELCOME_CHANNEL_ID,
        "WELCOME_MESSAGE": cfg.WELCOME_MESSAGE,
        "WELCOME_ENABLED": "true" if cfg.WELCOME_ENABLED else "false",
        "DIGEST_CHANNEL_ID": cfg.DIGEST_CHANNEL_ID,
        "DIGEST_TIME": cfg.DIGEST_TIME,
        "DIGEST_ENABLED": "true" if cfg.DIGEST_ENABLED else "false",
        "MODERATION_ENABLED": "true" if cfg.MODERATION_ENABLED else "false",
        "MODERATION_SENSITIVITY": cfg.MODERATION_SENSITIVITY,
        "MOD_LOG_CHANNEL_ID": cfg.MOD_LOG_CHANNEL_ID,
        "TRANSLATION_LOGGING_ENABLED": "true" if cfg.TRANSLATION_LOGGING_ENABLED else "false",
    }
    # Only insert keys that don't already exist in DB (don't overwrite user edits)
    db = await get_db()
    for key, value in env_keys.items():
        await db.execute(
            "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )
    await db.commit()


async def sync_db_to_env():
    """Write DB config back to the .env file."""
    from dotenv import dotenv_values, set_key

    env_path = os.path.join(os.path.dirname(__file__), ".env")
    all_config = await get_all_config()

    for key, value in all_config.items():
        set_key(env_path, key, value)


# --- Conversation helpers ---


async def add_message(channel_id: str, role: str, content: str, provider: str | None = None):
    """Add a message to conversation history."""
    db = await get_db()
    await db.execute(
        "INSERT INTO conversations (channel_id, role, content, provider) VALUES (?, ?, ?, ?)",
        (channel_id, role, content, provider),
    )
    await db.commit()


async def get_messages(channel_id: str, limit: int = 20) -> list[dict]:
    """Get recent messages for a channel."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT role, content, provider, created_at FROM conversations WHERE channel_id = ? ORDER BY id DESC LIMIT ?",
        (channel_id, limit),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in reversed(rows)]


async def clear_messages(channel_id: str):
    """Delete all messages for a channel."""
    db = await get_db()
    await db.execute("DELETE FROM conversations WHERE channel_id = ?", (channel_id,))
    await db.commit()


async def list_channels() -> list[dict]:
    """List all channels with message counts."""
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT channel_id, COUNT(*) as message_count, MAX(created_at) as last_active
        FROM conversations
        GROUP BY channel_id
        ORDER BY last_active DESC
        """
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# --- FAQ helpers ---


async def add_faq(
    guild_id: str,
    question: str,
    answer: str,
    match_keywords: str,
    created_by: str | None = None,
) -> int:
    """Create an FAQ entry and return its ID."""
    db = await get_db()
    cursor = await db.execute(
        """
        INSERT INTO faqs (guild_id, question, answer, match_keywords, created_by)
        VALUES (?, ?, ?, ?, ?)
        """,
        (guild_id, question, answer, match_keywords, created_by),
    )
    await db.commit()
    return int(cursor.lastrowid)


async def list_faqs(guild_id: str | None = None) -> list[dict]:
    """List FAQ entries, optionally filtered by guild."""
    db = await get_db()
    if guild_id:
        cursor = await db.execute(
            """
            SELECT id, guild_id, question, answer, match_keywords, times_used, created_by, created_at
            FROM faqs
            WHERE guild_id = ?
            ORDER BY id DESC
            """,
            (guild_id,),
        )
    else:
        cursor = await db.execute(
            """
            SELECT id, guild_id, question, answer, match_keywords, times_used, created_by, created_at
            FROM faqs
            ORDER BY id DESC
            """
        )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def delete_faq(faq_id: int, guild_id: str | None = None) -> bool:
    """Delete an FAQ by ID, optionally scoped to a guild."""
    db = await get_db()
    if guild_id:
        cursor = await db.execute(
            "DELETE FROM faqs WHERE id = ? AND guild_id = ?",
            (faq_id, guild_id),
        )
    else:
        cursor = await db.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
    await db.commit()
    return cursor.rowcount > 0


async def increment_faq_usage(faq_id: int):
    """Increment times_used for an FAQ."""
    db = await get_db()
    await db.execute(
        "UPDATE faqs SET times_used = times_used + 1 WHERE id = ?",
        (faq_id,),
    )
    await db.commit()


# --- Permission helpers ---


async def add_permission(command_name: str, guild_id: str, role_id: str):
    """Add a role permission for a command."""
    db = await get_db()
    await db.execute(
        "INSERT OR IGNORE INTO command_permissions (command_name, guild_id, role_id) VALUES (?, ?, ?)",
        (command_name, guild_id, role_id),
    )
    await db.commit()


async def delete_permission(command_name: str, guild_id: str, role_id: str) -> bool:
    """Delete a role permission for a command."""
    db = await get_db()
    cursor = await db.execute(
        "DELETE FROM command_permissions WHERE command_name = ? AND guild_id = ? AND role_id = ?",
        (command_name, guild_id, role_id),
    )
    await db.commit()
    return cursor.rowcount > 0


async def list_permissions(guild_id: str | None = None, command_name: str | None = None) -> list[dict]:
    """List command permissions, optionally filtered by guild or command."""
    db = await get_db()
    query = "SELECT command_name, guild_id, role_id FROM command_permissions WHERE 1=1"
    params = []
    
    if guild_id:
        query += " AND guild_id = ?"
        params.append(guild_id)
    if command_name:
        query += " AND command_name = ?"
        params.append(command_name)
    
    query += " ORDER BY command_name, role_id"
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def check_permission(command_name: str, guild_id: str, user_role_ids: list[str]) -> bool:
    """Check if a user has permission to use a command. Returns True if no restrictions exist or user has required role."""
    db = await get_db()
    # First check if any permissions exist for this command in this guild
    cursor = await db.execute(
        "SELECT COUNT(*) as count FROM command_permissions WHERE command_name = ? AND guild_id = ?",
        (command_name, guild_id),
    )
    row = await cursor.fetchone()
    
    # If no permissions are set, command is unrestricted
    if row["count"] == 0:
        return True
    
    # Check if user has any of the required roles
    placeholders = ",".join("?" * len(user_role_ids))
    cursor = await db.execute(
        f"SELECT COUNT(*) as count FROM command_permissions WHERE command_name = ? AND guild_id = ? AND role_id IN ({placeholders})",
        [command_name, guild_id] + user_role_ids,
    )
    row = await cursor.fetchone()
    return row["count"] > 0


# --- Wizard helpers ---


async def get_wizard_state() -> dict:
    """Get the wizard state."""
    db = await get_db()
    cursor = await db.execute("SELECT completed, current_step, data FROM wizard_state WHERE id = 1")
    row = await cursor.fetchone()
    return {
        "completed": bool(row["completed"]),
        "current_step": row["current_step"],
        "data": json.loads(row["data"]),
    }


async def set_wizard_state(completed: bool | None = None, current_step: int | None = None, data: dict | None = None):
    """Update wizard state fields."""
    db = await get_db()
    updates = []
    params = []
    if completed is not None:
        updates.append("completed = ?")
        params.append(int(completed))
    if current_step is not None:
        updates.append("current_step = ?")
        params.append(current_step)
    if data is not None:
        updates.append("data = ?")
        params.append(json.dumps(data))
    if updates:
        await db.execute(f"UPDATE wizard_state SET {', '.join(updates)} WHERE id = 1", params)
        await db.commit()


# --- Session helpers ---


async def create_session(token: str, user_id: str, expires_at: str):
    """Store a session token."""
    db = await get_db()
    await db.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at),
    )
    await db.commit()


async def validate_session(token: str) -> dict | None:
    """Validate a session token, return session data or None."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT user_id, expires_at FROM sessions WHERE token = ? AND expires_at > datetime('now')",
        (token,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def delete_session(token: str):
    """Delete a session."""
    db = await get_db()
    await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    await db.commit()


# --- Moderation helpers ---


async def add_moderation_log(
    guild_id: str,
    channel_id: str,
    user_id: str,
    message_id: str,
    severity: str,
    reason: str,
    provider: str | None = None,
):
    """Log a moderation event."""
    db = await get_db()
    await db.execute(
        "INSERT INTO moderation_logs (guild_id, channel_id, user_id, message_id, severity, reason, provider) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (guild_id, channel_id, user_id, message_id, severity, reason, provider),
    )
    await db.commit()


async def get_moderation_logs(
    guild_id: str | None = None,
    user_id: str | None = None,
    severity: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Get moderation logs with optional filters."""
    db = await get_db()
    query = "SELECT * FROM moderation_logs WHERE 1=1"
    params = []

    if guild_id:
        query += " AND guild_id = ?"
        params.append(guild_id)

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    if severity:
        query += " AND severity = ?"
        params.append(severity)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def mark_moderation_reviewed(log_id: int):
    """Mark a moderation log as reviewed."""
    db = await get_db()
    await db.execute(
        "UPDATE moderation_logs SET reviewed = 1 WHERE id = ?",
        (log_id,),
    )
    await db.commit()


# --- Translation helpers ---


async def add_translation_log(
    guild_id: str,
    channel_id: str,
    user_id: str,
    source_language: str,
    target_language: str,
    provider: str | None = None,
):
    """Log a translation event."""
    db = await get_db()
    await db.execute(
        "INSERT INTO translation_logs (guild_id, channel_id, user_id, source_language, target_language, provider) VALUES (?, ?, ?, ?, ?, ?)",
        (guild_id, channel_id, user_id, source_language, target_language, provider),
    )
    await db.commit()


async def get_translation_logs(
    guild_id: str | None = None,
    user_id: str | None = None,
    source_language: str | None = None,
    target_language: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Get translation logs with optional filters."""
    db = await get_db()
    query = "SELECT * FROM translation_logs WHERE 1=1"
    params = []

    if guild_id:
        query += " AND guild_id = ?"
        params.append(guild_id)

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    if source_language:
        query += " AND source_language = ?"
        params.append(source_language)

    if target_language:
        query += " AND target_language = ?"
        params.append(target_language)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# --- Channel Prompt helpers ---


async def get_channel_prompt(channel_id: str) -> str | None:
    """Get custom system prompt for a specific channel."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT system_prompt FROM channel_prompts WHERE channel_id = ?",
        (channel_id,),
    )
    row = await cursor.fetchone()
    return row["system_prompt"] if row else None


async def set_channel_prompt(channel_id: str, guild_id: str, system_prompt: str):
    """Set or update custom system prompt for a channel."""
    db = await get_db()
    await db.execute(
        """INSERT INTO channel_prompts (channel_id, guild_id, system_prompt, updated_at)
           VALUES (?, ?, ?, datetime('now'))
           ON CONFLICT(channel_id) DO UPDATE SET
               system_prompt = excluded.system_prompt,
               updated_at = datetime('now')""",
        (channel_id, guild_id, system_prompt),
    )
    await db.commit()


async def remove_channel_prompt(channel_id: str):
    """Remove custom system prompt for a channel."""
    db = await get_db()
    await db.execute(
        "DELETE FROM channel_prompts WHERE channel_id = ?",
        (channel_id,),
    )
    await db.commit()


async def get_all_channel_prompts(guild_id: str | None = None) -> list[dict]:
    """Get all channel prompts, optionally filtered by guild."""
    db = await get_db()
    if guild_id:
        cursor = await db.execute(
            "SELECT * FROM channel_prompts WHERE guild_id = ? ORDER BY created_at DESC",
            (guild_id,),
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM channel_prompts ORDER BY created_at DESC"
        )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# --- Channel Provider helpers ---


async def get_channel_provider(channel_id: str) -> str | None:
    """Get provider override for a specific channel."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT provider FROM channel_providers WHERE channel_id = ?",
        (channel_id,),
    )
    row = await cursor.fetchone()
    return row["provider"] if row else None


async def set_channel_provider(channel_id: str, guild_id: str, provider: str):
    """Set or update provider override for a channel."""
    db = await get_db()
    await db.execute(
        """INSERT INTO channel_providers (channel_id, guild_id, provider, updated_at)
           VALUES (?, ?, ?, datetime('now'))
           ON CONFLICT(channel_id) DO UPDATE SET
               provider = excluded.provider,
               updated_at = datetime('now')""",
        (channel_id, guild_id, provider),
    )
    await db.commit()


async def remove_channel_provider(channel_id: str):
    """Remove provider override for a channel."""
    db = await get_db()
    await db.execute(
        "DELETE FROM channel_providers WHERE channel_id = ?",
        (channel_id,),
    )
    await db.commit()


async def get_all_channel_providers(guild_id: str | None = None) -> list[dict]:
    """Get all channel provider overrides, optionally filtered by guild."""
    db = await get_db()
    if guild_id:
        cursor = await db.execute(
            "SELECT * FROM channel_providers WHERE guild_id = ? ORDER BY created_at DESC",
            (guild_id,),
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM channel_providers ORDER BY created_at DESC"
        )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# --- Plugin helpers ---


async def upsert_plugin(name: str, version: str, author: str, description: str, enabled: bool = False):
    """Insert or update plugin metadata."""
    db = await get_db()
    await db.execute(
        """INSERT INTO plugins (name, version, author, description, enabled, updated_at)
           VALUES (?, ?, ?, ?, ?, datetime('now'))
           ON CONFLICT(name) DO UPDATE SET
               version = excluded.version,
               author = excluded.author,
               description = excluded.description,
               enabled = excluded.enabled,
               updated_at = datetime('now')""",
        (name, version, author, description, int(enabled)),
    )
    await db.commit()


async def set_plugin_enabled(name: str, enabled: bool) -> bool:
    """Enable or disable a plugin. Returns True if plugin exists."""
    db = await get_db()
    cursor = await db.execute(
        """UPDATE plugins
           SET enabled = ?, updated_at = datetime('now')
           WHERE name = ?""",
        (int(enabled), name),
    )
    await db.commit()
    return cursor.rowcount > 0


async def delete_plugin(name: str) -> bool:
    """Delete installed plugin record."""
    db = await get_db()
    cursor = await db.execute(
        "DELETE FROM plugins WHERE name = ?",
        (name,),
    )
    await db.commit()
    return cursor.rowcount > 0


async def get_plugin(name: str) -> dict | None:
    """Get installed plugin by name."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM plugins WHERE name = ?",
        (name,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def list_plugins() -> list[dict]:
    """List all installed plugins."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM plugins ORDER BY name ASC"
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def list_enabled_plugins() -> list[dict]:
    """List enabled plugins."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM plugins WHERE enabled = 1 ORDER BY name ASC"
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def close_db():
    """Close the database connection."""
    global _db
    if _db:
        await _db.close()
        _db = None
