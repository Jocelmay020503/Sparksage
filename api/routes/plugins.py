"""Plugin management API endpoints for SparkSage dashboard."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from api.deps import get_current_user
import db
from plugin_loader import plugin_loader

router = APIRouter(prefix="/api/plugins", tags=["plugins"])

_DISCOVERY_CACHE_TTL_SECONDS = 10.0
_last_discovery_sync_at = 0.0
_discovery_sync_lock = asyncio.Lock()


class PluginInfo(BaseModel):
    """Plugin information model."""

    name: str
    version: str
    author: str
    description: str
    enabled: bool
    loaded: bool
    cog_name: Optional[str] = None


class CatalogPlugin(BaseModel):
    """Available plugin from catalog."""

    name: str
    version: str
    author: str
    description: str
    repo: str
    download_url: str
    tags: List[str]
    requires_config: bool
    installed: bool = False


class PluginListResponse(BaseModel):
    """Response for plugin list."""

    plugins: List[PluginInfo]
    total: int


class CatalogListResponse(BaseModel):
    """Response for catalog list."""

    plugins: List[CatalogPlugin]
    total: int


class PluginsOverviewResponse(BaseModel):
    """Combined plugin + catalog payload for faster dashboard loading."""

    plugins: List[PluginInfo]
    plugins_total: int
    catalog: List[CatalogPlugin]
    catalog_total: int


async def _sync_discovered_manifests(force: bool = False):
    """Refresh plugin discovery and persist manifest metadata with basic TTL caching."""
    global _last_discovery_sync_at

    now = time.monotonic()
    if not force and (now - _last_discovery_sync_at) < _DISCOVERY_CACHE_TTL_SECONDS:
        return

    async with _discovery_sync_lock:
        now = time.monotonic()
        if not force and (now - _last_discovery_sync_at) < _DISCOVERY_CACHE_TTL_SECONDS:
            return

        plugin_loader.discover_plugins()
        manifests = [
            (
                manifest.name,
                manifest.version,
                manifest.author,
                manifest.description,
            )
            for manifest in plugin_loader.manifests.values()
        ]
        await db.save_plugin_manifests_bulk(manifests)
        _last_discovery_sync_at = time.monotonic()


def _get_discovered_plugins_snapshot() -> list[dict[str, Any]]:
    """Build plugin info from the already-discovered manifest cache."""
    discovered: list[dict[str, Any]] = []
    for manifest in plugin_loader.manifests.values():
        discovered.append(
            {
                "name": manifest.name,
                "version": manifest.version,
                "author": manifest.author,
                "description": manifest.description,
                "loaded": manifest.name in plugin_loader.loaded_cogs,
                "cog_name": plugin_loader.loaded_cogs.get(manifest.name),
            }
        )
    return discovered


async def _get_merged_plugins() -> list[dict[str, Any]]:
    await _sync_discovered_manifests()

    discovered = _get_discovered_plugins_snapshot()
    discovered_by_name = {item["name"]: item for item in discovered}

    db_plugins = await db.get_all_plugins()
    db_by_name = {item["name"]: item for item in db_plugins}

    merged: list[dict[str, Any]] = []

    for name, loader_item in discovered_by_name.items():
        db_item = db_by_name.get(name, {})
        merged.append(
            {
                "name": name,
                "version": loader_item["version"],
                "author": loader_item["author"],
                "description": loader_item["description"],
                "enabled": bool(db_item.get("enabled", False)),
                "loaded": bool(loader_item.get("loaded", False)),
                "cog_name": loader_item.get("cog_name"),
            }
        )

    for name, db_item in db_by_name.items():
        if name in discovered_by_name:
            continue
        merged.append(
            {
                "name": name,
                "version": db_item.get("version") or "1.0.0",
                "author": db_item.get("author") or "unknown",
                "description": db_item.get("description") or "",
                "enabled": bool(db_item.get("enabled", False)),
                "loaded": name in plugin_loader.loaded_cogs,
                "cog_name": plugin_loader.loaded_cogs.get(name),
            }
        )

    return sorted(merged, key=lambda item: item["name"].lower())


async def _find_plugin_or_404(plugin_name: str) -> dict[str, Any]:
    lookup = plugin_name.strip().lower()
    for plugin in await _get_merged_plugins():
        if plugin["name"].lower() == lookup:
            return plugin
    raise HTTPException(status_code=404, detail="Plugin not found")


def _load_catalog() -> List[dict[str, Any]]:
    """Load the plugins catalog from JSON file."""
    catalog_path = Path("plugins_catalog.json")
    if not catalog_path.exists():
        return []
    
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


async def _get_catalog_with_install_status() -> List[dict[str, Any]]:
    """Get catalog plugins marked with whether they're installed."""
    catalog = _load_catalog()
    installed_names = {p["name"] for p in await _get_merged_plugins()}
    
    for plugin in catalog:
        plugin["installed"] = plugin["name"] in installed_names
    
    return sorted(catalog, key=lambda p: p["name"])


