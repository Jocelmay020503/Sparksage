# Plugins Directory

This directory contains community-contributed plugins for SparkSage.

## Plugin Structure

Each plugin should be in its own directory with the following structure:

```
plugins/
    my_plugin/
        __init__.py
        cog.py
        plugin.json
        README.md (optional)
```

## Plugin Manifest (plugin.json)

Every plugin must have a `plugin.json` manifest file:

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "A brief description of your plugin",
  "cog_class": "MyPluginCog",
  "discord_py_version": "2.3.0",
  "dependencies": [],
  "commands": ["command1", "command2"],
  "permissions": ["Send Messages", "Read Messages"]
}
```

## Cog File (cog.py)

Your cog should inherit from `discord.ext.commands.Cog`:

```python
import discord
from discord.ext import commands

class MyPluginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @discord.app_commands.command(name="mycommand", description="My command")
    async def my_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello from my plugin!")

async def setup(bot):
    await bot.add_cog(MyPluginCog(bot))
```

## Installing Plugins

1. Place your plugin directory in `plugins/`
2. Use `/plugin install <plugin_name>` in Discord
3. Or use the dashboard to install plugins

## Security Note

Only install plugins from trusted sources. Plugins have access to the bot's functionality.
