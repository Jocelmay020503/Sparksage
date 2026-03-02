from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_current_user
import db
from utils.plugin_loader import get_plugin_loader

router = APIRouter()


class PluginActionRequest(BaseModel):
    name: str


@router.get("")
async def get_plugins(current_user: str = Depends(get_current_user)):
    """List discovered plugins with install and enable state."""
    loader = get_plugin_loader()
    discovered = loader.discover_plugins()
    installed = await db.list_plugins()
    installed_by_name = {plugin["name"]: plugin for plugin in installed}

    result = []
    for name in discovered:
        info = loader.get_plugin_info(name)
        if not info:
            continue

        installed_plugin = installed_by_name.get(name)
        result.append(
            {
                "name": info.get("name", name),
                "version": info.get("version", "1.0.0"),
                "author": info.get("author", "Unknown"),
                "description": info.get("description", ""),
                "installed": installed_plugin is not None,
                "enabled": bool(installed_plugin and installed_plugin.get("enabled")),
            }
        )

    return {"plugins": result}


@router.post("/install")
async def install_plugin(payload: PluginActionRequest, current_user: str = Depends(get_current_user)):
    """Install plugin metadata from manifest."""
    loader = get_plugin_loader()
    info = loader.get_plugin_info(payload.name)
    if not info:
        raise HTTPException(status_code=404, detail="Plugin not found")

    await db.upsert_plugin(
        payload.name,
        info.get("version", "1.0.0"),
        info.get("author", "Unknown"),
        info.get("description", ""),
        enabled=False,
    )
    return {"status": "installed", "name": payload.name}


@router.post("/enable")
async def enable_plugin(payload: PluginActionRequest, current_user: str = Depends(get_current_user)):
    """Enable an installed plugin."""
    plugin = await db.get_plugin(payload.name)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin is not installed")

    updated = await db.set_plugin_enabled(payload.name, True)
    if not updated:
        raise HTTPException(status_code=404, detail="Plugin is not installed")

    return {
        "status": "enabled",
        "name": payload.name,
        "message": "Plugin enabled. Restart bot to load this plugin.",
    }


@router.post("/disable")
async def disable_plugin(payload: PluginActionRequest, current_user: str = Depends(get_current_user)):
    """Disable an installed plugin."""
    updated = await db.set_plugin_enabled(payload.name, False)
    if not updated:
        raise HTTPException(status_code=404, detail="Plugin is not installed")

    return {
        "status": "disabled",
        "name": payload.name,
        "message": "Plugin disabled. Restart bot to unload this plugin.",
    }


@router.delete("/{name}")
async def uninstall_plugin(name: str, current_user: str = Depends(get_current_user)):
    """Uninstall plugin metadata."""
    deleted = await db.delete_plugin(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Plugin is not installed")

    return {
        "status": "uninstalled",
        "name": name,
        "message": "Plugin uninstalled. Restart bot if it is currently loaded.",
    }
