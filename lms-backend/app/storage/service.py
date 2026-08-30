import os
import mimetypes
import shutil
from datetime import datetime
from typing import Optional, Union, BinaryIO
import aiofiles

from app.config import settings

class LocalStorageProvider:
    def __init__(self):
        self.base_path = settings.STORAGE_LOCAL_PATH
        self.base_url = settings.STORAGE_BASE_URL
        os.makedirs(self.base_path, exist_ok=True)
        print(f"[Storage] Local storage provider initialized at: {self.base_path}")

    def get_full_path(self, relative_path: str) -> str:
        return os.path.join(self.base_path, relative_path)

    async def upload(
        self, 
        file_data: Union[bytes, BinaryIO], 
        destination: str, 
        mime_type: Optional[str] = None
    ) -> dict:
        full_path = self.get_full_path(destination)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        async with aiofiles.open(full_path, 'wb') as f:
            if isinstance(file_data, bytes):
                await f.write(file_data)
            else:
                # If it's a file-like object or SpooledTemporaryFile
                # Read chunks and write
                file_data.seek(0)
                while chunk := file_data.read(1024 * 1024):
                    await f.write(chunk)

        size = os.path.getsize(full_path)
        guessed_type, _ = mimetypes.guess_type(destination)
        final_mime = mime_type or guessed_type or "application/octet-stream"

        return {
            "filename": os.path.basename(destination),
            "path": destination,
            "size": size,
            "mimeType": final_mime
        }

    async def download(self, path: str):
        full_path = self.get_full_path(path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        return full_path  # We can return the path directly for FastAPI's FileResponse/StreamingResponse

    async def delete(self, path: str):
        full_path = self.get_full_path(path)
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"File deleted: {path}")
        else:
            print(f"File not found for deletion: {path}")

    async def exists(self, path: str) -> bool:
        full_path = self.get_full_path(path)
        return os.path.exists(full_path)

    async def get_metadata(self, path: str) -> dict:
        full_path = self.get_full_path(path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        
        stat = os.stat(full_path)
        guessed_type, _ = mimetypes.guess_type(full_path)
        mime_type = guessed_type or "application/octet-stream"
        
        return {
            "size": stat.st_size,
            "mimeType": mime_type,
            "lastModified": datetime.fromtimestamp(stat.st_mtime)
        }

    def get_public_url(self, path: str) -> str:
        # Note: path might contain spaces or slashes
        return f"{self.base_url}/videos/stream/{path}"


class StorageService:
    def __init__(self):
        # Only local storage is supported as per TS implementation fallback
        self.provider = LocalStorageProvider()

    async def upload(self, file_data: Union[bytes, BinaryIO], destination: str, mime_type: Optional[str] = None) -> dict:
        return await self.provider.upload(file_data, destination, mime_type)

    async def download(self, path: str) -> str:
        return await self.provider.download(path)

    async def delete(self, path: str):
        await self.provider.delete(path)

    async def exists(self, path: str) -> bool:
        return await self.provider.exists(path)

    async def get_metadata(self, path: str) -> dict:
        return await self.provider.get_metadata(path)

    def get_public_url(self, path: str) -> str:
        return self.provider.get_public_url(path)

    async def save_document(self, buffer: bytes, filename: str) -> str:
        # Save a document file to storage
        destination = f"documents/{datetime.now().year}/{filename}"
        await self.upload(buffer, destination)
        return destination

    async def delete_file(self, path: str):
        await self.delete(path)

# Global storage service instance
storage_service = StorageService()
