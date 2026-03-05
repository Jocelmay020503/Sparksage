"""
Code Review Cog - Code Analysis and Feedback

Contains commands for analyzing code and providing reviews:
- /review: Analyze code for bugs, style issues, and improvements
"""

from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import config
from utils import ask_ai, check_command_permission

# System prompt for code review
CODE_REVIEW_SYSTEM_PROMPT = """You are a senior code reviewer with expertise across multiple programming languages. 
Your task is to analyze code for:
1. **Bugs and potential errors** — logical flaws, off-by-one errors, null pointer risks, etc.
2. **Style and best practices** — naming conventions, code organization, adherence to language standards
3. **Performance improvements** — inefficient algorithms, unnecessary operations, optimization opportunities
4. **Security concerns** — input validation, injection risks, hardcoded secrets, unsafe operations

Respond with clear, actionable feedback using markdown formatting with syntax-highlighted code blocks. 
Be constructive and explain the "why" behind each suggestion.
Format code examples with appropriate language markers (```python, ```javascript, etc.)"""


async def detect_language(code: str) -> str:
    """Attempt to detect programming language from code patterns."""
    # Simple heuristic-based detection
    code_lower = code.lower()

    # Check for common patterns
    if any(keyword in code_lower for keyword in ["def ", "import ", "class ", "async def"]):
        return "python"
    if any(keyword in code_lower for keyword in ["function ", "const ", "let ", "var ", "=>", ".then("]):
        return "javascript"
    if any(keyword in code_lower for keyword in ["public ", "private ", "class ", "void ", ".java"]):
        return "java"
    if any(keyword in code_lower for keyword in ["fn ", "let ", "mut ", "impl "]):
        return "rust"
    if any(keyword in code_lower for keyword in ["func ", "struct ", "protocol "]):
        return "swift"
    if any(keyword in code_lower for keyword in ["#include", "int main", "printf"]):
        return "c"

    return "plaintext"


class CodeReview(commands.Cog):
    """Commands for code review and analysis."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="review", description="Review code for bugs, style, and improvements")
    @app_commands.describe(
        code="The code snippet to review (required)",
        language="Programming language hint (optional - will auto-detect if omitted)",
    )
    async def review(
        self, interaction: discord.Interaction, code: str, language: str | None = None
    ):
        """Review a code snippet and provide detailed feedback."""
        # Check permissions
        if not await check_command_permission(interaction, "review"):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return
        
        await interaction.response.defer()

        # Determine language
        if not language:
            detected = await detect_language(code)
            language = detected
        else:
            language = language.lower()

        # Prepare the review prompt
        review_request = f"""Please review the following {language} code:

```{language}
{code}
```

Provide detailed feedback on bugs, style, performance, and security."""

        # Get AI review response using the code review system prompt
        try:
            response, provider_name = await ask_ai(
                interaction.channel_id, 
                interaction.user.display_name, 
                review_request,
                custom_system_prompt=CODE_REVIEW_SYSTEM_PROMPT,
                interaction_type="code_review",
                guild_id=str(interaction.guild_id) if interaction.guild_id else None,
                user_id=str(interaction.user.id),
            )

            provider_label = config.PROVIDERS.get(provider_name, {}).get("name", provider_name)
            lang_label = language if language != "plaintext" else "text"

            # Format response with header and provider info
            header = f"**Code Review** — {lang_label.title()}"
            footer = f"\n-# Reviewed by {provider_label} | Language: {lang_label.title()}"

            full_response = f"{header}\n\n{response}{footer}"

            # Send response (split if necessary)
            for i in range(0, len(full_response), 1900):
                chunk = full_response[i : i + 1900]
                await interaction.followup.send(chunk)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Code review failed: {str(e)}\n\nPlease try again or check your code for issues."
            )


async def setup(bot: commands.Bot):
    """Load the CodeReview cog."""
    await bot.add_cog(CodeReview(bot))
