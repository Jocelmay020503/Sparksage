# Changelog

## [0.6.3] - 2026-03-04

### Added - Phase 5.5: Dashboard Polish (Dark Mode & Responsive Design)

- **Dark Mode Support**:
  - `ThemeProvider` component wrapping app with `next-themes` integration
  - `ThemeToggle` button component in sidebar footer with sun/moon icons
  - System-aware theme detection with automatic light/dark mode switching
  - Root layout enhanced with `suppressHydrationWarning` for theme handling
  - Proper dark mode color variables in globals.css (already existed)

- **Responsive Design Improvements**:
  - All dashboard pages updated with Tailwind responsive breakpoints (sm:, md:, lg:, xl:)
  - Cost dashboard: flexible header with wrapped time range selector buttons
  - Cost summary cards: `sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5` for optimal scaling
  - Cost charts section: `sm:grid-cols-1 lg:grid-cols-2` responsive grid
  - Provider cost table: horizontal scroll on mobile with `overflow-x-auto`, hidden token columns on small screens
  - Top users/guilds: `sm:grid-cols-2` responsive grid layout
  - Overview page: `sm:grid-cols-2 lg:grid-cols-4` summary cards
  - Providers page: `sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3` provider grid
  - Prompts & Channel Providers: `sm:grid-cols-1 md:grid-cols-2` form layouts

- **Mobile Optimization**:
  - Dashboard main layout: `w-full overflow-x-hidden` to prevent horizontal scroll
  - Sticky header with `sticky top-0 bg-background z-10` for persistent navigation
  - Responsive padding: `p-4 sm:p-6` for better mobile spacing
  - Text truncation on dashboard header title for narrow screens
  - Button layouts with proper sizing (`text-xs sm:text-sm`) for mobile
  - Table responsiveness with minimum widths and selective column hiding

- **New Components**:
  - `dashboard/src/components/theme-provider.tsx` — Next.js theme provider wrapper
  - `dashboard/src/components/theme-toggle.tsx` — Dark/light mode toggle button

- **Enhanced Files**:
  - `dashboard/src/app/layout.tsx` — ThemeProvider integration
  - `dashboard/src/app/dashboard/layout.tsx` — Responsive main layout with sticky header
  - `dashboard/src/app/dashboard/page.tsx` — Responsive grid breakpoints
  - `dashboard/src/app/dashboard/costs/page.tsx` — Full mobile responsiveness
  - `dashboard/src/app/dashboard/providers/page.tsx` — Responsive provider grid
  - `dashboard/src/app/dashboard/prompts/page.tsx` — Responsive form layout
  - `dashboard/src/app/dashboard/channel-providers/page.tsx` — Responsive form grid
  - `dashboard/src/components/sidebar/app-sidebar.tsx` — Theme toggle in footer

### Fixed
- TypeScript type errors in cost dashboard PieChart label renderer (Phase 5.4 hotfix)

## [0.6.2] - 2026-03-04

### Added - Phase 5.4: Cost Tracking and Expense Monitoring

- **Cost Calculator Utility** (`utils/cost_calculator.py`):
  - `ProviderPricing` dataclass with input/output token rates per 1M tokens
  - Pricing data for Gemini, Groq, OpenRouter, Anthropic, OpenAI
  - `calculate_cost()` function returning USD cost from token counts
  - `format_cost()` for multiple display scales (USD, millidollars, microdollars)
  - `get_all_provider_costs()` and `get_provider_pricing()` helpers

- **Database Cost Tracking** (`db.py`):
  - `cost_usage` table tracking API calls with provider, tokens, cost, guild/user IDs
  - Indexed queries on provider, guild_id, user_id, created_at
  - `log_cost_usage()` — record API cost event
  - `get_cost_summary()` — aggregate total/token/query metrics with provider breakdown
  - `get_cost_by_provider()` — cost metrics per provider
  - `get_top_expensive_users()` and `get_top_expensive_guilds()` — cost rankings
  - `get_cost_history()` — daily aggregated cost trends

- **REST API Endpoints** (`api/routes/costs.py`):
  - `GET /api/costs/summary?days=30` — overall cost metrics with provider breakdown
  - `GET /api/costs/by-provider?days=30` — cost breakdown by provider
  - `GET /api/costs/top-users?days=30&limit=10` — top spending users
  - `GET /api/costs/top-guilds?days=30&limit=10` — top spending guilds
  - `GET /api/costs/history?days=30` — daily cost history for trending

