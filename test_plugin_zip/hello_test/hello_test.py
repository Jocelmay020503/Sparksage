import discord
from discord.ext import commands
from discord import app_commands

class HelloTestCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    hello = app_commands.Group(name='hello_test', description='Hello test commands')

    @hello.command(name='world', description='Say hello world')
    async def hello_world(self, interaction: discord.Interaction):
        await interaction.response.send_message('Hello from test plugin!', ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelloTestCog(bot))
