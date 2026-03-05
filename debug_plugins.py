#!/usr/bin/env python3
"""Debug script to verify plugin loading and command registration."""

import asyncio
import json
from pathlib import Path
import sys

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent))

from plugin_loader import plugin_loader
import config


async def debug_plugins():
    """Check plugin status and command registration."""
    print("=" * 70)
    print("🔧 SparkSage Plugin Diagnostic")
    print("=" * 70)
    
    # Check config
    print(f"\n📋 Configuration:")
    print(f"  DISCORD_GUILD_ID: {config.DISCORD_GUILD_ID or '(not set - syncing will take up to 1 hour)'}")
    print(f"  DISCORD_TOKEN: {'Set ✅' if config.DISCORD_TOKEN else 'NOT SET ❌'}")
    
    # Discover plugins
    print(f"\n🔍 Discovering plugins...")
    discovered = plugin_loader.discover_plugins()
    print(f"  Found {len(discovered)} plugin(s): {', '.join(discovered)}")
    
    if plugin_loader.discovery_errors:
        print(f"\n  ⚠️  Discovery errors:")
        for plugin_name, error in plugin_loader.discovery_errors.items():
            print(f"     - {plugin_name}: {error}")
    
    # Check manifest and cog files
    print(f"\n📦 Plugin Details:")
    for plugin_name in discovered:
        manifest = plugin_loader.get_manifest(plugin_name)
        plugin_path = plugin_loader.get_plugin_path(plugin_name)
        
        if manifest and plugin_path:
            cog_file = plugin_path / manifest.cog
            exists = "✅" if cog_file.exists() else "❌"
            print(f"\n  {plugin_name}:")
            print(f"    Path: {plugin_path}")
            print(f"    Cog File: {manifest.cog} {exists}")
            print(f"    Version: {manifest.version}")
            print(f"    Author: {manifest.author}")
            print(f"    Description: {manifest.description}")
            
            if cog_file.exists() and manifest.cog.endswith('.py'):
                try:
                    with open(cog_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    has_setup = '@app_commands.command' in content or 'app_commands.Group' in content
                    has_setup_fn = 'async def setup' in content or 'def setup' in content
                    status = "✅ Has commands" if has_setup else "⚠️ No app_commands found"
                    print(f"    Commands: {status}")
                    print(f"    Setup function: {'✅' if has_setup_fn else '❌'}")
                except Exception as e:
                    print(f"    Error reading file: {e}")
        else:
            print(f"\n  {plugin_name}: ❌ Manifest or path not found")
    
    # Load plugins (need a mock bot instance)
    print(f"\n⚙️  Loading plugins test (requires discord.py bot instance):")
    print("  Note: Full loading test requires a running Discord bot")
    print("  To test enable/disable, use the dashboard or Discord commands.")
    
    print(f"\n" + "=" * 70)
    print("💡 Next steps:")
    print("  1. If DISCORD_GUILD_ID is set - commands should appear instantly")
    print("  2. If not set - wait up to 1 hour for global sync")
    print("  3. Check bot console for 'Synced X command(s)' messages")
    print("  4. Enable plugins via dashboard: /plugin enable <name>")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(debug_plugins())
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