- **Cost Tracking Dashboard** (`dashboard/src/app/dashboard/costs/page.tsx`):
  - Summary cards: Total Cost, Input Tokens, Output Tokens, Queries, Avg Cost/Query
  - Daily cost line chart with time range selector (7/14/30/60/90 days)
  - Provider cost pie chart showing distribution
  - Provider breakdown table with cost, queries, input/output tokens
  - Top expensive users and guilds rankings with token usage
  - Information card explaining cost system
  - Custom cost formatting for USD display

- **API Integration** (`dashboard/src/lib/api.ts`):
  - TypeScript types: `CostSummary`, `CostByProvider`, `CostHistoryItem`, `TopExpensiveItem`
  - API methods: `getCostSummary()`, `getCostByProvider()`, `getCostHistory()`
  - `getTopExpensiveUsers()` and `getTopExpensiveGuilds()` methods

- **Sidebar Navigation**:
  - Added `Costs` menu item with DollarSign icon

## [0.5.4] - 2026-03-03

### Added - Phase 4.5: Per-Channel Provider Override

- **Channel Provider Database Table** (`channel_providers`) in `db.py`:
  - Stores per-channel provider overrides with guild mapping
  - Includes created/updated timestamps and guild index
- **Channel Provider DB Helpers** in `db.py`:
  - `get_channel_provider()` — get provider override for a channel
  - `set_channel_provider()` — create/update channel provider override
  - `remove_channel_provider()` — remove override and use global provider
  - `get_all_channel_providers()` — list channel-provider mappings
- **Provider Override Runtime Support**:
  - `providers.chat()` now accepts optional `preferred_provider`
  - `utils.ask_ai()` checks channel provider override before global provider fallback chain
- **Discord Channel Provider Command** (`cogs/channel_provider.py`):
  - Added `/channel-provider` command with actions: `set`, `reset`, `show`
  - Supports provider choices: Gemini, Groq, OpenRouter, Anthropic, OpenAI
  - Uses `Manage Channels` default permission
- **API Endpoints** (`api/routes/channel_providers.py`):
  - `GET /api/channel-providers` and `GET /api/channel-providers/{channel_id}`
  - `POST /api/channel-providers`, `DELETE /api/channel-providers/{channel_id}`
  - Router registered in `api/main.py`
- **Dashboard Channel Provider Management**:
  - New page: `/dashboard/channel-providers`
  - Create/remove channel provider overrides from UI
  - Added API client methods/types in `dashboard/src/lib/api.ts`
  - Added `Channel Providers` item in sidebar navigation

## [0.5.3] - 2026-03-03

### Added - Phase 4.4: Custom System Prompts Per Channel

- **Channel Prompt Database Table** (`channel_prompts`) in `db.py`:
  - Stores per-channel system prompts with guild mapping
  - Includes created/updated timestamps and guild index
- **Channel Prompt DB Helpers** in `db.py`:
  - `get_channel_prompt()` — get prompt for a channel
  - `set_channel_prompt()` — create/update channel prompt
  - `remove_channel_prompt()` — reset channel to global prompt
  - `get_all_channel_prompts()` — list channel prompt mappings
- **Per-Channel Prompt Runtime Support** in `utils/__init__.py`:
  - `ask_ai()` now checks channel-specific prompt first
  - Falls back to global `SYSTEM_PROMPT` when no channel prompt exists
- **Discord Prompt Management Command** (`cogs/channel_prompt.py`):
  - Added `/prompt` command with actions: `set`, `reset`, `show`
  - Uses `Manage Channels` permission check for channel prompt changes
- **API Endpoints** (`api/routes/channel_prompts.py`):
  - `GET /api/channel-prompts` and `GET /api/channel-prompts/{channel_id}`
  - `POST /api/channel-prompts`, `PUT /api/channel-prompts/{channel_id}`, `DELETE /api/channel-prompts/{channel_id}`
  - Router registered in `api/main.py`
- **Dashboard Prompt Management**:
  - New page: `/dashboard/prompts`
  - Create/remove channel prompts from dashboard UI
  - Added API client methods in `dashboard/src/lib/api.ts`
  - Added `Prompts` navigation item in sidebar

