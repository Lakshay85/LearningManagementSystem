"""
Migration script to add ImageKit columns to videos and documents tables.
Run this once after deploying the ImageKit integration.

Usage:
    python -m app.migrations.add_imagekit_columns
"""
import asyncio
import sys
from sqlalchemy import text
from app.database import engine

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


async def migrate():
    print("[Migration] Adding ImageKit columns to videos and documents tables...")
    
    async with engine.begin() as conn:
        # Add imagekitFileId and cdnUrl to videos table
        try:
            await conn.execute(text(
                "ALTER TABLE videos ADD COLUMN IF NOT EXISTS \"imagekitFileId\" VARCHAR NULL"
            ))
            print("[Migration] Added imagekitFileId to videos table")
        except Exception as e:
            print(f"[Migration] videos.imagekitFileId: {e}")

        try:
            await conn.execute(text(
                "ALTER TABLE videos ADD COLUMN IF NOT EXISTS \"cdnUrl\" VARCHAR NULL"
            ))
            print("[Migration] Added cdnUrl to videos table")
        except Exception as e:
            print(f"[Migration] videos.cdnUrl: {e}")

        # Add imagekitFileId and cdnUrl to documents table
        try:
            await conn.execute(text(
                "ALTER TABLE documents ADD COLUMN IF NOT EXISTS \"imagekitFileId\" VARCHAR NULL"
            ))
            print("[Migration] Added imagekitFileId to documents table")
        except Exception as e:
            print(f"[Migration] documents.imagekitFileId: {e}")

        try:
            await conn.execute(text(
                "ALTER TABLE documents ADD COLUMN IF NOT EXISTS \"cdnUrl\" VARCHAR NULL"
            ))
            print("[Migration] Added cdnUrl to documents table")
        except Exception as e:
            print(f"[Migration] documents.cdnUrl: {e}")

    print("[Migration] ImageKit columns migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
