import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
from utils import safe_defer

# yt-dlp options
YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "source_address": "0.0.0.0",
    "default_search": "ytsearch",
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "no_color": True,
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

    @staticmethod
    def _is_url(value: str) -> bool:
        text = (value or "").strip().lower()
        return text.startswith("http://") or text.startswith("https://")

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    async def get_youtube_url(self, search: str):
        query = (search or "").strip().strip("<>")
        if not query:
            raise ValueError("Empty query")

        # Use explicit ytsearch for plain text; keep direct URLs unchanged.
        lookup = query if self._is_url(query) else f"ytsearch1:{query}"

        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(
            None,
            lambda: ytdl.extract_info(lookup, download=False)
        )

        if not data:
            raise LookupError("No results returned")

        if "entries" in data:
            entries = [entry for entry in (data.get("entries") or []) if entry]
            if not entries:
                raise LookupError("No matching videos found")
            data = entries[0]

        stream_url = data.get("url")
        if not stream_url and data.get("webpage_url"):
            # Fallback: resolve to a playable stream URL from the page URL.
            resolved = await loop.run_in_executor(
                None,
                lambda: ytdl.extract_info(data["webpage_url"], download=False),
            )
            if resolved:
                data = resolved
                stream_url = data.get("url")

        if not stream_url:
            raise LookupError("No playable audio stream found")

        return {
            "url": stream_url,
            "title": data.get("title", "Unknown title"),
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

    @app_commands.command(name="play", description="Play music from YouTube")
    @app_commands.describe(query="YouTube link or search query")
    async def play(self, interaction: discord.Interaction, query: str):

        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ Please join a voice channel first.", ephemeral=True
            )
            return

        await safe_defer(interaction)

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
        except Exception as e:
            await interaction.followup.send(
                "❌ I couldn't find that track. Please try a different YouTube link or search query."
            )
            print(f"Music lookup failed for query '{query}': {e}")
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

    @app_commands.command(name="stop", description="Stop music and clear the queue")
    async def stop(self, interaction: discord.Interaction):

        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_connected():
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        music_queue = self.get_queue(guild_id)
        music_queue.queue.clear()
        music_queue.is_playing = False
        music_queue.current = None

        await voice_client.disconnect()
        await interaction.response.send_message("⏹️ Music stopped and queue cleared.")

    @app_commands.command(name="queue", description="View the current music queue")
    async def queue(self, interaction: discord.Interaction):

        guild_id = interaction.guild.id
        music_queue = self.get_queue(guild_id)

        if not music_queue.current and len(music_queue.queue) == 0:
            await interaction.response.send_message("❌ The queue is empty.", ephemeral=True)
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
                queue_list += f"\n*...and {len(music_queue.queue) - 10} more track(s)*"
            embed.add_field(name="📋 Up Next", value=queue_list, inline=False)

        embed.set_footer(text=f"Total queued: {len(music_queue.queue)} track(s)")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pause", description="Pause the current music")
    async def pause(self, interaction: discord.Interaction):

        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_playing():
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)
            return

        voice_client.pause()
        self.get_queue(interaction.guild.id).is_paused = True
        await interaction.response.send_message("⏸️ Music paused.")

    @app_commands.command(name="resume", description="Resume paused music")
    async def resume(self, interaction: discord.Interaction):

        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_paused():
            await interaction.response.send_message("❌ There is no paused music to resume.", ephemeral=True)
            return

        voice_client.resume()
        self.get_queue(interaction.guild.id).is_paused = False
        await interaction.response.send_message("▶️ Music resumed.")


# REQUIRED — para ma-load ng bot
async def setup(bot):
    await bot.add_cog(Music(bot))