## [0.5.2] - 2026-03-03

### Added - Phase 4.3: Multi-Language Translation

- **Translation Cog** (`cogs/translate.py`) with AI-powered language translation
- **Translate Slash Command** (`/translate`):
  - Translates text to target language using AI provider
  - Auto-detects source language using language detection model
  - Supports 25 common languages (Spanish, French, German, Chinese, Japanese, Arabic, etc.)
  - Language autocomplete in Discord UI
  - Returns bilingual formatted output with source and target language labels
  - Displays AI provider attribution
- **Translation Logging**:
  - Optional translation event tracking to database
  - `TRANSLATION_LOGGING_ENABLED` config flag (default: false)
- **Translation Database Table** (`translation_logs`):
  - Records translation requests: guild, channel, user, source/target languages, provider, timestamp
  - Indexes on guild_id, user_id, and language pair combinations for efficient queries
- **Translation Helper Functions** in `db.py`:
  - `add_translation_log()` — record a translation event
  - `get_translation_logs()` — query translation history with optional filters (guild, user, source language, target language)
- **Translation Configuration** in `config.py`:
  - `TRANSLATION_LOGGING_ENABLED` — enable/disable translation logging (default: false)
- **Dashboard Controls**:
  - Translation section in settings page
  - Toggle for translation logging enable/disable
  - Part of unified settings management alongside other Phase 4 features

## [0.5.1] - 2026-03-02

### Added - Phase 4.2: Content Moderation Pipeline

- **Moderation Cog** (`cogs/moderation.py`) with AI-powered content checking
- **Real-Time Message Flagging** via `on_message` listener:
  - Checks messages for toxicity, hate speech, spam, and rule violations
  - Uses AI to rate messages and provide structured JSON response
  - Never auto-deletes; always flags for human review
  - Skips bot messages and DM channels
  - Configurable skip list (can exclude certain channels)
- **Moderation Log Channel** posts flagged messages with:
  - Rich embedded message with user, channel, content, reason
  - Severity badge (Low/Medium/High) with color coding
  - AI provider attribution
  - Direct link to original message
  - Action buttons for moderator response (future expansion)
- **Moderation Database Table** (`moderation_logs`):
  - Tracks all flagged messages with guild, channel, user, severity, reason
  - `reviewed` flag for tracking moderation actions
  - Indexes on guild_id, user_id, and severity for fast queries
- **Moderation Helper Functions** in `db.py`:
  - `add_moderation_log()` — record flagged message
  - `get_moderation_logs()` — query with optional filters (guild, user, severity)
  - `mark_moderation_reviewed()` — mark log as reviewed
- **Moderation Configuration** in `config.py`:
  - `MODERATION_ENABLED` — enable/disable moderation (default: false)
  - `MOD_LOG_CHANNEL_ID` — channel for posting flagged messages
  - `MODERATION_SENSITIVITY` — low/medium/high (influences AI prompt, default: medium)
- **Dashboard Moderation Controls** in `/dashboard/settings`:
  - Enable/disable toggle for moderation
  - Mod-log channel ID input field
  - Sensitivity selector (Low/Medium/High) to adjust detection strictness
  - Descriptive help text explaining each setting

### Changed - Phase 4.2

- **`bot.py`** — loads `cogs.moderation` during startup
- **`config.py`** — adds `MODERATION_ENABLED`, `MODERATION_SENSITIVITY`, `MOD_LOG_CHANNEL_ID` with reload support
- **`db.py`** — includes moderation_logs table creation and sync functions
- **`dashboard/src/app/dashboard/settings/page.tsx`** — adds Content Moderation section with controls

### Acceptance Criteria ✓ (Phase 4.2)

- ✓ Messages checked against moderation prompt in real-time
- ✓ AI returns structured JSON with flagged/reason/severity
- ✓ Flagged messages posted to mod-log channel as rich embeds
- ✓ Never auto-deletes; always flags for human review
- ✓ Moderation events tracked in database
- ✓ Dashboard controls for all moderation settings
- ✓ Configurability: enable/disable, channel, sensitivity level

---

## [0.5.0] - 2026-03-02

### Added - Phase 4.1: Daily Digest Scheduler

