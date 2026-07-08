import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def clean():
    engine = create_async_engine('postgresql+asyncpg://postgres:root@localhost:5432/lms')
    async with engine.begin() as conn:
        await conn.execute(text('TRUNCATE users CASCADE'))
    await engine.dispose()
    print("All users cleared successfully.")

asyncio.run(clean())
