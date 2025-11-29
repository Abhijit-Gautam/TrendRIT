import trimesh
import numpy as np
from PIL import Image
import imageio
import io
from pathlib import Path

class ExportService:
    def __init__(self, output_folder='outputs/'):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
    
    def create_rotating_gif(self, mesh_path, output_name, frames=36):
        """Create 360° rotating GIF of 3D mesh"""
        mesh = trimesh.load(mesh_path)
        
        images = []
        for i in range(frames):
            angle = (i / frames) * 2 * np.pi
            
            # Render mesh from rotating camera
            rotation_matrix = trimesh.transformations.rotation_matrix(
                angle, [0, 1, 0]
            )
            rotated_mesh = mesh.copy()
            rotated_mesh.apply_transform(rotation_matrix)
            
            # Render to image
            img = self._render_mesh(rotated_mesh)
            images.append(img)
        
        # Save as GIF
        output_path = self.output_folder / f"{output_name}.gif"
        imageio.mimsave(output_path, images, duration=0.1)
        
        return str(output_path)
    
    def _render_mesh(self, mesh):
        """Render mesh to PIL Image using pyrender or simple projection"""
        # Simplified: Use trimesh's built-in rendering
        scene = mesh.scene()
        png = scene.save_image(resolution=[800, 600])
        return Image.open(io.BytesIO(png))
