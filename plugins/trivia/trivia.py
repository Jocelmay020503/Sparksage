import discord
from discord.ext import commands
from discord import app_commands, ui
import random


# Trivia questions database
QUESTIONS = {
    "easy": [
        {
            "question": "What is the capital of France?",
            "options": ["London", "Paris", "Berlin", "Madrid"],
            "correct": 1,
        },
        {
            "question": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "correct": 1,
        },
        {
            "question": "What color is the sky?",
            "options": ["Green", "Blue", "Red", "Yellow"],
            "correct": 1,
        },
    ],
    "medium": [
        {
            "question": "What is the largest planet in our solar system?",
            "options": ["Saturn", "Jupiter", "Neptune", "Uranus"],
            "correct": 1,
        },
        {
            "question": "Who wrote Romeo and Juliet?",
            "options": ["Mark Twain", "William Shakespeare", "Jane Austen", "Charles Dickens"],
            "correct": 1,
        },
        {
            "question": "What is the chemical symbol for Gold?",
            "options": ["Go", "Au", "Gd", "Ag"],
            "correct": 1,
        },
    ],
    "hard": [
        {
            "question": "What year did the Titanic sink?",
            "options": ["1912", "1905", "1920", "1898"],
            "correct": 0,
        },
        {
            "question": "Who is the author of 'One Hundred Years of Solitude'?",
            "options": ["Jorge Luis Borges", "Gabriel García Márquez", "Pablo Neruda", "Octavio Paz"],
            "correct": 1,
        },
    ],
}

# Store user scores
user_scores = {}


class AnswerButtons(ui.View):
    """Button view for trivia answers"""
    
    def __init__(self, correct_index: int, question_data: dict, interaction: discord.Interaction):
        super().__init__()
        self.correct_index = correct_index
        self.question_data = question_data
        self.interaction = interaction
        self.answered = False
        
        # Create buttons for each option
        labels = ["A", "B", "C", "D"]
        for idx, option in enumerate(question_data["options"]):
            button = ui.Button(label=labels[idx], style=discord.ButtonStyle.primary)
            button.callback = lambda interaction, i=idx: self.answer_callback(interaction, i)
            self.add_item(button)
    
    async def answer_callback(self, interaction: discord.Interaction, selected: int):
        if self.answered:
            await interaction.response.send_message("❌ Poll already closed!", ephemeral=True)
            return
        
        self.answered = True
        is_correct = selected == self.correct_index
        user_id = interaction.user.id
        
        # Update score
        if user_id not in user_scores:
            user_scores[user_id] = {"correct": 0, "total": 0}
        
        user_scores[user_id]["total"] += 1
        if is_correct:
            user_scores[user_id]["correct"] += 1
        
        # Create result embed
        labels = ["A", "B", "C", "D"]
        embed = discord.Embed(
            title="📊 Answer Result",
            color=discord.Color.green() if is_correct else discord.Color.red(),
        )
        
        if is_correct:
            embed.description = f"✅ **Correct!** The answer was **{labels[self.correct_index]}) {self.question_data['options'][self.correct_index]}**"
        else:
            embed.description = f"❌ **Wrong!** You chose **{labels[selected]}) {self.question_data['options'][selected]}**\n\nThe correct answer is **{labels[self.correct_index]}) {self.question_data['options'][self.correct_index]}**"
        
        stats = user_scores[user_id]
        win_rate = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        embed.add_field(
            name="📈 Your Stats",
            value=f"Correct: {stats['correct']}/{stats['total']}\nWin Rate: {win_rate:.1f}%",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        
        await self.interaction.edit_original_response(view=self)


class Trivia(commands.Cog):
    """Interactive trivia game for Discord servers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="trivia", description="Start an interactive trivia game")
    @app_commands.describe(difficulty="Difficulty level: easy, medium, or hard")
    async def trivia(self, interaction: discord.Interaction, difficulty: str = "medium"):
        difficulties = {
            "easy": "🟢 Easy",
            "medium": "🟡 Medium",
            "hard": "🔴 Hard",
        }

        diff_lower = difficulty.lower()
        if diff_lower not in difficulties:
            await interaction.response.send_message(
                "❌ Invalid difficulty. Choose: easy, medium, or hard",
                ephemeral=True,
            )
            return

        # Pick random question
        questions = QUESTIONS.get(diff_lower, QUESTIONS["medium"])
        if not questions:
            await interaction.response.send_message(
                "❌ No questions available for this difficulty",
                ephemeral=True,
            )
            return
        
        question_data = random.choice(questions)
        correct_index = question_data["correct"]
        
        # Create embed
        embed = discord.Embed(
            title="🎯 Trivia Question",
            description=f"**Difficulty:** {difficulties[diff_lower]}\n\n**{question_data['question']}**",
            color=discord.Color.blue(),
        )
        
        labels = ["A", "B", "C", "D"]
        for idx, option in enumerate(question_data["options"]):
            embed.add_field(name=f"{labels[idx]})", value=option, inline=False)
        
        embed.set_footer(text="Click a button to answer!")
        
        # Create view with buttons
        view = AnswerButtons(correct_index, question_data, interaction)
        
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="trivia_score", description="Check your trivia score")
    async def trivia_score(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        stats = user_scores.get(user_id)
        
        if not stats or stats["total"] == 0:
            embed = discord.Embed(
                title="📊 Your Trivia Score",
                description="You haven't answered any trivia questions yet!\n\nUse `/trivia` to start playing!",
                color=discord.Color.orange(),
            )
        else:
            win_rate = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
            embed = discord.Embed(
                title="📊 Your Trivia Score",
                description=f"**Correct Answers:** {stats['correct']}\n**Total Questions:** {stats['total']}\n**Win Rate:** {win_rate:.1f}%",
                color=discord.Color.green(),
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Trivia(bot))