class PluginInstallError(Exception):
    """Raised when plugin installation fails with a specific HTTP status."""

    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.status_code = status_code


def _download_plugin_zip(zip_url: str, temp_zip: Path, plugin_name: str):
    """Download plugin ZIP from URL or local path into temp file."""
    parsed = urlparse(zip_url)
    fallback_zip = Path("plugins_downloads") / f"{plugin_name}.zip"

    if parsed.scheme in {"http", "https", "file"}:
        try:
            with urlopen(zip_url, timeout=30) as response, temp_zip.open("wb") as output:
                shutil.copyfileobj(response, output)
            return
        except (HTTPError, URLError) as exc:
            if fallback_zip.exists():
                shutil.copy2(fallback_zip, temp_zip)
                return

            if isinstance(exc, HTTPError):
                reason = f"HTTP {exc.code}"
            else:
                reason = str(getattr(exc, "reason", exc))

            raise PluginInstallError(
                f"Failed to download plugin '{plugin_name}' from '{zip_url}' ({reason})",
                status_code=502,
            ) from exc

    source = Path(zip_url)
    if not source.is_absolute():
        source = Path.cwd() / source

    if not source.exists():
        raise PluginInstallError(
            f"Plugin ZIP not found at '{source}'",
            status_code=502,
        )

    shutil.copy2(source, temp_zip)


def _select_plugin_root(extract_root: Path, plugin_name: str) -> Path:
    """Pick the directory that contains a valid manifest + cog pair."""
    candidates: list[tuple[int, Path]] = []

    for manifest_path in extract_root.rglob("manifest.json"):
        try:
            raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        manifest_name = str(raw_manifest.get("name", "")).strip()
        cog_name = str(raw_manifest.get("cog", "")).strip()
        if not cog_name:
            continue

        cog_path = manifest_path.parent / cog_name
        if not cog_path.exists() or not cog_path.is_file():
            continue

        score = 0
        if manifest_name.lower() == plugin_name.lower():
            score += 3
        if manifest_path.parent.name.lower() == plugin_name.lower():
            score += 1

        candidates.append((score, manifest_path.parent))

    if not candidates:
        raise PluginInstallError(
            f"Plugin archive for '{plugin_name}' is missing a valid manifest/cog layout",
            status_code=422,
        )

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _extract_plugin_payload(temp_zip: Path, plugin_dir: Path, plugin_name: str):
    """Extract ZIP safely and normalize plugin files into plugins/<plugin_name>."""
    try:
        with tempfile.TemporaryDirectory() as extract_tmp:
            extract_root = Path(extract_tmp)

            with zipfile.ZipFile(temp_zip, "r") as zip_ref:
                for entry in zip_ref.infolist():
                    entry_path = Path(entry.filename)
                    if entry_path.is_absolute() or ".." in entry_path.parts:
                        raise PluginInstallError(
                            f"Plugin archive for '{plugin_name}' contains unsafe file paths",
                            status_code=422,
                        )
                zip_ref.extractall(extract_root)

            plugin_root = _select_plugin_root(extract_root, plugin_name)

            plugin_dir.mkdir(parents=True, exist_ok=False)
            for item in plugin_root.iterdir():
                destination = plugin_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, destination)
                else:
                    shutil.copy2(item, destination)
    except zipfile.BadZipFile as exc:
        raise PluginInstallError(
            f"Plugin archive for '{plugin_name}' is not a valid ZIP file",
            status_code=422,
        ) from exc


