"""
Digest Cog - Daily Activity Summarization

Automatically summarizes daily activity and posts to a designated channel.
Configurable schedule and channel through config.
"""

from __future__ import annotations

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import asyncio

import config
import providers
import db as database


class Digest(commands.Cog):
    """Digest commands and automated daily summaries."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_digest_task.start()

    def cog_unload(self):
        """Stop the task when cog is unloaded."""
        self.daily_digest_task.cancel()

    @tasks.loop(hours=24)
    async def daily_digest_task(self):
        """Generate and post daily digest at the configured time."""
        # Check if digest is enabled
        if not config.DIGEST_ENABLED:
            return

        channel_id = config.DIGEST_CHANNEL_ID
        if not channel_id:
            print("⚠️ Digest enabled but no channel configured")
            return

        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                print(f"⚠️ Digest channel {channel_id} not found")
                return

            # Generate digest
            digest_content = await self._generate_digest(channel.guild)
            
            if digest_content:
                # Create embed for the digest
                embed = discord.Embed(
                    title="📊 Daily Activity Digest",
                    description=digest_content,
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_footer(text="SparkSage Daily Digest")
                
                await channel.send(embed=embed)
                print(f"✅ Daily digest posted to #{channel.name}")
            else:
                print("ℹ️ No significant activity to report in digest")
                
        except Exception as e:
            print(f"❌ Error generating daily digest: {e}")

    @daily_digest_task.before_loop
    async def before_daily_digest(self):
        """Wait until the configured time before starting the loop."""
        await self.bot.wait_until_ready()
        
        # Parse the target time from config
        target_time = config.DIGEST_TIME  # Format: "HH:MM" (e.g., "09:00")
        
        if not target_time or ":" not in target_time:
            print("⚠️ Invalid DIGEST_TIME format, using default midnight (00:00)")
            target_time = "00:00"
        
        try:
            hours, minutes = map(int, target_time.split(":"))
            now = datetime.now(timezone.utc)
            target = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            
            # If target time has passed today, schedule for tomorrow
            if target <= now:
                target += timedelta(days=1)
            
            wait_seconds = (target - now).total_seconds()
            print(f"⏰ Daily digest scheduled for {target_time} UTC (in {wait_seconds/3600:.1f} hours)")
            await asyncio.sleep(wait_seconds)
            
        except Exception as e:
            print(f"⚠️ Error parsing DIGEST_TIME: {e}, starting immediately")
            await asyncio.sleep(1)

    async def _generate_digest(self, guild: discord.Guild) -> str:
        """Generate a digest of the past 24 hours of activity.
        
        Args:
            guild: The Discord guild to generate digest for
            
        Returns:
            Formatted digest text or empty string if no activity
        """
        # Get all messages from the past 24 hours across all channels
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        
        channel_summaries = []
        total_messages = 0
        
        # Iterate through all text channels in the guild
        for channel in guild.text_channels:
            # Skip the digest channel itself
            if str(channel.id) == config.DIGEST_CHANNEL_ID:
                continue
            
            try:
                # Check if bot has permission to read the channel
                if not channel.permissions_for(guild.me).read_message_history:
                    continue
                
                messages = []
                async for msg in channel.history(
                    after=twenty_four_hours_ago,
                    limit=200,
                    oldest_first=False
                ):
                    # Skip bot messages
                    if msg.author.bot:
                        continue
                    messages.append(f"{msg.author.display_name}: {msg.content[:100]}")
                
                if messages:
                    channel_summaries.append({
                        "channel": channel.name,
                        "count": len(messages),
                        "messages": messages[:20]  # Limit to 20 messages per channel for summary
                    })
                    total_messages += len(messages)
                    
            except discord.Forbidden:
                # Skip channels we can't access
                continue
            except Exception as e:
                print(f"⚠️ Error reading channel #{channel.name}: {e}")
                continue
        
        if total_messages == 0:
            return ""
        
        # Sort channels by message count (most active first)
        channel_summaries.sort(key=lambda x: x["count"], reverse=True)
        
        # Build the digest prompt
        digest_prompt = f"""Analyze the following Discord server activity from the past 24 hours and create a concise daily digest.

Total messages: {total_messages}
Active channels: {len(channel_summaries)}

Channel Activity:
"""
        
        for summary in channel_summaries[:5]:  # Top 5 most active channels
            digest_prompt += f"\n#{summary['channel']} ({summary['count']} messages):\n"
            digest_prompt += "\n".join(summary['messages'][:10]) + "\n"
        
        digest_prompt += """

Provide a brief digest covering:
1. **Most Active Discussions** - Key topics and channels
2. **Important Highlights** - Notable decisions, questions, or announcements
3. **Overall Sentiment** - General mood of the community

Keep it concise (under 500 words) and formatted in markdown.
"""
        
        # Use AI to summarize
        try:
            system_prompt = "You are SparkSage, creating a daily digest for a Discord community. Be concise, informative, and highlight what matters."
            response, provider_name = providers.chat(
                [{"role": "user", "content": digest_prompt}],
                system_prompt
            )
            return response
            
        except Exception as e:
            print(f"❌ Error generating AI summary: {e}")
            # Fallback to basic summary
            basic_summary = f"**Activity Summary**\n\n"
            basic_summary += f"📊 {total_messages} messages across {len(channel_summaries)} channels\n\n"
            basic_summary += "**Most Active Channels:**\n"
            for summary in channel_summaries[:5]:
                basic_summary += f"• #{summary['channel']}: {summary['count']} messages\n"
            return basic_summary

    @commands.command(name="digest")
    @commands.has_permissions(administrator=True)
    async def manual_digest(self, ctx: commands.Context):
        """Manually trigger a digest generation (admin only)."""
        async with ctx.typing():
            digest_content = await self._generate_digest(ctx.guild)
            
            if digest_content:
                embed = discord.Embed(
                    title="📊 Manual Activity Digest",
                    description=digest_content,
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_footer(text="SparkSage Manual Digest")
                await ctx.send(embed=embed)
            else:
                await ctx.send("No significant activity to report in the past 24 hours.")


async def setup(bot: commands.Bot):
    """Load the Digest cog."""
    await bot.add_cog(Digest(bot))
