import discord
from discord.ext import commands
from discord import app_commands

class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_polls = {}  # Store active polls

    @app_commands.command(name="poll", description="Create a poll! Users can vote using reactions.")
    @app_commands.describe(
        question="The poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)",
        option5="Fifth option (optional)"
    )
    async def poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None,
        option5: str = None,
    ):
        """Create a poll with up to 5 options"""
        # Build options list
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)
        if option5:
            options.append(option5)

        # Emojis para sa choices
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        # Gumawa ng embed
        embed = discord.Embed(
            title=f"📊 {question}",
            color=discord.Color.blue(),
            description="React to vote!"
        )

        # Idagdag ang bawat option
        for i, option in enumerate(options):
            embed.add_field(
                name=f"{emojis[i]} {option}",
                value="0 votes",
                inline=False
            )

        embed.set_footer(text=f"Poll by {interaction.user.display_name}")

        # Respond with the poll
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        # Mag-add ng reactions
        for i in range(len(options)):
            await message.add_reaction(emojis[i])

        # I-save ang active poll
        self.active_polls[message.id] = {
            "question": question,
            "options": options,
            "channel": interaction.channel.id,
            "author": interaction.user.id
        }

    @app_commands.command(name="endpoll", description="End a poll and show results")
    @app_commands.describe(message_id="The message ID of the poll to end")
    async def endpoll(self, interaction: discord.Interaction, message_id: str):
        """End a poll and show results"""
        try:
            poll_message_id = int(message_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
            return

        # Kunin ang poll message
        try:
            message = await interaction.channel.fetch_message(poll_message_id)
        except:
            await interaction.response.send_message("❌ Could not find that poll message.", ephemeral=True)
            return

        # Kunin ang results
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        results = {}

        for reaction in message.reactions:
            if str(reaction.emoji) in emojis:
                results[str(reaction.emoji)] = reaction.count - 1  # Minus 1 (bot reaction)

        # Gumawa ng results embed
        embed = discord.Embed(
            title="📊 Poll Results!",
            color=discord.Color.green()
        )

        poll_data = self.active_polls.get(poll_message_id)
        if poll_data:
            embed.description = f"**{poll_data['question']}**\n"
            for i, option in enumerate(poll_data['options']):
                votes = results.get(emojis[i], 0)
                embed.add_field(
                    name=f"{emojis[i]} {option}",
                    value=f"**{votes}** votes",
                    inline=False
                )

        await interaction.response.send_message(embed=embed)

# REQUIRED — para ma-load ng bot
async def setup(bot):
    await bot.add_cog(Poll(bot))

