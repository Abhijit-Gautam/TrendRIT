"""
Utility helpers for TrendRIT Backend
Common functions for file handling, validation, and image processing
"""

import os
from PIL import Image
from werkzeug.utils import secure_filename
from typing import Tuple, Optional, List
import hashlib
from datetime import datetime


# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}


def allowed_file(filename: str) -> bool:
    """
    Check if file extension is allowed
    
    Args:
        filename: Name of the file
        
    Returns:
        True if extension is allowed
    """
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_image(filepath: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a file is a valid image
    
    Args:
        filepath: Path to the image file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with Image.open(filepath) as img:
            img.verify()
        return True, None
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"


def get_image_dimensions(filepath: str) -> Optional[Tuple[int, int]]:
    """
    Get dimensions of an image
    
    Args:
        filepath: Path to the image file
        
    Returns:
        Tuple of (width, height) or None if error
    """
    try:
        with Image.open(filepath) as img:
            return img.size
    except:
        return None


def resize_image_if_needed(
    image: Image.Image, 
    max_dimension: int = 2048
) -> Image.Image:
    """
    Resize image if it exceeds max dimension while preserving aspect ratio
    
    Args:
        image: PIL Image object
        max_dimension: Maximum width or height
        
    Returns:
        Resized image (or original if no resize needed)
    """
    width, height = image.size
    
    if width <= max_dimension and height <= max_dimension:
        return image
    
    if width > height:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    else:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))
    
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def generate_unique_filename(original_filename: str, prefix: str = '') -> str:
    """
    Generate a unique filename with timestamp and hash
    
    Args:
        original_filename: Original file name
        prefix: Optional prefix for the filename
        
    Returns:
        Unique filename
    """
    ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'png'
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    hash_suffix = hashlib.md5(f"{original_filename}{timestamp}".encode()).hexdigest()[:8]
    
    if prefix:
        return f"{prefix}_{timestamp}_{hash_suffix}.{ext}"
    return f"{timestamp}_{hash_suffix}.{ext}"


def ensure_directory(path: str) -> str:
    """
    Ensure directory exists, create if not
    
    Args:
        path: Directory path
        
    Returns:
        The path (for chaining)
    """
    os.makedirs(path, exist_ok=True)
    return path


def get_file_size_mb(filepath: str) -> float:
    """
    Get file size in megabytes
    
    Args:
        filepath: Path to file
        
    Returns:
        File size in MB
    """
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0.0


def clean_filename(filename: str) -> str:
    """
    Clean and secure a filename
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename safe for filesystem
    """
    return secure_filename(filename)


def get_mime_type(filename: str) -> str:
    """
    Get MIME type from filename
    
    Args:
        filename: Name of the file
        
    Returns:
        MIME type string
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    mime_types = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp',
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'glb': 'model/gltf-binary',
        'gltf': 'model/gltf+json',
        'obj': 'model/obj',
        'ply': 'application/octet-stream'
    }
    
    return mime_types.get(ext, 'application/octet-stream')


def format_file_size(size_bytes: int) -> str:
    """
    Format file size to human readable string
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def list_files_in_directory(
    directory: str, 
    extensions: Optional[List[str]] = None
) -> List[str]:
    """
    List files in a directory with optional extension filter
    
    Args:
        directory: Directory path
        extensions: Optional list of extensions to filter
        
    Returns:
        List of file paths
    """
    if not os.path.exists(directory):
        return []
    
    files = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            if extensions is None:
                files.append(filepath)
            else:
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                if ext in extensions:
                    files.append(filepath)
    
    return files


def delete_file_safe(filepath: str) -> bool:
    """
    Safely delete a file if it exists
    
    Args:
        filepath: Path to file
        
    Returns:
        True if deleted or didn't exist, False on error
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        return True
    except Exception as e:
        print(f"Error deleting file {filepath}: {e}")
        return False


def image_to_base64(image: Image.Image, format: str = 'PNG') -> str:
    """
    Convert PIL Image to base64 string
    
    Args:
        image: PIL Image object
        format: Image format (PNG, JPEG, etc.)
        
    Returns:
        Base64 encoded string
    """
    import base64
    from io import BytesIO
    
    buffer = BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def base64_to_image(base64_string: str) -> Image.Image:
    """
    Convert base64 string to PIL Image
    
    Args:
        base64_string: Base64 encoded image string
        
    Returns:
        PIL Image object
    """
    import base64
    from io import BytesIO
    
    # Remove data URL prefix if present
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    image_data = base64.b64decode(base64_string)
    return Image.open(BytesIO(image_data))
