import os
import re
import secrets
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

ALLOWED_VIDEO_MIME_TYPES = [
    'video/mp4',
    'video/webm',
    'video/ogg',
    'video/quicktime',
    'video/x-msvideo',
    'video/x-matroska',
    'video/x-flv',
    'video/3gpp',
    'video/3gpp2',
]

ALLOWED_VIDEO_EXTENSIONS = [
    '.mp4',
    '.webm',
    '.ogg',
    '.ogv',
    '.mov',
    '.avi',
    '.mkv',
    '.flv',
    '.3gp',
    '.3g2',
]

MAX_VIDEO_FILE_SIZE = 500 * 1024 * 1024

DANGEROUS_PATTERNS = [
    (re.compile(r'\.\.'), '_'),
    (re.compile(r'[<>:"|?*]'), '_'),
    (re.compile(r'[\x00-\x1f\x80-\x9f]'), '_'),
]

WINDOWS_RESERVED_NAMES = re.compile(r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])$', re.I)

def sanitize_filename(filename: str) -> str:
    if not filename:
        return f"file_{int(datetime.now().timestamp())}"

    # Get basename
    sanitized = os.path.basename(filename)

    # Replace dangerous characters
    for pattern, replacement in DANGEROUS_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    # Windows reserved names
    base, ext = os.path.splitext(sanitized)
    if WINDOWS_RESERVED_NAMES.match(base):
        base = "_" + base

    # Clean whitespace and multiple underscores
    sanitized = sanitized.strip().strip('.')
    sanitized = re.sub(r'[_\s]+', '_', sanitized)

    # Limit filename length
    truncated_base = base[:100]
    if not truncated_base:
        random_suffix = secrets.token_hex(4)
        return f"video_{int(datetime.now().timestamp())}_{random_suffix}{ext or '.mp4'}"

    return truncated_base + ext

def generate_unique_filename(original_filename: str) -> str:
    sanitized = sanitize_filename(original_filename)
    base, ext = os.path.splitext(sanitized)
    if not ext:
        ext = '.mp4'
    timestamp = int(datetime.now().timestamp() * 1000)
    random_suffix = secrets.token_hex(8)
    return f"{base}_{timestamp}_{random_suffix}{ext}"

def is_valid_video_mime_type(mime_type: str) -> bool:
    return mime_type.lower() in ALLOWED_VIDEO_MIME_TYPES

def is_valid_video_extension(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_VIDEO_EXTENSIONS

def is_valid_file_size(size: int) -> bool:
    return 0 < size <= MAX_VIDEO_FILE_SIZE

def validate_video_file(filename: str, mime_type: str, size: int) -> Tuple[bool, Optional[str]]:
    if not is_valid_video_mime_type(mime_type):
        return False, f"Invalid file type. Allowed types: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"

    if not is_valid_video_extension(filename):
        return False, f"Invalid file extension. Allowed extensions: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"

    if not is_valid_file_size(size):
        return False, f"File size must be between 1 byte and {MAX_VIDEO_FILE_SIZE / (1024 * 1024)} MB"

    return True, None

def get_video_storage_path(filename: str) -> str:
    now = datetime.now()
    year = now.year
    month = str(now.month).zfill(2)
    day = str(now.day).zfill(2)
    return f"videos/{year}/{month}/{day}/{filename}"

def format_file_size(bytes_size: int) -> str:
    if bytes_size == 0:
        return '0 Bytes'
    k = 1024
    sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    import math
    i = int(math.floor(math.log(bytes_size) / math.log(k)))
    return f"{round(bytes_size / (k ** i), 2)} {sizes[i]}"