- **Digest Cog** (`cogs/digest.py`) with automated daily activity summarization
- **Daily Digest Scheduler** using `discord.ext.tasks.loop`:
  - Configurable schedule via `DIGEST_TIME` (default: 09:00 UTC)
  - Collects messages from past 24 hours across all accessible channels
  - AI-powered summarization covering most active discussions, highlights, and sentiment
  - Fallback to basic statistics if AI summarization fails
  - Skips the digest channel itself to avoid recursion
- **Manual Digest Command** (`!digest`) for administrators to trigger on-demand
- **Digest Configuration** in `config.py`:
  - `DIGEST_ENABLED` — enable/disable digest (default: false)
  - `DIGEST_CHANNEL_ID` — target channel for posting digests
  - `DIGEST_TIME` — scheduled time in HH:MM UTC format (default: "09:00")
- **Database Integration** in `db.py`:
  - Digest settings synced to/from database via `sync_env_to_db()`
  - Config reload support for digest settings
- **Dashboard Digest Controls** in `/dashboard/settings`:
  - Enable/disable toggle with radio buttons
  - Channel ID input field with helper text
  - Time picker (HTML5 time input) for scheduling
  - Description explaining digest functionality
- **Rich Embed Formatting** for digest posts with timestamp and SparkSage branding

### Changed - Phase 4.1

- **`bot.py`** — loads `cogs.digest` during startup
- **`config.py`** — adds `DIGEST_CHANNEL_ID`, `DIGEST_TIME`, `DIGEST_ENABLED` config keys with reload support
- **`db.py`** — includes digest settings in `sync_env_to_db()` function
- **`dashboard/src/app/dashboard/settings/page.tsx`** — adds Daily Digest section with controls for all digest settings

### Acceptance Criteria ✓ (Phase 4.1)

- ✓ Digest runs automatically at configured time (24-hour loop with precise scheduling)
- ✓ Collects messages from past 24h across all channels
- ✓ Summarizes activity using AI with fallback chain support
- ✓ Posts to designated channel as rich embed
- ✓ Dashboard controls for all digest settings
- ✓ Manual trigger available via `!digest` command (admin-only)

---

## [0.4.4] - 2026-03-02

### Added - Phase 3.5: Role-Based Access Control for Commands

- **Permissions Database Schema** (`command_permissions` table) with composite primary key on `(command_name, guild_id, role_id)` and guild-level indexing
- **Permission Helper Functions** in `db.py`:
  - `add_permission()` — add role requirement for a command
  - `delete_permission()` — remove role restriction
  - `list_permissions()` — list permissions with optional guild/command filtering
  - `check_permission()` — validate user permission based on roles
- **Permissions Cog** (`cogs/permissions.py`) with slash commands:
  - `/permissions-set <command> <role>` — restrict command to role
  - `/permissions-remove <command> <role>` — lift restriction
  - `/permissions-list` — show all restrictions for the server
- **Permission Enforcement** in command cogs:
  - `check_command_permission()` helper function in `utils/__init__.py`
  - Permission checks added to `/ask`, `/clear`, `/summarize`, `/review` commands
  - Administrators always bypass restrictions
- **Permissions API Endpoints**:
  - `GET /api/permissions` — list permissions with optional filters
  - `POST /api/permissions` — create permission rule
  - `DELETE /api/permissions` — remove permission rule
- **Dashboard Permissions Page** at `/dashboard/permissions` for managing command access control with grouped display by command

### Changed - Phase 3.5

- **`bot.py`** — loads `cogs.permissions` during startup
- **`cogs/general.py`, `cogs/summarize.py`, `cogs/code_review.py`** — add permission checks to commands
- **`api/main.py`** — registers `permissions` router under `/api/permissions`
- **`dashboard/src/lib/api.ts`** — adds `PermissionItem` interface and CRUD methods
- **`dashboard/src/components/sidebar/app-sidebar.tsx`** — adds Permissions navigation item with Shield icon

### Acceptance Criteria ✓ (Phase 3.5)

- ✓ Server admins can restrict any command to specific roles via Discord and dashboard
- ✓ Unrestricted commands remain available to everyone
- ✓ Permission changes take effect immediately without restart
- ✓ Administrators bypass all restrictions

---

## [0.4.3] - 2026-03-02

### Added - Phase 3.4: New Member Onboarding Flow

