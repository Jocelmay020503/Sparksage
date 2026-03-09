"""Direct test of channel prompt retrieval logic."""

import asyncio
import sys
sys.path.insert(0, ".")

import db as database
import config


async def test_prompt_logic():
    """Test the exact logic used in ask_ai."""
    
    await database.init_db()
    
    channel_id = "1480228373409042535"
    
    # Simulate ask_ai logic
    print("=== Testing Channel Prompt Logic ===\n")
    
    print(f"Global System Prompt: '{config.SYSTEM_PROMPT}'\n")
    
    # This is exactly what ask_ai does
    channel_prompt = await database.get_channel_prompt(channel_id)
    system_prompt = channel_prompt if channel_prompt else config.SYSTEM_PROMPT
    
    print(f"Channel ID: {channel_id}")
    print(f"Retrieved channel_prompt: '{channel_prompt}'")
    print(f"Final system_prompt used: '{system_prompt}'")
    print(f"\nSystem prompt is using CUSTOM prompt: {system_prompt != config.SYSTEM_PROMPT}")


if __name__ == "__main__":
    asyncio.run(test_prompt_logic())
