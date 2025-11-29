"""
Cloudinary Storage Service
Handles all file uploads and storage operations to Cloudinary
With local fallback when Cloudinary is not configured
"""

import cloudinary
import cloudinary.uploader
from pathlib import Path
from config import Config
import os
import shutil
import uuid
from PIL import Image


# Check if Cloudinary is configured
CLOUDINARY_CONFIGURED = bool(
    os.environ.get('CLOUDINARY_CLOUD_NAME') and 
    os.environ.get('CLOUDINARY_API_KEY') and 
    os.environ.get('CLOUDINARY_API_SECRET')
)

if not CLOUDINARY_CONFIGURED:
    print("[INFO] Cloudinary not configured - using local storage fallback")


class CloudinaryStorageService:
    """Service for managing file uploads to Cloudinary (with local fallback)"""
    
    MEME_FOLDER = 'trendrit/memes'
    OUTPUT_FOLDER = 'trendrit/outputs'
    MESH_FOLDER = 'trendrit/meshes'
    GIF_FOLDER = 'trendrit/gifs'
    
    # Local storage paths (fallback)
    LOCAL_STORAGE_BASE = 'static/uploads'
    
    @staticmethod
    def _get_local_url(relative_path):
        """Generate local URL for a file"""
        return f"http://localhost:5000/static/uploads/{relative_path}"
    
    @staticmethod
    def upload_meme_image(file_path, user_id, filename=None):
        """
        Upload meme image to Cloudinary or local storage
        
        Args:
            file_path: Local path to the image file
            user_id: ID of the user uploading
            filename: Optional custom filename
            
        Returns:
            dict with 'url' and 'public_id' of uploaded file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Use local storage if Cloudinary is not configured
        if not CLOUDINARY_CONFIGURED:
            return CloudinaryStorageService._upload_local_image(file_path, user_id, filename)
        
        try:
            public_id = f"{CloudinaryStorageService.MEME_FOLDER}/{user_id}/{filename or Path(file_path).stem}"
            
            result = cloudinary.uploader.upload(
                file_path,
                public_id=public_id,
                folder=CloudinaryStorageService.MEME_FOLDER,
                resource_type='image',
                overwrite=True,
                tags=['meme', user_id]
            )
            
            return {
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'format': result.get('format'),
                'width': result.get('width'),
                'height': result.get('height')
            }
        except Exception as e:
            print(f"Error uploading to Cloudinary, falling back to local: {e}")
            return CloudinaryStorageService._upload_local_image(file_path, user_id, filename)
    
    @staticmethod
    def _upload_local_image(file_path, user_id, filename=None):
        """Upload image to local storage (fallback)"""
        # Create local storage directory
        user_folder = os.path.join(CloudinaryStorageService.LOCAL_STORAGE_BASE, 'memes', user_id)
        os.makedirs(user_folder, exist_ok=True)
        
        # Generate unique filename
        original_name = filename or Path(file_path).name
        unique_id = str(uuid.uuid4())[:8]
        dest_filename = f"{unique_id}_{original_name}"
        dest_path = os.path.join(user_folder, dest_filename)
        
        # Copy file to local storage
        shutil.copy2(file_path, dest_path)
        
        # Get image dimensions
        width, height = None, None
        try:
            with Image.open(dest_path) as img:
                width, height = img.size
        except:
            pass
        
        relative_path = f"memes/{user_id}/{dest_filename}"
        
        return {
            'url': CloudinaryStorageService._get_local_url(relative_path),
            'public_id': f"local/{relative_path}",
            'format': Path(file_path).suffix.lstrip('.'),
            'width': width,
            'height': height
        }
    
    @staticmethod
    def upload_mesh(file_path, meme_id, subject_id):
        """
        Upload 3D mesh file to Cloudinary or local storage
        
        Args:
            file_path: Local path to mesh file (.glb, .obj, etc)
            meme_id: Associated meme ID
            subject_id: Associated subject ID
            
        Returns:
            dict with 'url' and 'public_id' of uploaded file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Use local storage if Cloudinary is not configured
        if not CLOUDINARY_CONFIGURED:
            return CloudinaryStorageService._upload_local_file(
                file_path, 'meshes', f"{meme_id}/subject_{subject_id}"
            )
        
        try:
            file_ext = Path(file_path).suffix
            public_id = f"{CloudinaryStorageService.MESH_FOLDER}/{meme_id}/subject_{subject_id}"
            
            result = cloudinary.uploader.upload(
                file_path,
                public_id=public_id,
                resource_type='raw',
                overwrite=True,
                tags=['mesh', meme_id, f'subject_{subject_id}']
            )
            
            return {
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'bytes': result.get('bytes')
            }
        except Exception as e:
            print(f"Error uploading mesh to Cloudinary, falling back to local: {e}")
            return CloudinaryStorageService._upload_local_file(
                file_path, 'meshes', f"{meme_id}/subject_{subject_id}"
            )
    
    @staticmethod
    def _upload_local_file(file_path, folder, name):
        """Upload any file to local storage (fallback)"""
        dest_folder = os.path.join(CloudinaryStorageService.LOCAL_STORAGE_BASE, folder)
        os.makedirs(dest_folder, exist_ok=True)
        
        file_ext = Path(file_path).suffix
        dest_filename = f"{name.replace('/', '_')}{file_ext}"
        dest_path = os.path.join(dest_folder, dest_filename)
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(dest_path), exist_ok=True) if os.path.dirname(dest_path) else None
        
        shutil.copy2(file_path, dest_path)
        
        relative_path = f"{folder}/{dest_filename}"
        file_size = os.path.getsize(dest_path)
        
        return {
            'url': CloudinaryStorageService._get_local_url(relative_path),
            'public_id': f"local/{relative_path}",
            'bytes': file_size
        }
    
    @staticmethod
    def upload_gif(file_path, meme_id):
        """
        Upload GIF export to Cloudinary or local storage
        
        Args:
            file_path: Local path to GIF file
            meme_id: Associated meme ID
            
        Returns:
            dict with 'url' and 'public_id' of uploaded file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not CLOUDINARY_CONFIGURED:
            return CloudinaryStorageService._upload_local_file(file_path, 'gifs', meme_id)
        
        try:
            public_id = f"{CloudinaryStorageService.GIF_FOLDER}/{meme_id}"
            
            result = cloudinary.uploader.upload(
                file_path,
                public_id=public_id,
                resource_type='image',
                format='gif',
                overwrite=True,
                tags=['gif', meme_id]
            )
            
            return {
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'duration': result.get('duration'),
                'frames': result.get('frames')
            }
        except Exception as e:
            print(f"Error uploading GIF to Cloudinary, falling back to local: {e}")
            return CloudinaryStorageService._upload_local_file(file_path, 'gifs', meme_id)
    
    @staticmethod
    def upload_video(file_path, meme_id):
        """
        Upload video export to Cloudinary or local storage
        
        Args:
            file_path: Local path to video file
            meme_id: Associated meme ID
            
        Returns:
            dict with 'url' and 'public_id' of uploaded file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not CLOUDINARY_CONFIGURED:
            return CloudinaryStorageService._upload_local_file(file_path, 'videos', meme_id)
        
        try:
            public_id = f"{CloudinaryStorageService.OUTPUT_FOLDER}/{meme_id}/video"
            
            result = cloudinary.uploader.upload(
                file_path,
                public_id=public_id,
                resource_type='video',
                overwrite=True,
                tags=['video', meme_id]
            )
            
            return {
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'duration': result.get('duration'),
                'width': result.get('width'),
                'height': result.get('height')
            }
        except Exception as e:
            print(f"Error uploading video to Cloudinary, falling back to local: {e}")
            return CloudinaryStorageService._upload_local_file(file_path, 'videos', meme_id)
    
    @staticmethod
    def delete_file(public_id, resource_type='image'):
        """
        Delete file from Cloudinary or local storage
        
        Args:
            public_id: Public ID of the file to delete
            resource_type: Type of resource ('image', 'video', 'raw')
            
        Returns:
            dict with deletion result
        """
        # Handle local files
        if public_id.startswith('local/'):
            local_path = os.path.join(
                CloudinaryStorageService.LOCAL_STORAGE_BASE,
                public_id.replace('local/', '')
            )
            if os.path.exists(local_path):
                os.remove(local_path)
                return {'result': 'ok'}
            return {'result': 'not found'}
        
        if not CLOUDINARY_CONFIGURED:
            return {'result': 'cloudinary not configured'}
        
        try:
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type
            )
            return result
        except Exception as e:
            print(f"Error deleting file: {e}")
            raise
    
    @staticmethod
    def get_file_url(public_id, transformations=None):
        """
        Generate Cloudinary URL with optional transformations or local URL
        
        Args:
            public_id: Public ID of the file
            transformations: Optional list of transformations to apply
            
        Returns:
            URL string
        """
        # Handle local files
        if public_id.startswith('local/'):
            return CloudinaryStorageService._get_local_url(public_id.replace('local/', ''))
        
        if not CLOUDINARY_CONFIGURED:
            return None
        
        if transformations:
            return cloudinary.CloudinaryImage(public_id).build_url(**transformations)
        return cloudinary.CloudinaryImage(public_id).build_url()
    
    @staticmethod
    def list_user_files(user_id):
        """
        List all files uploaded by a user
        
        Args:
            user_id: User ID to filter by
            
        Returns:
            list of file resources
        """
        if not CLOUDINARY_CONFIGURED:
            # List local files for user
            user_folder = os.path.join(CloudinaryStorageService.LOCAL_STORAGE_BASE, 'memes', user_id)
            if not os.path.exists(user_folder):
                return []
            
            files = []
            for filename in os.listdir(user_folder):
                file_path = os.path.join(user_folder, filename)
                files.append({
                    'public_id': f"local/memes/{user_id}/{filename}",
                    'url': CloudinaryStorageService._get_local_url(f"memes/{user_id}/{filename}"),
                    'bytes': os.path.getsize(file_path)
                })
            return files
        
        try:
            # Search for files with user_id tag
            resources = cloudinary.api.resources(
                tags=[user_id],
                max_results=100
            )
            return resources.get('resources', [])
        except Exception as e:
            print(f"Error listing user files: {e}")
            return []