- **Onboarding Cog** (`cogs/onboarding.py`) with `on_member_join` listener
- **Welcome delivery flow**:
  - posts in configured `WELCOME_CHANNEL_ID` when set
  - otherwise sends a DM to the new member
  - falls back to server system channel if DMs are blocked
- **Structured welcome content** includes:
  - customizable welcome template (`WELCOME_MESSAGE` with `{user}` and `{server}` placeholders)
  - server rules summary
  - key channel links
  - prompt to ask SparkSage setup questions
- **Onboarding configuration keys**:
  - `WELCOME_ENABLED`
  - `WELCOME_CHANNEL_ID`
  - `WELCOME_MESSAGE`

### Changed - Phase 3.4

- **`bot.py`** — loads `cogs.onboarding` and enables `members` intent
- **`config.py`** — adds onboarding config vars and DB reload mapping
- **`db.py`** — syncs onboarding keys into persistent config table
- **Dashboard Settings page** — adds onboarding controls (enabled toggle, channel ID, template)
- **`.env.example`** — documents onboarding environment keys

### Acceptance Criteria ✓ (Phase 3.4)

- ✓ New members receive a welcome message automatically
- ✓ Message template customizable from dashboard (`WELCOME_MESSAGE`)
- ✓ Onboarding can be enabled/disabled without restart (`WELCOME_ENABLED`)

---

## [0.4.2] - 2026-03-02

### Added - Phase 3.3: FAQ Auto-Detection and Response

- **FAQ database schema** (`faqs` table) with `times_used` tracking and guild-level indexing
- **FAQ Cog** (`cogs/faq.py`) with `/faq add`, `/faq list`, `/faq remove`
- **Auto FAQ detection** in message listener using keyword overlap confidence and automatic reply on high-confidence matches
- **FAQ usage analytics** via `times_used` increment on every auto-response
- **FAQ API endpoints**:
  - `GET /api/faqs`
  - `POST /api/faqs`
  - `DELETE /api/faqs/{id}`
- **Dashboard FAQ page** at `/dashboard/faqs` for creating, viewing, and deleting FAQ entries

### Changed - Phase 3.3

- **`bot.py`** — loads `cogs.faq` during startup
- **`api/main.py`** — registers `faqs` router under `/api/faqs`
- **`dashboard/src/lib/api.ts`** — adds FAQ client types and CRUD methods
- **`dashboard/src/components/sidebar/app-sidebar.tsx`** — adds FAQ navigation item

### Acceptance Criteria ✓ (Phase 3.3)

- ✓ Admins can CRUD FAQ entries via Discord commands and dashboard
- ✓ Bot auto-responds to messages matching FAQ keywords
- ✓ FAQ usage is tracked (`times_used` counter)

---

## [0.4.1] - 2026-03-02

### Added - Phase 3.2: Code Review with Syntax Highlighting

- **Code Review Cog** (`cogs/code_review.py`) — `/review` slash command for analyzing code
  - `code` parameter (required) — the code snippet to review
  - `language` parameter (optional) — programming language hint; auto-detects if omitted
- **Language Auto-Detection** — Heuristic-based detection for Python, JavaScript, Java, Rust, Swift, C, etc.
- **Specialized Review Prompt** — Senior code reviewer persona that analyzes:
  - Bugs and potential errors (logical flaws, null pointer risks, etc.)
  - Style and best practices (naming, organization, language standards)
  - Performance improvements (algorithmic efficiency, optimization opportunities)
  - Security concerns (input validation, injection risks, hardcoded secrets)
- **Syntax Highlighting** — Responses formatted with markdown code blocks and language markers (```python, ```javascript, etc.)
- **Discord Integration** — Full integration with existing ask_ai() and provider system; response footer shows which AI provider performed the review

### Changed - Phase 3.2

- **`bot.py`** — Updated cog loading in `on_ready()` to include `cogs.code_review`

### Acceptance Criteria ✓ (Phase 3.2)

- ✓ Users can paste code and get structured feedback via `/review`
- ✓ Response uses proper syntax highlighting via Discord markdown
- ✓ Language auto-detection works; optional language parameter provides override
- ✓ Code integrates with multi-provider fallback and conversation history
- ✓ All reviews attributed to AI provider in footer

---

## [0.4.0] - 2026-03-02

### Added - Phase 3.1: Cog-Based Modular Command System

