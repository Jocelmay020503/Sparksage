"""Plugin loader for SparkSage runtime plugin management."""

from __future__ import annotations

import asyncio
import concurrent.futures
import importlib.util
import inspect
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from discord.ext import commands


@dataclass(slots=True)
class PluginManifest:
    """Represents a plugin manifest.json entry."""

    name: str
    version: str
    author: str
    description: str
    cog: str
    requirements: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginManifest":
        required_fields = ("name", "version", "author", "description", "cog")
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValueError(f"Missing required manifest fields: {missing}")

        cog = str(data["cog"]).strip()
        cog_path = Path(cog)
        if (
            cog_path.is_absolute()
            or ".." in cog_path.parts
            or cog_path.suffix != ".py"
            or cog_path.name != cog
        ):
            raise ValueError("Manifest field 'cog' must be a local Python filename ending in .py")

        requirements = data.get("requirements", [])
        if requirements is None:
            requirements = []
        if not isinstance(requirements, list):
            raise ValueError("Manifest field 'requirements' must be a list")

        return cls(
            name=str(data["name"]).strip(),
            version=str(data["version"]).strip(),
            author=str(data["author"]).strip(),
            description=str(data["description"]).strip(),
            cog=cog,
            requirements=[str(item) for item in requirements],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "cog": self.cog,
            "requirements": self.requirements,
        }


