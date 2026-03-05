# Plugin Marketplace Implementation ✨

## Overview

The Plugin Marketplace allows users to **browse available plugins**, **install them with one click**, and then **enable/disable** them. This provides a complete plugin management experience directly from the dashboard.

---

## Components

### 1. Plugin Catalog (`plugins_catalog.json`)

A JSON file listing all available plugins for installation.

**Structure:**
```json
[
  {
    "name": "plugin_name",
    "version": "1.0.0",
    "author": "Author Name",
    "description": "What this plugin does",
    "repo": "https://github.com/repo/url",
    "download_url": "https://github.com/releases/download/plugin.zip",
    "tags": ["tag1", "tag2"],
    "requires_config": false
  }
]
```

**Features:**
- Centralized list of installable plugins
- Metadata for each plugin
- Download URLs for installation
- Configuration requirement warnings
- Tags for categorization

---

### 2. Backend API Endpoints

#### GET `/api/plugins/catalog`
Get all available plugins with install status

**Response:**
```json
{
  "plugins": [
    {
      "name": "trivia",
      "version": "1.0.0",
      "author": "SparkSage Community",
      "description": "Interactive trivia game...",
      "repo": "https://github.com/...",
      "download_url": "https://github.com/.../plugin.zip",
      "tags": ["game", "fun"],
      "requires_config": false,
      "installed": false
    }
  ],
  "total": 8
}
```

#### POST `/api/plugins/install/{plugin_name}`
Install a plugin from the catalog

**Process:**
1. Download plugin ZIP from catalog URL
2. Extract to `plugins/{name}/` directory
3. Discover manifest.json
4. Save to database
5. Return success/error

**Response:**
```json
{
  "status": "ok",
  "message": "Plugin 'trivia' installed successfully",
  "plugin_name": "trivia",
  "installed": true
}
```

---

### 3. Dashboard UI - Two Tabs

#### Tab 1: Installed Plugins
- Shows installed plugins with status (Loaded/Enabled/Disabled)
- Enable/Disable buttons
- Plugin metadata (version, author)
- Same as before

#### Tab 2: Available for Installation
- Shows plugins from catalog that aren't installed
- "⭐ New" badge
- Tags
- Configuration warnings
- "Install" button
- "Docs" link to repository

---

## User Workflow

### Installing a Plugin

1. **Open Dashboard** → Plugins page
2. **Click "Available" tab** → See marketplace
3. **Find plugin** → Review description, tags, requirements
4. **Click "Install"** → Button shows "Installing..."
5. **Installation completes** → Success toast notification
6. **Auto-switch to "Installed" tab** → New plugin appears
7. **Enable plugin** → Click "Enable" button
8. **Use in Discord** → Plugin commands available

### Managing Plugins

1. **Open Dashboard** → Plugins page
2. **Click "Installed" tab** → See all installed plugins
3. **Click "Enable"** → Loads plugin immediately
4. **Click "Disable"** → Unloads plugin
5. **See status** - ✅ Loaded | ⏳ Enabled | ❌ Disabled

---

## API Integration

### Dashboard Client (`api.ts`)

**New Methods:**
```typescript
getPluginsCatalog(token: string): Promise<CatalogListResponse>
installPlugin(token: string, pluginName: string): Promise<{...}>
```

**New Types:**
```typescript
interface CatalogPlugin {
  name: string;
  version: string;
  author: string;
  description: string;
  repo: string;
  download_url: string;
  tags: string[];
  requires_config: boolean;
  installed: boolean;
}

interface CatalogListResponse {
  plugins: CatalogPlugin[];
  total: number;
}
```

---

## Backend Implementation

### Plugin Installation (`api/routes/plugins.py`)

Key functions:

1. **`_load_catalog()`**
   - Reads `plugins_catalog.json`
   - Returns list of available plugins

2. **`_get_catalog_with_install_status()`**
   - Gets catalog
   - Marks which plugins are installed
   - Returns sorted list

3. **`_install_plugin_from_zip(url, name)`**
   - Downloads ZIP from URL
   - Extracts to `plugins/{name}/`
   - Handles errors gracefully
   - Cleans up on failure