def _install_plugin_from_zip(zip_url: str, plugin_name: str) -> tuple[bool, str, int]:
    """
    Download and extract a plugin from a ZIP URL (blocking I/O).
    
    Returns: (success: bool, message: str, status_code: int)
    """
    plugin_dir = None
    temp_zip = None
    try:
        plugins_dir = Path("plugins")
        plugins_dir.mkdir(parents=True, exist_ok=True)
        
        plugin_dir = plugins_dir / plugin_name
        
        # Check if already installed
        if plugin_dir.exists():
            return False, f"Plugin '{plugin_name}' is already installed", 409
        
        # Create temp file and download archive
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            temp_zip = Path(tmp.name)
        _download_plugin_zip(zip_url, temp_zip, plugin_name)

        # Extract and normalize directory layout
        _extract_plugin_payload(temp_zip, plugin_dir, plugin_name)
        
        return True, f"Plugin '{plugin_name}' installed successfully", 200

    except PluginInstallError as e:
        # Cleanup on known install errors
        if plugin_dir and plugin_dir.exists():
            shutil.rmtree(plugin_dir, ignore_errors=True)
        return False, str(e), e.status_code
    
    except Exception as e:
        # Cleanup on error
        if plugin_dir and plugin_dir.exists():
            shutil.rmtree(plugin_dir, ignore_errors=True)
        return False, f"Failed to install plugin: {str(e)}", 500
    
    finally:
        # Cleanup temp file
        if temp_zip and temp_zip.exists():
            try:
                temp_zip.unlink()
            except OSError:
                pass


def _create_plugin_zip(plugin_dir: Path, zip_path: Path):
    """Create a ZIP archive of a plugin directory."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in plugin_dir.rglob('*'):
            if file_path.is_file() and not file_path.name.endswith('.pyc'):
                arcname = file_path.relative_to(plugin_dir.parent)
                zip_file.write(file_path, arcname)


def _extract_plugin_name_from_zip(zip_path: Path) -> str:
    """Extract plugin name from manifest.json inside ZIP."""
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        # Look for manifest.json
        for name in zip_file.namelist():
            if name.endswith('manifest.json'):
                with zip_file.open(name) as manifest_file:
                    manifest_data = json.load(manifest_file)
                    plugin_name = manifest_data.get('name', '').strip()
                    if plugin_name:
                        return plugin_name
        raise ValueError("No valid manifest.json found in ZIP")


@router.get("", response_model=PluginListResponse)
@router.get("/list", response_model=PluginListResponse)
async def get_plugins_list(user: dict = Depends(get_current_user)):
    """Get list of all available plugins with status."""
    plugins = await _get_merged_plugins()
    return PluginListResponse(plugins=plugins, total=len(plugins))


@router.get("/catalog", response_model=CatalogListResponse)
async def get_plugins_catalog(user: dict = Depends(get_current_user)):
    """Get catalog of available plugins for installation."""
    catalog = await _get_catalog_with_install_status()
    return CatalogListResponse(plugins=catalog, total=len(catalog))


@router.get("/overview", response_model=PluginsOverviewResponse)
async def get_plugins_overview(user: dict = Depends(get_current_user)):
    """Get installed plugins and catalog in one request for faster page load."""
    plugins = await _get_merged_plugins()
    installed_names = {plugin["name"] for plugin in plugins}

    catalog: list[dict[str, Any]] = []
    for plugin in _load_catalog():
        catalog.append(
            {
                **plugin,
                "installed": plugin.get("name") in installed_names,
            }
        )

    catalog = sorted(catalog, key=lambda item: item["name"])

    return PluginsOverviewResponse(
        plugins=[PluginInfo(**plugin) for plugin in plugins],
        plugins_total=len(plugins),
        catalog=[CatalogPlugin(**plugin) for plugin in catalog],
        catalog_total=len(catalog),
    )


@router.post("/upload")
async def upload_plugin(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload and install a plugin from a ZIP file."""
    
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a .zip file")
    
    # Save uploaded file to temp location
    temp_zip = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            temp_zip = Path(tmp.name)
            content = await file.read()
            tmp.write(content)
        
        # Extract plugin name from ZIP
        try:
            plugin_name = await asyncio.to_thread(_extract_plugin_name_from_zip, temp_zip)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Invalid plugin ZIP: {str(e)}")
        
        # Install plugin using existing logic
        def _install():
            return _install_plugin_from_zip(str(temp_zip), plugin_name)
        
        success, message, status_code = await asyncio.to_thread(_install)
        
        if not success:
            raise HTTPException(status_code=status_code, detail=message)
        
        # Refresh discovery + persist manifests in one pass
        await _sync_discovered_manifests(force=True)
        
        return {
            "status": "ok",
            "message": message,
            "plugin_name": plugin_name,
            "installed": True
        }
    
    finally:
        # Cleanup temp file
        if temp_zip and temp_zip.exists():
            temp_zip.unlink(missing_ok=True)


