# SparkSage Deployment Demo - Loom Video Script

## Video 0: Railway Deployment Verification (1-2 minutes)

### Opening - Show Railway Dashboard (1.5 minutes)
- **Show**: Open https://railway.app in browser and navigate to deployed projects
- **Say**: "SparkSage has been successfully deployed on Railway. Let me show you the deployment dashboard."
- **Do**: Login to Railway account
- **Show**: Projects section
- **Do**: Click on SparkSage project
- **Show**: Project overview with:
  - Service status: **Running** (green indicator)
  - Deployment history
  - Recent successful builds
  - Live URLs for:
    - FastAPI Backend: [show running status]
    - Discord Bot: [show running status with uptime]
- **Say**: "Both the FastAPI backend and Discord bot are running successfully on Railway. The application is live and accessible."
- **Show**: Environment variables configured (without exposing secrets)
- **Show**: Railway logs showing bot connected to Discord
- **Say**: "The bot is actively connected to Discord and ready to receive commands."

### Closing (15 seconds)
- **Say**: "Now let's explore the deployed application starting with the web dashboard."

---

## Video 1: Dashboard Overview & Authentication (3-4 minutes)

### Opening (15 seconds)
- **Show**: Browser with deployed dashboard URL
- **Say**: "This is SparkSage's web dashboard, running live on Railway. Let me walk you through its features and authentication."

### Authentication Demo (45 seconds)
- **Show**: Navigate to dashboard login page
- **Say**: "The dashboard uses Discord OAuth for authentication. Let me sign in with Discord."
- **Do**: Click "Sign in with Discord"
- **Show**: Discord authorization page
- **Do**: Authorize the application
- **Show**: Successful redirect to dashboard home

### Dashboard Navigation (2 minutes)
- **Show**: Dashboard sidebar with all sections
- **Say**: "The dashboard has several key sections. Let me walk through each one."

**Settings Section:**
- **Show**: Click on Settings
- **Say**: "In Settings, we can view our Discord server connection and bot status."
- **Show**: Server name, bot status indicator