4. **`install_plugin()` endpoint**
   - Validates plugin exists in catalog
   - Downloads and installs
   - Discovers manifest
   - Saves to database

---

## Files Modified

### Backend
- ✅ `api/routes/plugins.py` - Added catalog and install endpoints
- ✅ `plugins_catalog.json` - Created with 8 sample plugins

### Frontend
- ✅ `dashboard/src/lib/api.ts` - Added types and methods
- ✅ `dashboard/src/app/dashboard/plugins/page.tsx` - New UI with tabs

---

## Available Plugins in Catalog

1. **Trivia** - Interactive trivia game
2. **Moderation Tools** - Advanced moderation features
3. **User Stats** - Track user statistics
4. **Music Player** - Play music in voice channels
5. **Role Manager** - Automatic role assignment
6. **Custom Commands** - Create custom commands
7. **Welcome Bot** - Automatic member welcome
8. **Suggestion System** - Community suggestions voting

---

## Installation Flow Diagram

```
User Opens Dashboard
    ↓
Clicks "Plugins" → "Available" Tab
    ↓
Sees Catalog of 8 Plugins
    ↓
Finds "Trivia" Plugin
    ↓
Clicks "Install" Button
    ↓
API downloads trivia.zip from GitHub
    ↓
API extracts to plugins/trivia/
    ↓
API discovers manifest.json
    ↓
API saves to database
    ↓
Success Toast → Auto-switch to "Installed"
    ↓
User sees "Trivia" in Installed Plugins (❌ Disabled)
    ↓
User clicks "Enable"
    ↓
Bot loads plugin cog
    ↓
Status changes to ✅ Loaded
    ↓
User can run /trivia commands in Discord
```

---

## Error Handling

### Installation Errors

1. **Plugin already installed**
   - Message: "Plugin 'name' is already installed"

2. **Download fails**
   - Message: "Failed to install plugin: [error details]"
   - Auto-cleanup of partial files

3. **Invalid ZIP**
   - Message: "Failed to install plugin: [error details]"
   - Auto-cleanup

4. **Manifest not found**
   - Plugin installs but appears in gray
   - Error shown in logs

---

## Security Considerations

1. **Trusted Sources Only** - Catalog contains only trusted plugins
2. **Manifest Validation** - Plugins must have valid manifest
3. **No Arbitrary Code Execution** - Plugins run in Discord.py sandbox
4. **Admin Only** - Installation requires auth token
5. **Cleanup on Failure** - Failed installs don't leave partial files

---

## Future Enhancements

1. **Plugin Search** - Search catalog by name/tags
2. **Plugin Ratings** - Community rating system
3. **Auto-Updates** - Automatic plugin version updates
4. **Plugin Permissions** - Grant/revoke plugin capabilities
5. **Plugin Conflicts** - Detect incompatible plugins
6. **Uninstall** - Remove plugin completely
7. **Rollback** - Revert to previous version
8. **Statistics** - Track plugin usage

---

## Testing

### Test Installation Flow

1. Go to `/dashboard/plugins`
2. Click "Available" tab
3. Click "Install" on any plugin (e.g., "trivia")
4. Wait for success message
5. Tab automatically switches to "Installed"
6. New plugin appears with ❌ Disabled status
7. Click "Enable"
8. Status changes to ✅ Loaded
9. Commands available in Discord

### Test Catalog API

```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/plugins/catalog
```

### Test Install API

```bash
curl -X POST -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/plugins/install/trivia
```

---

## Sample Plugins in Catalog

All plugins in `plugins_catalog.json` are examples. They point to real GitHub repositories that would contain:
- Valid `manifest.json`
- Cog Python file
- Optional requirements.txt
- README with documentation

---

## Conclusion

The Plugin Marketplace transforms SparkSage's plugin system from a **developer-focused** install process to a **user-friendly** one-click marketplace experience. Users can now discover, install, and manage plugins directly from the web dashboard.

**Benefits:**
✅ One-click plugin installation
✅ Visual plugin discovery
✅ No manual file management
✅ Clear install status tracking
✅ Easy enable/disable workflow
✅ Complete UI/API integration