@router.post("/install/{plugin_name}")
async def install_plugin(plugin_name: str, user: dict = Depends(get_current_user)):
    """Install a plugin from the catalog."""
    # Get catalog
    catalog = _load_catalog()
    catalog_item = next((p for p in catalog if p["name"] == plugin_name), None)
    
    if not catalog_item:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found in catalog")
    
    # Install plugin in thread pool to avoid blocking
    success, message, status_code = await asyncio.to_thread(
        _install_plugin_from_zip,
        catalog_item["download_url"],
        plugin_name
    )
    
    if not success:
        raise HTTPException(status_code=status_code, detail=message)
    
    # Refresh discovery + persist manifests in one pass
    await _sync_discovered_manifests(force=True)
    
    return {
        "status": "ok",
        "message": message,
        "plugin_name": plugin_name,
        "installed": True
    }


@router.get("/info/{plugin_name}", response_model=PluginInfo)
async def get_plugin_info(plugin_name: str, user: dict = Depends(get_current_user)):
    """Get information about a specific plugin."""
    info = await _find_plugin_or_404(plugin_name)
    return PluginInfo(**info)


@router.post("/enable/{plugin_name}")
async def enable_plugin(plugin_name: str, user: dict = Depends(get_current_user)):
    """Enable and load a plugin at runtime."""
    await _sync_discovered_manifests(force=True)

    manifest = plugin_loader.get_manifest(plugin_name)
    if not manifest:
        raise HTTPException(status_code=404, detail="Plugin not found")

    # Save manifest metadata first
    await db.save_plugin_manifest(
        manifest.name,
        manifest.version,
        manifest.author,
        manifest.description,
    )

    # Mark as enabled in database BEFORE loading the cog
    # This ensures DB state is committed and can be retried if loading fails
    await db.enable_plugin(manifest.name)

    # Try to load the cog into the bot if it's running
    message = f"Plugin '{manifest.name}' enabled"
    if plugin_loader.is_bot_running():
        success, load_msg = await asyncio.to_thread(
            plugin_loader.load_plugin_cog_threadsafe,
            manifest.name,
        )
        
        if success:
            # Check if DISCORD_GUILD_ID is set for instant updates
            import config
            if config.DISCORD_GUILD_ID:
                message = f"✅ {load_msg}! Commands synced instantly - reload Discord to see them."
            else:
                message = (
                    f"✅ {load_msg}! Commands were mirrored to connected guilds for instant updates; "
                    "global propagation to other guilds may still take up to 1 hour."
                )
        else:
            # Bot running but load failed - still enabled, will retry on next startup
            print(f"⚠️ Warning: Plugin '{manifest.name}' enabled but failed to load: {load_msg}")
            # Don't override the message - show the load failure reason
            message = load_msg
    else:
        # Bot not running - plugin is enabled and will load on next startup
        print(f"ℹ️  Bot not running; plugin '{manifest.name}' enabled and will load on next startup")
        message = f"Plugin '{manifest.name}' enabled (will load on next bot startup)"

    info = await _find_plugin_or_404(manifest.name)

    return {
        "status": "ok",
        "message": message,
        "plugin_name": manifest.name,
        "loaded": info["loaded"],
        "enabled": info["enabled"],
    }
