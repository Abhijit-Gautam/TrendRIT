"""
Reconstruction Service for 3D mesh generation
Converts depth maps and RGB images into 3D point clouds and textured meshes
"""

import numpy as np
import open3d as o3d
import trimesh
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import os


class ReconstructionService:
    """
    Service for converting 2D images with depth maps into 3D meshes
    Uses Open3D for point cloud processing and Trimesh for mesh operations
    """
    
    def __init__(self, output_folder='./data/3d_models'):
        """
        Initialize reconstruction service
        
        Args:
            output_folder: Directory for saving 3D models
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        # Default camera intrinsics (will be adjusted based on image size)
        self.default_focal_length_factor = 0.7  # Focal length as factor of width
        
        print(f"[OK] ReconstructionService initialized, output: {self.output_folder}")
    
    def depth_to_pointcloud(
        self, 
        image: Image.Image, 
        depth_map: np.ndarray, 
        mask: Optional[np.ndarray] = None,
        scale_factor: float = 1.0
    ) -> o3d.geometry.PointCloud:
        """
        Convert depth map to colored 3D point cloud
        
        Args:
            image: RGB PIL Image
            depth_map: 2D numpy array of depth values
            mask: Optional binary mask to filter points
            scale_factor: Depth scale adjustment
            
        Returns:
            Open3D PointCloud object
        """
        img_array = np.array(image)
        h, w = depth_map.shape
        
        # Handle image/depth size mismatch
        if img_array.shape[:2] != (h, w):
            image = image.resize((w, h), Image.Resampling.LANCZOS)
            img_array = np.array(image)
        
        # Camera intrinsics (pinhole model)
        fx = fy = w * self.default_focal_length_factor
        cx, cy = w / 2.0, h / 2.0
        
        # Normalize depth
        depth_normalized = depth_map.astype(np.float32)
        depth_min, depth_max = depth_normalized.min(), depth_normalized.max()
        if depth_max > depth_min:
            depth_normalized = (depth_normalized - depth_min) / (depth_max - depth_min)
        depth_normalized = depth_normalized * scale_factor
        
        # Create meshgrid for coordinates
        u, v = np.meshgrid(np.arange(w), np.arange(h))
        
        # Apply mask if provided
        if mask is not None:
            valid = mask.astype(bool)
        else:
            valid = np.ones((h, w), dtype=bool)
        
        # Filter out zero/near-zero depth
        valid = valid & (depth_normalized > 0.01)
        
        # Get valid points
        z = depth_normalized[valid]
        x = (u[valid] - cx) * z / fx
        y = (v[valid] - cy) * z / fy
        
        points = np.stack([x, -y, -z], axis=-1)  # Flip Y and Z for standard orientation
        
        # Get colors
        if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
            colors = img_array[valid, :3] / 255.0
        else:
            # Grayscale
            gray = img_array[valid] / 255.0
            colors = np.stack([gray, gray, gray], axis=-1)
        
        # Create point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        pcd.colors = o3d.utility.Vector3dVector(colors)
        
        return pcd
    
    def clean_pointcloud(
        self, 
        pcd: o3d.geometry.PointCloud,
        nb_neighbors: int = 20,
        std_ratio: float = 2.0,
        voxel_size: float = 0.0
    ) -> o3d.geometry.PointCloud:
        """
        Clean point cloud by removing outliers and optionally downsampling
        
        Args:
            pcd: Input point cloud
            nb_neighbors: Number of neighbors for outlier detection
            std_ratio: Standard deviation ratio for outlier removal
            voxel_size: Voxel size for downsampling (0 = no downsampling)
            
        Returns:
            Cleaned point cloud
        """
        # Remove statistical outliers
        pcd_clean, _ = pcd.remove_statistical_outlier(
            nb_neighbors=nb_neighbors, 
            std_ratio=std_ratio
        )
        
        # Optional voxel downsampling
        if voxel_size > 0:
            pcd_clean = pcd_clean.voxel_down_sample(voxel_size)
        
        # Estimate normals
        pcd_clean.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
        )
        pcd_clean.orient_normals_towards_camera_location()
        
        return pcd_clean
    
    def pointcloud_to_mesh(
        self, 
        pcd: o3d.geometry.PointCloud,
        method: str = 'poisson',
        depth: int = 9
    ) -> o3d.geometry.TriangleMesh:
        """
        Convert point cloud to triangle mesh
        
        Args:
            pcd: Input point cloud with normals
            method: Reconstruction method ('poisson' or 'ball_pivoting')
            depth: Depth parameter for Poisson reconstruction
            
        Returns:
            Triangle mesh
        """
        if method == 'poisson':
            # Poisson surface reconstruction
            mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                pcd, depth=depth
            )
            
            # Remove low density vertices (cleanup)
            densities = np.asarray(densities)
            density_threshold = np.quantile(densities, 0.1)
            vertices_to_remove = densities < density_threshold
            mesh.remove_vertices_by_mask(vertices_to_remove)
            
        elif method == 'ball_pivoting':
            # Ball pivoting algorithm
            distances = pcd.compute_nearest_neighbor_distance()
            avg_dist = np.mean(distances)
            radii = [avg_dist * 0.5, avg_dist, avg_dist * 2]
            mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
                pcd, o3d.utility.DoubleVector(radii)
            )
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Clean mesh
        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_duplicated_vertices()
        mesh.remove_non_manifold_edges()
        
        return mesh
    
    def texture_mesh(
        self, 
        mesh: o3d.geometry.TriangleMesh, 
        image: Image.Image,
        depth_map: np.ndarray
    ) -> o3d.geometry.TriangleMesh:
        """
        Apply texture from original image to mesh using vertex colors
        
        Args:
            mesh: Input mesh
            image: Original RGB image
            depth_map: Original depth map for UV mapping
            
        Returns:
            Textured mesh
        """
        vertices = np.asarray(mesh.vertices)
        img_array = np.array(image)
        h, w = depth_map.shape
        
        # Camera intrinsics
        fx = fy = w * self.default_focal_length_factor
        cx, cy = w / 2.0, h / 2.0
        
        colors = []
        for vertex in vertices:
            x, y, z = vertex
            
            # Project back to image coordinates
            if abs(z) > 0.001:
                u = int(x * fx / (-z) + cx)
                v = int((-y) * fy / (-z) + cy)
                
                # Clamp to image bounds
                u = max(0, min(w - 1, u))
                v = max(0, min(h - 1, v))
                
                color = img_array[v, u, :3] / 255.0 if len(img_array.shape) == 3 else [0.5, 0.5, 0.5]
            else:
                color = [0.5, 0.5, 0.5]
            
            colors.append(color)
        
        mesh.vertex_colors = o3d.utility.Vector3dVector(np.array(colors))
        return mesh
    
    def reconstruct_from_image(
        self, 
        image: Image.Image, 
        depth_map: np.ndarray,
        mask: Optional[np.ndarray] = None,
        project_id: str = 'output',
        mesh_method: str = 'poisson'
    ) -> Dict[str, Any]:
        """
        Full reconstruction pipeline: image + depth -> textured 3D mesh
        
        Args:
            image: RGB PIL Image
            depth_map: Depth map as numpy array
            mask: Optional segmentation mask
            project_id: ID for output files
            mesh_method: Reconstruction method
            
        Returns:
            Dictionary with paths to output files and statistics
        """
        # Step 1: Create point cloud
        pcd = self.depth_to_pointcloud(image, depth_map, mask)
        print(f"  - Point cloud: {len(pcd.points)} points")
        
        # Step 2: Clean point cloud
        pcd_clean = self.clean_pointcloud(pcd)
        print(f"  - Cleaned: {len(pcd_clean.points)} points")
        
        # Step 3: Convert to mesh
        mesh = self.pointcloud_to_mesh(pcd_clean, method=mesh_method)
        print(f"  - Mesh: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")
        
        # Step 4: Apply texture
        mesh = self.texture_mesh(mesh, image, depth_map)
        
        # Save outputs
        pcd_path = self.output_folder / f"{project_id}_pointcloud.ply"
        mesh_glb_path = self.output_folder / f"{project_id}_mesh.glb"
        mesh_obj_path = self.output_folder / f"{project_id}_mesh.obj"
        
        # Save point cloud
        o3d.io.write_point_cloud(str(pcd_path), pcd_clean)
        
        # Save mesh in multiple formats
        o3d.io.write_triangle_mesh(str(mesh_glb_path), mesh)
        o3d.io.write_triangle_mesh(str(mesh_obj_path), mesh)
        
        return {
            'point_cloud_path': str(pcd_path),
            'mesh_glb_path': str(mesh_glb_path),
            'mesh_obj_path': str(mesh_obj_path),
            'stats': {
                'original_points': len(pcd.points),
                'cleaned_points': len(pcd_clean.points),
                'vertices': len(mesh.vertices),
                'triangles': len(mesh.triangles)
            }
        }
    
    def create_scene_composition(
        self,
        meshes: list,
        positions: list = None,
        scales: list = None,
        output_name: str = 'scene'
    ) -> str:
        """
        Compose multiple meshes into a single scene
        
        Args:
            meshes: List of mesh paths or Open3D meshes
            positions: List of (x, y, z) positions for each mesh
            scales: List of scale factors for each mesh
            output_name: Output filename
            
        Returns:
            Path to composed scene file
        """
        combined_mesh = o3d.geometry.TriangleMesh()
        
        for i, mesh_input in enumerate(meshes):
            # Load mesh if path is provided
            if isinstance(mesh_input, str):
                mesh = o3d.io.read_triangle_mesh(mesh_input)
            else:
                mesh = mesh_input
            
            # Apply scale if provided
            if scales and i < len(scales):
                mesh.scale(scales[i], center=mesh.get_center())
            
            # Apply position if provided
            if positions and i < len(positions):
                mesh.translate(positions[i])
            
            combined_mesh += mesh
        
        # Save combined scene
        output_path = self.output_folder / f"{output_name}_combined.glb"
        o3d.io.write_triangle_mesh(str(output_path), combined_mesh)
        
        return str(output_path)
    
    def load_3d_template(self, template_path: str) -> o3d.geometry.TriangleMesh:
        """Load a 3D template mesh"""
        return o3d.io.read_triangle_mesh(template_path)
    
    def get_mesh_bounds(self, mesh: o3d.geometry.TriangleMesh) -> Dict[str, Any]:
        """Get bounding box information for a mesh"""
        bbox = mesh.get_axis_aligned_bounding_box()
        return {
            'min_bound': bbox.min_bound.tolist(),
            'max_bound': bbox.max_bound.tolist(),
            'center': mesh.get_center().tolist(),
            'extent': (bbox.max_bound - bbox.min_bound).tolist()
        }
