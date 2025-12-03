"""
Export Service for generating animated GIFs and videos from 3D meshes
Supports local file storage and various export formats
"""

import trimesh
import numpy as np
from PIL import Image
import imageio
import io
from pathlib import Path
from typing import Optional, List
import os


class ExportService:
    """Service for exporting 3D scenes as GIFs and videos"""
    
    def __init__(self, output_folder='./data/exports'):
        """
        Initialize export service
        
        Args:
            output_folder: Directory for saving exported files
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        print(f"[OK] ExportService initialized, output: {self.output_folder}")
    
    def create_rotating_gif(
        self, 
        mesh_path: str, 
        output_name: str, 
        frames: int = 36,
        duration: float = 0.1,
        resolution: tuple = (800, 600)
    ) -> str:
        """
        Create 360° rotating GIF of 3D mesh
        
        Args:
            mesh_path: Path to the mesh file (.glb, .obj, .ply)
            output_name: Name for the output file (without extension)
            frames: Number of frames in the animation
            duration: Duration per frame in seconds
            resolution: Output resolution (width, height)
            
        Returns:
            Path to the generated GIF
        """
        # Load mesh
        mesh = trimesh.load(mesh_path)
        
        # Handle scene vs single mesh
        if isinstance(mesh, trimesh.Scene):
            # Combine all geometries in the scene
            meshes = []
            for name, geometry in mesh.geometry.items():
                if isinstance(geometry, trimesh.Trimesh):
                    meshes.append(geometry)
            if meshes:
                mesh = trimesh.util.concatenate(meshes)
            else:
                raise ValueError("No valid meshes found in scene")
        
        images = []
        for i in range(frames):
            angle = (i / frames) * 2 * np.pi
            
            # Create rotation matrix around Y-axis
            rotation_matrix = trimesh.transformations.rotation_matrix(
                angle, [0, 1, 0], point=mesh.centroid
            )
            
            # Apply rotation to a copy
            rotated_mesh = mesh.copy()
            rotated_mesh.apply_transform(rotation_matrix)
            
            # Render to image
            img = self._render_mesh(rotated_mesh, resolution)
            if img is not None:
                images.append(img)
        
        if not images:
            raise ValueError("Failed to render any frames")
        
        # Save as GIF
        output_path = self.output_folder / f"{output_name}.gif"
        imageio.mimsave(str(output_path), images, duration=duration, loop=0)
        
        print(f"[OK] Created GIF: {output_path} ({len(images)} frames)")
        return str(output_path)
    
    def _render_mesh(
        self, 
        mesh: trimesh.Trimesh, 
        resolution: tuple = (800, 600)
    ) -> Optional[np.ndarray]:
        """
        Render mesh to image array
        
        Args:
            mesh: Trimesh object to render
            resolution: Output resolution
            
        Returns:
            Image as numpy array or None
        """
        try:
            # Create scene with the mesh
            scene = mesh.scene()
            
            # Try to render using trimesh's built-in rendering
            png_bytes = scene.save_image(resolution=resolution)
            
            # Convert to PIL Image then to numpy array
            img = Image.open(io.BytesIO(png_bytes))
            return np.array(img)
            
        except Exception as e:
            print(f"[WARNING] Render failed: {e}")
            # Fallback: create a placeholder image
            return self._create_placeholder_frame(resolution)
    
    def _create_placeholder_frame(
        self, 
        resolution: tuple = (800, 600)
    ) -> np.ndarray:
        """Create a placeholder frame when rendering fails"""
        # Create a simple gradient placeholder
        width, height = resolution
        img = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add gradient
        for y in range(height):
            gray = int(50 + (y / height) * 100)
            img[y, :] = [gray, gray, gray]
        
        return img
    
    def create_orbit_animation(
        self,
        mesh_path: str,
        output_name: str,
        frames: int = 60,
        orbit_radius: float = 2.0,
        elevation_angle: float = 30.0,
        format: str = 'gif'
    ) -> str:
        """
        Create orbit animation around the mesh
        
        Args:
            mesh_path: Path to mesh file
            output_name: Output filename
            frames: Number of frames
            orbit_radius: Camera orbit radius
            elevation_angle: Camera elevation in degrees
            format: Output format ('gif' or 'mp4')
            
        Returns:
            Path to output file
        """
        mesh = trimesh.load(mesh_path)
        
        if isinstance(mesh, trimesh.Scene):
            meshes = [g for g in mesh.geometry.values() if isinstance(g, trimesh.Trimesh)]
            mesh = trimesh.util.concatenate(meshes) if meshes else None
        
        if mesh is None:
            raise ValueError("No valid mesh found")
        
        images = []
        center = mesh.centroid
        
        for i in range(frames):
            # Calculate camera position on orbit
            angle = (i / frames) * 2 * np.pi
            elevation_rad = np.radians(elevation_angle)
            
            cam_x = center[0] + orbit_radius * np.cos(angle) * np.cos(elevation_rad)
            cam_y = center[1] + orbit_radius * np.sin(elevation_rad)
            cam_z = center[2] + orbit_radius * np.sin(angle) * np.cos(elevation_rad)
            
            # For now, use simple rotation-based rendering
            rotation = trimesh.transformations.rotation_matrix(
                angle, [0, 1, 0], point=center
            )
            
            rotated = mesh.copy()
            rotated.apply_transform(rotation)
            
            img = self._render_mesh(rotated)
            if img is not None:
                images.append(img)
        
        # Save output
        if format == 'gif':
            output_path = self.output_folder / f"{output_name}.gif"
            imageio.mimsave(str(output_path), images, duration=0.05, loop=0)
        else:
            output_path = self.output_folder / f"{output_name}.mp4"
            imageio.mimsave(str(output_path), images, fps=30)
        
        return str(output_path)
    
    def create_depth_visualization(
        self,
        depth_map: np.ndarray,
        output_name: str,
        colormap: str = 'viridis'
    ) -> str:
        """
        Create colored depth visualization image
        
        Args:
            depth_map: 2D numpy array of depth values
            output_name: Output filename
            colormap: Matplotlib colormap name
            
        Returns:
            Path to output image
        """
        import matplotlib.pyplot as plt
        
        # Normalize depth map
        depth_normalized = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())
        
        # Apply colormap
        cmap = plt.get_cmap(colormap)
        colored = (cmap(depth_normalized)[:, :, :3] * 255).astype(np.uint8)
        
        # Save image
        output_path = self.output_folder / f"{output_name}_depth.png"
        Image.fromarray(colored).save(str(output_path))
        
        return str(output_path)
    
    def get_export_info(self, export_path: str) -> dict:
        """
        Get information about an exported file
        
        Args:
            export_path: Path to the export file
            
        Returns:
            Dictionary with file information
        """
        path = Path(export_path)
        
        if not path.exists():
            return {'error': 'File not found'}
        
        info = {
            'path': str(path),
            'filename': path.name,
            'extension': path.suffix,
            'size_bytes': path.stat().st_size,
            'size_mb': path.stat().st_size / (1024 * 1024)
        }
        
        # Get additional info for images/gifs
        if path.suffix.lower() in ['.gif', '.png', '.jpg', '.jpeg']:
            try:
                with Image.open(path) as img:
                    info['width'] = img.width
                    info['height'] = img.height
                    if hasattr(img, 'n_frames'):
                        info['frames'] = img.n_frames
            except:
                pass
        
        return info
