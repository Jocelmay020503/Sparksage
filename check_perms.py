import asyncio
import db

async def main():
    await db.init_db()
    perms = await db.list_permissions()
    
    if not perms:
        print("❌ No permissions found in database!")
    else:
        print(f"✅ Found {len(perms)} permission(s):\n")
        for p in perms:
            print(f"  Command: {p['command_name']:15} | Guild: {p['guild_id']} | Role: {p['role_id']}")

asyncio.run(main())