- **Cog Architecture** — Refactored all slash commands from `bot.py` into separate, reusable cog files
- **Cogs Added:**
  - `cogs/general.py` — Core commands: `/ask`, `/clear`, `/provider`
  - `cogs/summarize.py` — Conversation summarization: `/summarize`
  - (Ready for future cogs: `faq.py`, `onboarding.py`, `permissions.py`)
- **Shared Utilities** — Extracted common functions (`get_history()`, `ask_ai()`) to `utils/__init__.py` for code reuse across cogs
- **Dynamic Cog Loading** — Cogs loaded at bot startup in `on_ready()` event; new cogs can be added to `cogs/` directory without modifying core bot logic

### Changed - Phase 3.1

- **`bot.py`** — Simplified to focus on event handlers (`on_ready`, `on_message`) and dynamic cog loading
  - Removed inline slash command definitions (moved to cogs)
  - Imports shared utilities from `utils` module
  - Cleaner 106-line file vs. previous 172-line file with duplicate logic
- **`utils/__init__.py`** — New module containing `ask_ai()`, `get_history()`, `MAX_HISTORY` constant
- **`cogs/__init__.py`** — Documentation of modular cog system and available/planned cogs

### Architecture

```
Before (v0.3):
  bot.py — contains 50+ lines of command definitions
  Commands duplicated across handlers and cogs

After (v0.4):
  bot.py — 5 lines for cog loading
  cogs/general.py — clean, isolated commands
  cogs/summarize.py — clean, isolated commands
  utils/__init__.py — shared utilities
```

### Files Modified

| File | Change | Impact |
|------|--------|--------|
| `bot.py` | Simplified cog loader | -66 LOC, cleaner architecture |
| `cogs/__init__.py` | **New** | Cog system documentation |
| `cogs/general.py` | **New** | `/ask`, `/clear`, `/provider` commands |
| `cogs/summarize.py` | **New** | `/summarize` command |
| `utils/__init__.py` | **New** | Shared `ask_ai()`, `get_history()` |

### Acceptance Criteria ✓

- ✓ All existing commands work identically after refactoring
- ✓ New cogs can be added by creating a file in `cogs/` and loading it
- ✓ `bot.py` is simplified to just event handlers and cog loading
- ✓ Code duplication eliminated via `utils/` module
- ✓ Ready for Phase 3.2–3.5 (code review, FAQ, onboarding, permissions)

---

## [0.3.0] - 2026-02-19

### Added
- **Admin Dashboard** — Next.js 16 + shadcn/ui web interface for managing SparkSage
- **Setup Wizard** — 4-step guided setup on first login (Discord token → Providers → Bot settings → Review). Skippable and accessible from sidebar nav.
- **FastAPI Backend** — 19 REST API endpoints for dashboard communication
- **SQLite Database** (`db.py`) — persistent storage for config, conversations, sessions, and wizard state
- **Dashboard Pages:**
  - **Overview** — bot status, latency, guild count, active provider, fallback chain visualization, recent activity
  - **Providers** — provider cards with test/set-primary buttons, fallback chain display
  - **Settings** — live config editor with save/reset (changes apply without restart)
  - **Conversations** — per-channel viewer with chat-style messages, provider badges, timestamps
- **Authentication** — Discord OAuth2 (primary) + password fallback (dev/local) via next-auth v5
- **Unified Launcher** (`run.py`) — starts Discord bot + FastAPI server in one process
- **Live Config Reload** — `config.reload_from_db()` and `providers.reload_clients()` for runtime updates
- **Provider Testing** — `providers.test_provider()` for validating API keys from the dashboard
- **Bot Status API** — `bot.get_bot_status()` exposes online state, latency, guilds to dashboard

### Changed
- **`bot.py`** — conversations now stored in SQLite (previously in-memory), added `get_bot_status()`
- **`config.py`** — added dashboard env vars, `reload_from_db()`, `_build_providers()` for dynamic rebuilds
- **`providers.py`** — added `reload_clients()`, `test_provider()`, extracted `_build_clients()`
- **`requirements.txt`** — added fastapi, uvicorn, aiosqlite, pyjwt, python-multipart, httpx
- **`.env.example`** — added DASHBOARD section (port, password, Discord OAuth, JWT secret, DB path)
- **`.gitignore`** — added *.db, dashboard/node_modules/, dashboard/.next/, dashboard/.env.local
- **`docs/PRODUCT_DESIGN.md`** — full rewrite with dashboard architecture, API endpoints, database schema, updated roadmap

