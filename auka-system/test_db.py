import asyncio
from scripts.database.supabase_client import db

async def main():
    p = await db.get_prospectos(limit=100)
    print(f"Found {len(p)} prospectos in DB")

if __name__ == "__main__":
    asyncio.run(main())