class PluginLoader:
    """Manages plugin discovery, loading, and lifecycle."""

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_cogs: Dict[str, str] = {}
        self.loaded_modules: Dict[str, str] = {}
        self.manifests: Dict[str, PluginManifest] = {}
        self.plugin_dirs: Dict[str, Path] = {}
        self.discovery_errors: Dict[str, str] = {}
        self._bot: Optional[commands.Bot] = None
        self._bot_loop: Optional[asyncio.AbstractEventLoop] = None

    def bind_bot(self, bot: commands.Bot):
        """Bind the active bot instance so APIs can manage plugins at runtime."""
        self._bot = bot
        self._bot_loop = bot.loop

    def is_bot_running(self) -> bool:
        return bool(self._bot and self._bot_loop and self._bot_loop.is_running())

    def discover_plugins(self) -> List[str]:
        """Find all plugins in plugins directory with valid manifests."""
        self.manifests.clear()
        self.plugin_dirs.clear()
        self.discovery_errors.clear()

        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        for plugin_folder in sorted(self.plugins_dir.iterdir()):
            if not plugin_folder.is_dir() or plugin_folder.name.startswith("_"):
                continue

            manifest_file = plugin_folder / "manifest.json"
            if not manifest_file.exists():
                continue

            try:
                with manifest_file.open("r", encoding="utf-8") as manifest_handle:
                    raw_manifest = json.load(manifest_handle)

                manifest = PluginManifest.from_dict(raw_manifest)
                if manifest.name in self.manifests:
                    raise ValueError(f"Duplicate plugin name in manifests: {manifest.name}")

                self.manifests[manifest.name] = manifest
                self.plugin_dirs[manifest.name] = plugin_folder
            except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
                self.discovery_errors[plugin_folder.name] = str(exc)
                print(f"Error loading plugin manifest for {plugin_folder.name}: {exc}")

        return sorted(self.manifests.keys())

    def resolve_plugin_name(self, plugin_name: str) -> Optional[str]:
        """Resolve plugin name in a case-insensitive way."""
        lookup = plugin_name.strip().lower()
        for name in self.manifests:
            if name.lower() == lookup:
                return name
        return None

    def get_manifest(self, plugin_name: str) -> Optional[PluginManifest]:
        resolved = self.resolve_plugin_name(plugin_name)
        if not resolved:
            return None
        return self.manifests.get(resolved)

    def get_plugin_path(self, plugin_name: str) -> Optional[Path]:
        """Get the directory path for a plugin."""
        resolved = self.resolve_plugin_name(plugin_name)
        if not resolved:
            return None
        return self.plugin_dirs.get(resolved)

    def _find_cog_class(self, module: Any) -> Optional[type[commands.Cog]]:
        for attribute in module.__dict__.values():
            if (
                isinstance(attribute, type)
                and issubclass(attribute, commands.Cog)
                and attribute is not commands.Cog
            ):
                return attribute
        return None

    def _remove_module_from_cache(self, module_name: str):
        to_remove = [name for name in sys.modules if name == module_name or name.startswith(f"{module_name}.")]
        for name in to_remove:
            sys.modules.pop(name, None)

    async def load_plugin_cog(
        self,
        bot: commands.Bot,
        plugin_name: str,
        sync_commands: bool = True,
    ) -> tuple[bool, str]:
        """Load a plugin's cog into the bot at runtime."""
        try:
            self.bind_bot(bot)
            self.discover_plugins()

            resolved_name = self.resolve_plugin_name(plugin_name)
            if not resolved_name:
                return False, f"Plugin '{plugin_name}' not found"

            if resolved_name in self.loaded_cogs:
                return True, f"Plugin '{resolved_name}' is already loaded"

            manifest = self.manifests[resolved_name]
            plugin_path = self.plugin_dirs.get(resolved_name)
            if not plugin_path:
                return False, f"Plugin directory for '{resolved_name}' not found"

            cog_file = plugin_path / manifest.cog
            if not cog_file.exists():
                return False, f"Cog file '{manifest.cog}' not found in plugin '{resolved_name}'"

            module_name = f"sparksage_plugins.{resolved_name}.{cog_file.stem}"
            self._remove_module_from_cache(module_name)

            spec = importlib.util.spec_from_file_location(module_name, cog_file)
            if not spec or not spec.loader:
                return False, f"Failed to load module spec for {resolved_name}"

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
            except Exception:
                self._remove_module_from_cache(module_name)
                raise

            cogs_before = set(bot.cogs.keys())

            setup_fn = getattr(module, "setup", None)
            if callable(setup_fn):
                setup_result = setup_fn(bot)
                if inspect.isawaitable(setup_result):
                    await setup_result
            else:
                cog_class = self._find_cog_class(module)
                if cog_class is None:
                    self._remove_module_from_cache(module_name)
                    return False, f"No Cog class or setup() found in {manifest.cog}"
                await bot.add_cog(cog_class(bot))

            cogs_after = set(bot.cogs.keys())
            added_cogs = sorted(cogs_after - cogs_before)
            cog_name = added_cogs[0] if added_cogs else manifest.name

            self.loaded_cogs[resolved_name] = cog_name
            self.loaded_modules[resolved_name] = module_name

            if sync_commands:
                # Sync to guild first for instant updates, then global
                try:
                    import config
                    if config.DISCORD_GUILD_ID:
                        try:
                            import discord
                            guild_id = int(config.DISCORD_GUILD_ID)
                            guild_obj = discord.Object(id=guild_id)
                            # Copy global commands to guild before syncing (includes new plugin commands)
                            bot.tree.copy_global_to(guild=guild_obj)
                            guild_synced = await bot.tree.sync(guild=guild_obj)
                            print(f"✅ Plugin '{resolved_name}' loaded - Commands synced to guild {guild_id} (INSTANT)")
                        except ValueError as ve:
                            print(f"❌ Invalid DISCORD_GUILD_ID: {config.DISCORD_GUILD_ID} - {ve}")
                        except Exception as ge:
                            print(f"❌ Failed to sync to guild: {ge}")
                    else:
                        print(f"ℹ️  DISCORD_GUILD_ID not set - guild sync skipped. Commands will appear after global sync (up to 1 hour)")
                    
                    # Also sync globally (takes up to 1 hour to propagate)
                    global_synced = await bot.tree.sync()
                    print(f"✅ Global sync completed - {len(global_synced)} total command(s)")
                except Exception as e:
                    print(f"❌ Unexpected error during sync: {e}")

            return True, f"Plugin '{resolved_name}' loaded successfully"
        except Exception as exc:
            return False, f"Error loading plugin '{plugin_name}': {exc}"

    async def unload_plugin_cog(
        self,
        bot: commands.Bot,
        plugin_name: str,
        sync_commands: bool = True,
    ) -> tuple[bool, str]:
        """Unload a plugin's cog from the bot at runtime."""
        try:
            self.bind_bot(bot)
            resolved_name = self.resolve_plugin_name(plugin_name) or plugin_name

            if resolved_name not in self.loaded_cogs and resolved_name not in self.loaded_modules:
                return False, f"Plugin '{resolved_name}' is not loaded"

            module_name = self.loaded_modules.get(resolved_name)
            cogs_to_remove: List[str] = []

            if module_name:
                cogs_to_remove.extend(
                    [
                        cog_name
                        for cog_name, cog in bot.cogs.items()
                        if getattr(cog, "__module__", "") == module_name
                    ]
                )

            fallback_cog = self.loaded_cogs.get(resolved_name)
            if fallback_cog and fallback_cog in bot.cogs and fallback_cog not in cogs_to_remove:
                cogs_to_remove.append(fallback_cog)

            for cog_name in cogs_to_remove:
                await bot.remove_cog(cog_name)

            self.loaded_cogs.pop(resolved_name, None)
            if module_name:
                self._remove_module_from_cache(module_name)
            self.loaded_modules.pop(resolved_name, None)

            if sync_commands:
                # Sync to guild first for instant removal, then global
                try:
                    import config
                    if config.DISCORD_GUILD_ID:
                        try:
                            import discord
                            guild_id = int(config.DISCORD_GUILD_ID)
                            guild_obj = discord.Object(id=guild_id)
                            # DON'T copy_global_to here - we want to remove commands, not add them back
                            # Just sync the current tree state (which has commands removed)
                            guild_synced = await bot.tree.sync(guild=guild_obj)
                            print(f"✅ Plugin '{resolved_name}' unloaded - Commands removed from guild {guild_id} (INSTANT)")
                        except ValueError as ve:
                            print(f"❌ Invalid DISCORD_GUILD_ID: {config.DISCORD_GUILD_ID} - {ve}")
                        except Exception as ge:
                            print(f"❌ Failed to sync to guild: {ge}")
                    else:
                        print(f"ℹ️  DISCORD_GUILD_ID not set - guild sync skipped. Commands will be removed after global sync (up to 1 hour)")
                    
                    # Also sync globally (takes up to 1 hour to propagate)
                    global_synced = await bot.tree.sync()
                    print(f"✅ Global sync completed - {len(global_synced)} total command(s)")
                except Exception as e:
                    print(f"❌ Unexpected error during sync: {e}")

            return True, f"Plugin '{resolved_name}' unloaded successfully"
        except Exception as exc:
            return False, f"Error unloading plugin '{plugin_name}': {exc}"

    def _run_on_bot_loop(self, coroutine: Any, timeout: float = 30.0) -> tuple[bool, str]:
        if not self._bot_loop or not self._bot_loop.is_running():
            return False, "Bot event loop is not running"

        future = asyncio.run_coroutine_threadsafe(coroutine, self._bot_loop)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            future.cancel()
            return False, "Plugin operation timed out"
        except Exception as exc:
            return False, f"Plugin operation failed: {exc}"

    def load_plugin_cog_threadsafe(
        self,
        plugin_name: str,
        sync_commands: bool = True,
        timeout: float = 30.0,
    ) -> tuple[bool, str]:
        if not self._bot:
            return False, "Bot is not connected"
        return self._run_on_bot_loop(
            self.load_plugin_cog(self._bot, plugin_name, sync_commands=sync_commands),
            timeout=timeout,
        )

    def unload_plugin_cog_threadsafe(
        self,
        plugin_name: str,
        sync_commands: bool = True,
        timeout: float = 30.0,
    ) -> tuple[bool, str]:
        if not self._bot:
            return False, "Bot is not connected"
        return self._run_on_bot_loop(
            self.unload_plugin_cog(self._bot, plugin_name, sync_commands=sync_commands),
            timeout=timeout,
        )

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get plugin information."""
        resolved_name = self.resolve_plugin_name(plugin_name)
        if not resolved_name:
            return None

        manifest = self.manifests[resolved_name]
        return {
            "name": manifest.name,
            "version": manifest.version,
            "author": manifest.author,
            "description": manifest.description,
            "loaded": resolved_name in self.loaded_cogs,
            "cog_name": self.loaded_cogs.get(resolved_name),
        }

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all available plugins with their runtime status."""
        result: List[Dict[str, Any]] = []
        for plugin_name in self.discover_plugins():
            info = self.get_plugin_info(plugin_name)
            if info:
                result.append(info)
        return result


plugin_loader = PluginLoader()
