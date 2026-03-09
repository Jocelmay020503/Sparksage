"""Test if channel prompt is being retrieved and used correctly."""

import asyncio
import sys
sys.path.insert(0, "/root")

import db as database


async def test_channel_prompt():
    """Test retrieving a channel prompt."""
    # Initialize database
    await database.init_db()
    
    # The channel ID from the database
    channel_id = "1480228373409042535"
    
    # Get the channel prompt
    prompt = await database.get_channel_prompt(channel_id)
    
    print(f"Channel ID: {channel_id}")
    print(f"Retrieved Prompt: {prompt}")
    print(f"Prompt is None: {prompt is None}")
    
    if prompt:
        print(f"Prompt length: {len(prompt)}")
        print(f"First 100 chars: {prompt[:100]}")
    
    # Get all prompts
    all_prompts = await database.get_all_channel_prompts()
    print(f"\nAll prompts in database: {all_prompts}")


if __name__ == "__main__":
    asyncio.run(test_channel_prompt())
