import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio

# yt-dlp options
YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


class MusicQueue:
    def __init__(self):
        self.queue = []
        self.current = None
        self.is_playing = False
        self.is_paused = False


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    async def get_youtube_url(self, search: str):
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: ytdl.extract_info(search, download=False)
        )
        if "entries" in data:
            data = data["entries"][0]
        return {
            "url": data["url"],
            "title": data["title"],
            "duration": data.get("duration", 0),
            "thumbnail": data.get("thumbnail", None),
        }

    async def play_next(self, guild_id, voice_client):
        music_queue = self.get_queue(guild_id)

        if len(music_queue.queue) == 0:
            music_queue.is_playing = False
            music_queue.current = None
            return

        song = music_queue.queue.pop(0)
        music_queue.current = song
        music_queue.is_playing = True

        source = discord.FFmpegPCMAudio(song["url"], **FFMPEG_OPTIONS)
        voice_client.play(
            source,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(guild_id, voice_client),
                self.bot.loop
            )
        )

    @app_commands.command(name="play", description="Mag-play ng music mula sa YouTube!")
    @app_commands.describe(query="YouTube link o search query")
    async def play(self, interaction: discord.Interaction, query: str):

        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ Sumali ka muna sa voice channel!", ephemeral=True
            )
            return

        await interaction.response.defer()

        voice_channel = interaction.user.voice.channel
        guild_id = interaction.guild.id
        music_queue = self.get_queue(guild_id)

        if interaction.guild.voice_client is None:
            voice_client = await voice_channel.connect()
        else:
            voice_client = interaction.guild.voice_client
            if voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)

        try:
            song = await self.get_youtube_url(query)
        except Exception:
            await interaction.followup.send("❌ Hindi mahanap ang kanta!")
            return

        music_queue.queue.append(song)

        embed = discord.Embed(
            title="🎵 Added to Queue!",
            description=f"**{song['title']}**",
            color=discord.Color.red()
        )
        if song["thumbnail"]:
            embed.set_thumbnail(url=song["thumbnail"])

        embed.add_field(
            name="Position",
            value=f"#{len(music_queue.queue)}" if music_queue.is_playing else "▶️ Now Playing!",
            inline=True
        )

        await interaction.followup.send(embed=embed)

        if not music_queue.is_playing:
            await self.play_next(guild_id, voice_client)

    @app_commands.command(name="stop", description="Itigil ang music at i-clear ang queue")
    async def stop(self, interaction: discord.Interaction):

        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_connected():
            await interaction.response.send_message("❌ Wala akong pinapatugtog!", ephemeral=True)
            return

        guild_id = interaction.guild.id
        music_queue = self.get_queue(guild_id)
        music_queue.queue.clear()
        music_queue.is_playing = False
        music_queue.current = None

        await voice_client.disconnect()
        await interaction.response.send_message("⏹️ Naitigil na ang music!")

    @app_commands.command(name="queue", description="Tingnan ang music queue")
    async def queue(self, interaction: discord.Interaction):

        guild_id = interaction.guild.id
        music_queue = self.get_queue(guild_id)

        if not music_queue.current and len(music_queue.queue) == 0:
            await interaction.response.send_message("❌ Walang laman ang queue!", ephemeral=True)
            return

        embed = discord.Embed(title="🎵 Music Queue", color=discord.Color.red())

        if music_queue.current:
            embed.add_field(
                name="▶️ Now Playing",
                value=f"**{music_queue.current['title']}**",
                inline=False
            )

        if music_queue.queue:
            queue_list = ""
            for i, song in enumerate(music_queue.queue[:10]):
                queue_list += f"`{i+1}.` {song['title']}\n"
            if len(music_queue.queue) > 10:
                queue_list += f"\n*...at {len(music_queue.queue) - 10} pang kanta*"
            embed.add_field(name="📋 Up Next", value=queue_list, inline=False)

        embed.set_footer(text=f"Total: {len(music_queue.queue)} kanta sa queue")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pause", description="I-pause ang music")
    async def pause(self, interaction: discord.Interaction):

        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_playing():
            await interaction.response.send_message("❌ Wala akong pinapatugtog!", ephemeral=True)
            return

        voice_client.pause()
        self.get_queue(interaction.guild.id).is_paused = True
        await interaction.response.send_message("⏸️ Na-pause ang music!")

    @app_commands.command(name="resume", description="I-resume ang naka-pause na music")
    async def resume(self, interaction: discord.Interaction):

        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_paused():
            await interaction.response.send_message("❌ Wala akong naka-pause na music!", ephemeral=True)
            return

        voice_client.resume()
        self.get_queue(interaction.guild.id).is_paused = False
        await interaction.response.send_message("▶️ Na-resume ang music!")


# REQUIRED — para ma-load ng bot
async def setup(bot):
    await bot.add_cog(Music(bot))