@router.post("/disable/{plugin_name}")
async def disable_plugin(plugin_name: str, user: dict = Depends(get_current_user)):
    """Disable and unload a plugin at runtime."""
    await _sync_discovered_manifests(force=True)

    manifest = plugin_loader.get_manifest(plugin_name)
    db_state = await db.get_plugin_status(plugin_name)
    resolved_name = manifest.name if manifest else (db_state["name"] if db_state else None)
    if not resolved_name:
        raise HTTPException(status_code=404, detail="Plugin not found")

    # Mark as disabled in database FIRST
    # This ensures DB state is committed before attempting to unload
    await db.disable_plugin(resolved_name)

    # Now unload the cog from the bot if it's loaded
    message = f"Plugin '{resolved_name}' disabled"
    if resolved_name in plugin_loader.loaded_cogs:
        if not plugin_loader.is_bot_running():
            # DB marked as disabled, but cog still loaded in memory
            print(f"⚠️ Warning: Bot not running; plugin '{resolved_name}' marked disabled but still loaded in memory")
            message = f"Plugin '{resolved_name}' disabled in database, but cog still loaded (bot not running)"
        else:
            success, unload_msg = await asyncio.to_thread(
                plugin_loader.unload_plugin_cog_threadsafe,
                resolved_name,
            )
            if not success and "not loaded" not in unload_msg.lower():
                # DB is already disabled, log the unload issue but don't fail
                print(f"⚠️ Warning: Failed to unload plugin '{resolved_name}': {unload_msg}")
                message = unload_msg
            else:
                # Check if DISCORD_GUILD_ID is set for instant updates
                import config
                if config.DISCORD_GUILD_ID:
                    message = f"✅ {unload_msg}! Commands removed instantly - reload Discord to see changes."
                else:
                    message = (
                        f"✅ {unload_msg}! Command removals were mirrored to connected guilds; "
                        "global propagation to other guilds may still take up to 1 hour."
                    )

    info = await _find_plugin_or_404(resolved_name)

    return {
        "status": "ok",
        "message": message,
        "plugin_name": resolved_name,
        "loaded": info["loaded"],
        "enabled": info["enabled"],
    }

@router.delete("/uninstall/{plugin_name}")
async def uninstall_plugin(plugin_name: str, user: dict = Depends(get_current_user)):
    """Uninstall a plugin completely (disable, unload, and remove files)."""
    await _sync_discovered_manifests(force=True)

    # Check if plugin exists
    manifest = plugin_loader.get_manifest(plugin_name)
    db_state = await db.get_plugin_status(plugin_name)
    resolved_name = manifest.name if manifest else (db_state["name"] if db_state else None)
    
    if not resolved_name:
        raise HTTPException(status_code=404, detail="Plugin not found")

    # Unload if loaded
    if resolved_name in plugin_loader.loaded_cogs:
        if not plugin_loader.is_bot_running():
            raise HTTPException(status_code=409, detail="Bot is not running; cannot unload plugin")
        
        await asyncio.to_thread(
            plugin_loader.unload_plugin_cog_threadsafe,
            resolved_name,
        )

    # Remove plugin directory
    plugin_dir = Path("plugins") / resolved_name
    if plugin_dir.exists():
        await asyncio.to_thread(shutil.rmtree, plugin_dir, ignore_errors=True)

    # Remove from database
    await db.delete_plugin(resolved_name)

    # Rediscover plugins and refresh DB metadata cache
    await _sync_discovered_manifests(force=True)

    return {
        "status": "ok",
        "message": f"Plugin '{resolved_name}' uninstalled successfully",
        "plugin_name": resolved_name,
        "uninstalled": True
    }


@router.get("/download/{plugin_name}")
async def download_plugin(plugin_name: str, user: dict = Depends(get_current_user)):
    """Download a plugin as a ZIP file."""
    from fastapi.responses import FileResponse
    
    plugin_dir = Path("plugins") / plugin_name
    if not plugin_dir.exists():
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
    
    # Create ZIP in memory
    downloads_dir = Path("plugins_downloads")
    downloads_dir.mkdir(parents=True, exist_ok=True)
    zip_path = downloads_dir / f"{plugin_name}.zip"
    
    try:
        await asyncio.to_thread(_create_plugin_zip, plugin_dir, zip_path)
        return FileResponse(
            path=str(zip_path),
            filename=f"{plugin_name}.zip",
            media_type="application/zip"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ZIP: {str(e)}")


@router.get("/status")
async def get_plugins_status(user: dict = Depends(get_current_user)):
    """Get status map of plugins plus manifest discovery errors."""
    plugins = await _get_merged_plugins()
    status: Dict[str, Any] = {
        plugin["name"]: {
            "db_enabled": plugin["enabled"],
            "actually_loaded": plugin["loaded"],
            "version": plugin["version"],
            "author": plugin["author"],
            "description": plugin["description"],
        }
        for plugin in plugins
    }
    return {
        "status": status,
        "discovery_errors": plugin_loader.discovery_errors,
    }
