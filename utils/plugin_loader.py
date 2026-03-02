"""
Plugin system for loading community-contributed cogs dynamically.

Plugins are stored in the plugins/ directory with the following structure:
plugins/
    plugin_name/
        __init__.py
        cog.py (contains the Cog class)
        plugin.json (manifest file)
        
The plugin.json manifest should contain:
{
    "name": "plugin_name",
    "version": "1.0.0",
    "author": "Author Name",
    "description": "Plugin description",
    "cog_class": "MyCog",
    "discord_py_version": "2.3.0",
    "dependencies": []
}
"""

import json
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class PluginManifest:
    """Represents a plugin manifest (plugin.json)."""
    
    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("name")
        self.version = data.get("version", "1.0.0")
        self.author = data.get("author", "Unknown")
        self.description = data.get("description", "")
        self.cog_class = data.get("cog_class")
        self.discord_py_version = data.get("discord_py_version")
        self.dependencies = data.get("dependencies", [])
        self.commands = data.get("commands", [])
        self.permissions = data.get("permissions", [])
        
    def validate(self) -> tuple[bool, str]:
        """Validate the plugin manifest."""
        if not self.name:
            return False, "Plugin name is required"
        if not self.cog_class:
            return False, "Cog class name is required"
        if not self.version:
            return False, "Plugin version is required"
        return True, "Valid"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "cog_class": self.cog_class,
            "discord_py_version": self.discord_py_version,
            "dependencies": self.dependencies,
            "commands": self.commands,
            "permissions": self.permissions,
        }


class Plugin:
    """Represents a loaded plugin."""
    
    def __init__(self, manifest: PluginManifest, path: Path, cog_class: Any):
        self.manifest = manifest
        self.path = path
        self.cog_class = cog_class
        self.enabled = False
        
    @property
    def name(self) -> str:
        return self.manifest.name
    
    @property
    def version(self) -> str:
        return self.manifest.version


class PluginLoader:
    """Manages loading and unloading of plugins."""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, Plugin] = {}
        self.loaded_plugins: List[str] = []
        
        # Create plugins directory if it doesn't exist
        self.plugins_dir.mkdir(exist_ok=True)
        
    def discover_plugins(self) -> List[str]:
        """
        Discover all available plugins in the plugins directory.
        Returns a list of plugin names.
        """
        discovered = []
        
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory {self.plugins_dir} does not exist")
            return discovered
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith("_"):
                manifest_path = plugin_dir / "plugin.json"
                if manifest_path.exists():
                    discovered.append(plugin_dir.name)
                else:
                    logger.warning(f"Plugin {plugin_dir.name} missing plugin.json")
        
        return discovered
    
    def load_plugin_manifest(self, plugin_name: str) -> Optional[PluginManifest]:
        """Load and parse a plugin's manifest file."""
        manifest_path = self.plugins_dir / plugin_name / "plugin.json"
        
        if not manifest_path.exists():
            logger.error(f"Manifest not found for plugin: {plugin_name}")
            return None
        
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            manifest = PluginManifest(data)
            is_valid, error = manifest.validate()
            
            if not is_valid:
                logger.error(f"Invalid manifest for {plugin_name}: {error}")
                return None
            
            return manifest
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse manifest for {plugin_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading manifest for {plugin_name}: {e}")
            return None
    
    def load_plugin(self, plugin_name: str) -> tuple[bool, str]:
        """
        Load a plugin by name.
        Returns (success, message).
        """
        # Check if already loaded
        if plugin_name in self.plugins:
            return False, f"Plugin {plugin_name} is already loaded"
        
        # Load manifest
        manifest = self.load_plugin_manifest(plugin_name)
        if not manifest:
            return False, f"Failed to load manifest for {plugin_name}"
        
        # Load the cog module
        plugin_path = self.plugins_dir / plugin_name
        cog_path = plugin_path / "cog.py"
        
        if not cog_path.exists():
            return False, f"Cog file not found: {cog_path}"
        
        try:
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}.cog",
                cog_path
            )
            if spec is None or spec.loader is None:
                return False, f"Failed to load module spec for {plugin_name}"
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Get the cog class
            if not hasattr(module, manifest.cog_class):
                return False, f"Cog class {manifest.cog_class} not found in module"
            
            cog_class = getattr(module, manifest.cog_class)
            
            # Create plugin instance
            plugin = Plugin(manifest, plugin_path, cog_class)
            self.plugins[plugin_name] = plugin
            
            logger.info(f"Successfully loaded plugin: {plugin_name} v{manifest.version}")
            return True, f"Plugin {plugin_name} loaded successfully"
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}", exc_info=True)
            return False, f"Error loading plugin: {str(e)}"
    
    def unload_plugin(self, plugin_name: str) -> tuple[bool, str]:
        """
        Unload a plugin by name.
        Returns (success, message).
        """
        if plugin_name not in self.plugins:
            return False, f"Plugin {plugin_name} is not loaded"
        
        try:
            # Remove from loaded plugins
            del self.plugins[plugin_name]
            
            # Remove from sys.modules
            module_name = f"plugins.{plugin_name}.cog"
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            logger.info(f"Successfully unloaded plugin: {plugin_name}")
            return True, f"Plugin {plugin_name} unloaded successfully"
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False, f"Error unloading plugin: {str(e)}"
    
    def reload_plugin(self, plugin_name: str) -> tuple[bool, str]:
        """
        Reload a plugin by unloading and loading it again.
        Returns (success, message).
        """
        if plugin_name in self.plugins:
            success, message = self.unload_plugin(plugin_name)
            if not success:
                return False, f"Failed to unload: {message}"
        
        return self.load_plugin(plugin_name)
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a loaded plugin by name."""
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, Plugin]:
        """Get all loaded plugins."""
        return self.plugins.copy()
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a plugin."""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            # Try to load manifest even if not loaded
            manifest = self.load_plugin_manifest(plugin_name)
            if manifest:
                return {
                    "name": manifest.name,
                    "version": manifest.version,
                    "author": manifest.author,
                    "description": manifest.description,
                    "loaded": False,
                    "enabled": False,
                }
            return None
        
        return {
            "name": plugin.name,
            "version": plugin.version,
            "author": plugin.manifest.author,
            "description": plugin.manifest.description,
            "loaded": True,
            "enabled": plugin.enabled,
            "commands": plugin.manifest.commands,
            "permissions": plugin.manifest.permissions,
        }


# Global plugin loader instance
_plugin_loader: Optional[PluginLoader] = None


def get_plugin_loader() -> PluginLoader:
    """Get the global plugin loader instance."""
    global _plugin_loader
    if _plugin_loader is None:
        _plugin_loader = PluginLoader()
    return _plugin_loader
