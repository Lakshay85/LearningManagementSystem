import os
import base64
import mimetypes
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

    async def delete_by_file_id(self, file_id: str):
        """Local storage doesn't use file IDs, fall back to path-based delete."""
        print(f"[LocalStorage] delete_by_file_id not supported, ignoring file_id: {file_id}")


class ImageKitStorageProvider:
    """Storage provider using ImageKit.io CDN for file uploads and management."""

    def __init__(self):
        from imagekitio import ImageKit

        self.imagekit = ImageKit(
            private_key=settings.IMAGEKIT_PRIVATE_KEY,
        )
        self.url_endpoint = settings.IMAGEKIT_URL_ENDPOINT.rstrip("/")
        print(f"[Storage] ImageKit storage provider initialized (endpoint: {self.url_endpoint})")

    async def upload(
        self,
        file_data: Union[bytes, BinaryIO],
        destination: str,
        mime_type: Optional[str] = None,
    ) -> dict:
        """Upload a file to ImageKit.

        Args:
            file_data: Raw bytes or file-like object.
            destination: Desired path on ImageKit, e.g. ``videos/myvideo.mp4``.
            mime_type: Optional MIME type hint.

        Returns:
            dict with keys: filename, path, size, mimeType, fileId, cdnUrl
        """

        if isinstance(file_data, bytes):
            raw_bytes = file_data
        else:
            file_data.seek(0)
            raw_bytes = file_data.read()

        # Split destination into folder + filename
        parts = destination.replace("\\", "/").rsplit("/", 1)
        if len(parts) == 2:
            folder, file_name = parts
            folder = f"/lms/{folder}"
        else:
            folder = "/lms"
            file_name = parts[0]

        # Run synchronous ImageKit upload in thread pool with 600s timeout for large videos
        import asyncio
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.imagekit.files.upload(
                file=raw_bytes,
                file_name=file_name,
                folder=folder,
                is_private_file=False,
                use_unique_file_name=False,
                overwrite_file=True,
                timeout=600.0,
            )
        )

        # v5 SDK returns a pydantic model, access attributes directly
        cdn_url = getattr(result, "url", "")
        file_id = getattr(result, "file_id", "")
        file_path = getattr(result, "file_path", destination)
        size = getattr(result, "size", len(raw_bytes))

        guessed_type, _ = mimetypes.guess_type(file_name)
        final_mime = mime_type or guessed_type or "application/octet-stream"

        print(f"[ImageKit] Uploaded: {file_name} → {cdn_url} (fileId: {file_id})")

        return {
            "filename": file_name,
            "path": file_path,
            "size": size,
            "mimeType": final_mime,
            "fileId": file_id,
            "cdnUrl": cdn_url,
        }

    async def download(self, path: str) -> str:
        """Return the CDN URL for the given path (no local file)."""
        return self.get_public_url(path)

    async def delete(self, path: str):
        """Delete by path is not directly supported on ImageKit. Use delete_by_file_id instead."""
        print(f"[ImageKit] delete by path not supported directly. Use delete_by_file_id. Path: {path}")

    async def delete_by_file_id(self, file_id: str):
        """Delete a file from ImageKit using its fileId."""
        if not file_id:
            print("[ImageKit] No file ID provided for deletion, skipping.")
            return
        try:
            self.imagekit.files.delete(file_id=file_id)
            print(f"[ImageKit] Deleted file: {file_id}")
        except Exception as e:
            print(f"[ImageKit] Failed to delete file {file_id}: {str(e)}")

    async def exists(self, path: str) -> bool:
        """Check if a file exists on ImageKit."""
        try:
            results = self.imagekit.files.get(file_id=path)
            return results is not None
        except Exception:
            return False

    async def get_metadata(self, path: str) -> dict:
        """Get file metadata from ImageKit."""
        return {
            "size": 0,
            "mimeType": "application/octet-stream",
            "lastModified": datetime.now(),
        }

    def get_public_url(self, path: str) -> str:
        """Return the full CDN URL for a given file path."""
        clean_path = path.lstrip("/")
        return f"{self.url_endpoint}/{clean_path}"


class StorageService:
    def __init__(self):
        provider_name = settings.STORAGE_PROVIDER.lower()
        if provider_name == "imagekit":
            self.provider = ImageKitStorageProvider()
        else:
            self.provider = LocalStorageProvider()
        self._provider_name = provider_name

    @property
    def is_imagekit(self) -> bool:
        return self._provider_name == "imagekit"

    async def upload(self, file_data: Union[bytes, BinaryIO], destination: str, mime_type: Optional[str] = None) -> dict:
        return await self.provider.upload(file_data, destination, mime_type)

    async def download(self, path: str) -> str:
        return await self.provider.download(path)

    async def delete(self, path: str):
        await self.provider.delete(path)

    async def delete_by_file_id(self, file_id: str):
        await self.provider.delete_by_file_id(file_id)

    async def exists(self, path: str) -> bool:
        return await self.provider.exists(path)

    async def get_metadata(self, path: str) -> dict:
        return await self.provider.get_metadata(path)

    def get_public_url(self, path: str) -> str:
        return self.provider.get_public_url(path)

    async def save_document(self, buffer: bytes, filename: str) -> dict:
        """Save a document file to storage and return upload result dict.

        For ImageKit, returns full result with fileId/cdnUrl.
        For local storage, returns basic result with path.
        """
        destination = f"documents/{datetime.now().year}/{filename}"
        return await self.upload(buffer, destination)

    async def delete_file(self, path: str):
        await self.delete(path)


# Global storage service instance
storage_service = StorageService()