### Architecture

```
Before (v0.2):
  Discord → bot.py → providers.py → AI APIs
  Config: .env only, in-memory conversations

After (v0.3):
  Discord → bot.py ──┐
                      ├── providers.py → AI APIs
  Dashboard → FastAPI ┘
                │
            SQLite DB (config, conversations, sessions, wizard)
```

### Files Added

| File | Description |
|------|-------------|
| `db.py` | SQLite database layer (aiosqlite) |
| `run.py` | Unified launcher (bot + FastAPI) |
| `api/main.py` | FastAPI app factory with CORS |
| `api/auth.py` | JWT + password auth utilities |
| `api/deps.py` | Dependency injection |
| `api/routes/auth.py` | Login + user endpoints |
| `api/routes/config.py` | Config CRUD endpoints |
| `api/routes/providers.py` | Provider management + test endpoints |
| `api/routes/bot.py` | Bot status endpoint |
| `api/routes/conversations.py` | Conversation CRUD endpoints |
| `api/routes/wizard.py` | Setup wizard endpoints |
| `dashboard/` | Full Next.js + shadcn/ui admin dashboard (23 UI components, 4 wizard steps, 4 dashboard pages, auth, sidebar nav) |

---

## [0.2.0] - 2026-02-18

### Added
- **Multi-provider fallback system** (`providers.py`) — automatic failover across free AI providers
- **Free fallback chain:** Google Gemini 2.5 Flash → Groq (Llama 3.3 70B) → OpenRouter (DeepSeek R1)
- **Paid provider support** (optional): Anthropic Claude and OpenAI as configurable primary providers
- **`/provider` slash command** — shows active provider, model, and fallback chain status
- **Response footer** — each reply shows which AI provider generated the answer
- **Provider health check on startup** — logs active provider and full fallback chain

### Changed
- **`requirements.txt`** — replaced `anthropic` SDK with `openai` SDK (OpenAI-compatible, works with all providers)
- **`config.py`** — expanded from single-provider to multi-provider config with `PROVIDERS` dict and `FREE_FALLBACK_CHAIN`
- **`.env.example`** — now includes all 5 providers (3 free + 2 paid) with setup links and rate limit notes
- **`bot.py`** — refactored `ask_claude()` → `ask_ai()`, removed Anthropic-specific code, integrated `providers.py`
- **`docs/PRODUCT_DESIGN.md`** — updated architecture diagram, added provider comparison tables, updated roadmap

### Architecture

```
Before (v0.1):
  Discord → bot.py → Anthropic SDK → Claude API (paid only)

After (v0.2):
  Discord → bot.py → providers.py → OpenAI-compatible SDK
                                       ├── Gemini (free)
                                       ├── Groq (free)
                                       ├── OpenRouter (free)
                                       ├── Anthropic (paid, optional)
                                       └── OpenAI (paid, optional)
```

### Files Changed

| File | Action | Description |
|------|--------|-------------|
| `providers.py` | **Created** | Multi-provider client with automatic fallback logic |
| `bot.py` | Modified | Refactored to use `providers.py`, added `/provider` command, response footer |
| `config.py` | Modified | Multi-provider config, provider definitions, fallback chain |
| `requirements.txt` | Modified | `anthropic` → `openai` SDK |
| `.env.example` | Modified | All 5 providers with API key placeholders and docs links |
| `.env` | **Created** | Dummy keys for local development |
| `CHANGELOG.md` | **Created** | This file |
| `docs/PRODUCT_DESIGN.md` | Modified | Updated architecture, provider comparison, roadmap |

---

## [0.1.0] - 2026-02-18

### Added
- Initial project setup
- Discord bot with `discord.py`
- Anthropic Claude API integration
- `/ask` slash command
- `/clear` command to reset conversation memory
- `/summarize` command for thread summarization
- Per-channel conversation history (in-memory)
- Configurable model, tokens, and system prompt via `.env`
- Responds to @mentions
- Auto-splits long responses for Discord's 2000 char limit
- Project structure with `cogs/`, `utils/`, `docs/`, `tests/` directories
- Product design document with 7 use case categories and phased roadmap