**Providers Section:**
- **Show**: Click on Providers
- **Say**: "Providers section shows all configured AI providers - OpenAI, Anthropic, Google Gemini, and Groq. Each can be toggled on or off."
- **Show**: List of providers with toggle switches
- **Do**: Show one provider configuration (don't reveal API keys)

**Prompts Section:**
- **Show**: Click on Channel Prompts
- **Say**: "Channel Prompts let us set custom system prompts per channel. Each channel can have its own AI personality."
- **Show**: List of configured channel prompts (if any)

**Analytics Section:**
- **Show**: Click on Analytics
- **Say**: "Analytics shows bot usage over time with interactive charts."
- **Show**: Activity chart, command usage statistics

**Costs & Quota:**
- **Show**: Click on Costs
- **Say**: "Cost tracking monitors AI API usage and spending per provider."
- **Show**: Cost breakdown chart
- **Show**: Navigate to Quota section
- **Say**: "Quota management shows rate limits per user and guild."

### Closing (30 seconds)
- **Say**: "The dashboard provides complete control over the bot configuration. Next, I'll show the plugin system."

---

## Video 2: Plugin Installation & Management (4-5 minutes)

### Opening (15 seconds)
- **Show**: Dashboard plugins page
- **Say**: "Now I'll demonstrate the plugin system. SparkSage supports custom plugins that can be installed, enabled, or disabled on demand."

### Plugin Marketplace Overview (1 minute)
- **Show**: Navigate to Plugins section in dashboard
- **Say**: "Here's the plugin marketplace showing all available plugins."
- **Show**: List of installed and available plugins
- **Point out**: Each plugin's status (enabled/disabled)

### Installing a Plugin - Method 1: Dashboard Upload (2 minutes)
- **Say**: "Let me install a new plugin through the dashboard. I'll use the test plugin package."
- **Show**: Click "Upload Plugin" or "Install Plugin" button
- **Do**: Select a plugin ZIP file (hello_test.zip or similar)
- **Show**: Upload progress
- **Show**: Success message
- **Say**: "The plugin is now installed. Let's enable it."
- **Do**: Toggle the plugin to enabled state
- **Show**: Confirmation that plugin is active

### Plugin Features Demo (1.5 minutes)
- **Show**: Switch to Discord application
- **Say**: "Let's test the plugin in Discord."
- **Do**: Type `/` to show slash commands
- **Show**: New plugin commands appear in the list
- **Do**: Execute a plugin command (e.g., `/hello` or plugin-specific command)
- **Show**: Bot response
- **Say**: "The plugin is working perfectly in the live environment."

### Managing Plugins (30 seconds)
- **Show**: Back to dashboard plugins page
- **Say**: "We can also disable or uninstall plugins anytime."
- **Do**: Toggle a plugin to disabled
- **Show**: Confirmation
- **Do**: Re-enable the plugin

### Closing (30 seconds)
- **Say**: "Plugin installation works seamlessly in the deployed version. Next, I'll demonstrate the core bot features."

---

## Video 3: Core Bot Features in Discord (5-6 minutes)

### Opening (20 seconds)
- **Show**: Discord server with bot
- **Say**: "Now let me demonstrate SparkSage's core features in Discord using the deployed version."

### Permission System (1 minute)
- **Say**: "First, the permission system. Let's check and configure command permissions."
- **Do**: Type `/permissions list`
- **Show**: List of all commands and their permissions
- **Do**: Type `/permissions set` and show autocomplete
- **Say**: "Admins can restrict commands to specific roles."
- **Do**: Example: `/permissions set command:translate roles:@Moderator`
- **Show**: Success confirmation

### AI Chat Features (1.5 minutes)
- **Say**: "The main feature is AI chat. SparkSage supports multiple providers."
- **Do**: Type `/ask What is the capital of France?`
- **Show**: Bot responds with AI-generated answer
- **Say**: "Let's try a more complex question."
- **Do**: `/ask Explain quantum computing in simple terms`
- **Show**: Detailed AI response

### Translation Feature (1 minute)
- **Say**: "Built-in translation with language detection."
- **Do**: Type `/translate Hello, how are you? target_language:Spanish`
- **Show**: Translation result
- **Do**: Type `/translate Bonjour le monde`
- **Show**: Auto-detected French, translated to English

### Channel Prompts (1 minute)
- **Say**: "Channel prompts customize AI behavior per channel."
- **Do**: Type `/prompt set prompt:You are a helpful Python programming tutor`
- **Show**: Confirmation
- **Do**: Type `/prompt show`
- **Show**: Current channel prompt displayed
- **Do**: Ask an AI question in that channel
- **Show**: Response follows the custom prompt personality

### Plugin Features (1 minute)
**Music Plugin:**
- **Say**: "Let's try the music plugin."
- **Do**: Join a voice channel
- **Do**: Type `/play query:lofi hip hop`
- **Show**: Bot joins voice channel and plays music
- **Do**: Type `/queue`
- **Show**: Current queue
- **Do**: Type `/stop`

**Poll Plugin:**
- **Say**: "Quick poll creation."
- **Do**: Type `/poll question:Best programming language? option1:Python option2:JavaScript option3:Go`
- **Show**: Poll embed with reactions
- **Show**: Voting with reactions

### FAQ System (45 seconds)
- **Say**: "FAQ management for common questions."
- **Do**: Type `/faq add question:How do I use the bot? answer:Type /help to see all commands`
- **Show**: Confirmation
- **Do**: Type `/faq get question:How do I use the bot?`
- **Show**: FAQ answer displayed

### Closing (15 seconds)
- **Say**: "All features work flawlessly in the deployed environment. The bot is production-ready."

---

## Video 4: Dashboard Analytics & Cost Monitoring (3 minutes)

### Opening (15 seconds)
- **Show**: Back to dashboard
- **Say**: "Let me show how all those Discord interactions are tracked in the dashboard."

### Real-time Analytics (1 minute)
- **Show**: Navigate to Analytics page
- **Say**: "After using the bot, analytics update in real-time."
- **Show**: Activity chart with recent spikes
- **Show**: Command usage breakdown
- **Point out**: Most used commands
- **Show**: User activity statistics

### Cost Tracking (1.5 minutes)
- **Show**: Navigate to Costs page
- **Say**: "Cost tracking shows exactly how much each AI interaction costs."
- **Show**: Cost breakdown by provider
- **Show**: Token usage statistics (input/output tokens)
- **Show**: Time-series cost chart
- **Say**: "We used Groq for free tier testing, so costs are zero, but it tracks all usage."
- **Show**: Detailed cost table with timestamps

### Rate Limiting (30 seconds)
- **Show**: Navigate to Quota page
- **Say**: "Rate limiting prevents abuse and ensures fair usage."
- **Show**: Current rate limit status per user
- **Show**: Guild-level limits

### Closing (15 seconds)
- **Say**: "The dashboard provides complete observability for production deployment."

---

## Video 5: Deployment Architecture & Conclusion (2-3 minutes)

### Architecture Overview (1.5 minutes)
- **Show**: Split screen or quick diagrams
- **Say**: "Let me explain the deployment architecture."

**Components:**
- **Say**: "The application has three main components:"
  1. **Discord Bot**: "Python bot running on Railway, handles all Discord interactions"
  2. **FastAPI Backend**: "REST API for dashboard, also on Railway"
  3. **Next.js Dashboard**: "Deployed separately, React-based web interface"

**Database:**
- **Say**: "SQLite database persists all data - permissions, prompts, costs, analytics"

**AI Providers:**
- **Say**: "Integrates with OpenAI, Anthropic, Google Gemini, and Groq APIs"

**Plugin System:**
- **Say**: "Dynamic plugin loading allows extending functionality without redeployment"

### Key Features Summary (1 minute)
- **Say**: "Key features of the deployed application:"
  - ✅ Multi-AI provider support with automatic failover
  - ✅ Role-based permission system
  - ✅ Channel-specific AI prompts
  - ✅ Cost tracking and analytics
  - ✅ Rate limiting and quota management
  - ✅ Plugin marketplace with hot-reload
  - ✅ Web dashboard with Discord OAuth
  - ✅ Music playback with YouTube integration
  - ✅ Polls, FAQs, translation, moderation
  - ✅ Fully functional in production environment

### Live Links (30 seconds)
- **Show**: Text overlay or browser
- **Say**: "Here are the live deployment links:"
  - Dashboard: [your-dashboard-url]
  - Discord Bot Invite: [your-bot-invite-link]
  - GitHub Repository: https://github.com/Jocelmay020503/Sparksage

### Closing (30 seconds)
- **Say**: "SparkSage is successfully deployed and production-ready. All features work as expected in the live environment. The application is scalable, maintainable, and ready for real-world use."
- **Show**: Final dashboard view
- **Say**: "Thank you for watching!"

---

## Recording Tips

### Before Recording:
- [ ] Clear browser history and cache
- [ ] Prepare test data (plugin ZIP, example questions)
- [ ] Join a Discord voice channel beforehand
- [ ] Have all URLs bookmarked
- [ ] Test screen recording quality
- [ ] Close unnecessary applications
- [ ] Disable notifications
- [ ] Prepare a clean Discord server for demo

### During Recording:
- Speak clearly and at moderate pace
- Pause briefly between major sections
- Show mouse cursor for clarity
- Zoom in on important UI elements
- Keep videos under 5-6 minutes each
- Avoid dead air - always explain what you're doing
- If you make a mistake, just continue (can edit later)

### Video Settings:
- Resolution: 1080p minimum
- Frame rate: 30 fps
- Audio: Clear microphone, no background noise
- Cursor: Visible with click highlights

### Post-Recording:
- Trim any dead time at start/end
- Add video titles/descriptions
- Upload to Loom
- Test all links work
- Share with proper permissions

---

## Video Checklist

- [ ] Video 0: Railway deployment verification
- [ ] Video 1: Dashboard authentication and navigation
- [ ] Video 2: Plugin installation and management
- [ ] Video 3: Core bot features in Discord
- [ ] Video 4: Analytics and cost monitoring
- [ ] Video 5: Architecture overview and conclusion

**Total estimated time: 19-24 minutes across 6 videos**
**Alternative: Combine into 3-4 longer videos (5-8 minutes each)**

---

## Quick Reference: Essential Commands to Demonstrate

```
# Permission Management
/permissions list
/permissions set command:translate roles:@Moderator

# AI Chat
/ask [question]

# Translation
/translate [text] target_language:Spanish

# Channel Prompts
/prompt set prompt:[your custom prompt]
/prompt show
/prompt clear

# Music Plugin
/play query:lofi hip hop
/queue
/skip
/stop

# Poll Plugin
/poll question:[question] option1:[option1] option2:[option2] option3:[option3]
/endpoll message_id:[id]

# FAQ Management
/faq add question:[q] answer:[a]
/faq list
/faq get question:[q]

# Plugin Management (Discord)
/plugin list
/plugin enable plugin_name:music
/plugin disable plugin_name:music
```

---

## Deployment URLs to Mention

Update these with your actual deployed URLs:

- **Dashboard**: `https://your-dashboard.railway.app` or your actual URL
- **API Backend**: `https://your-api.railway.app`
- **Discord Bot**: Running on Railway (not publicly accessible, but show it's online)
- **GitHub Repository**: https://github.com/Jocelmay020503/Sparksage
- **Discord Bot Invite**: Generate from Discord Developer Portal

---

## Troubleshooting (If Needed During Demo)

If something doesn't work during recording:

1. **Bot offline**: Check Railway logs, ensure DISCORD_TOKEN is set
2. **Dashboard won't load**: Verify deployment status, check browser console
3. **Commands not showing**: Bot needs DISCORD_GUILD_ID for instant sync
4. **Plugin upload fails**: Check file size limits, ZIP structure
5. **Music won't play**: FFmpeg must be installed (in nixpacks.toml)
6. **Costs show zero**: Expected for Groq free tier

---

**Good luck with your demo! 🎥**
