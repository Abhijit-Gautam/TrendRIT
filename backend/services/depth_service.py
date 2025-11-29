from transformers import DPTImageProcessor, DPTForDepthEstimation
import torch
import numpy as np
import open3d as o3d
from PIL import Image

class DepthService:
    def __init__(self, model_name='Intel/dpt-hybrid-midas'):
        self.processor = DPTImageProcessor.from_pretrained(model_name)
        self.model = DPTForDepthEstimation.from_pretrained(model_name)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(self.device)
    
    def generate_depth_map(self, image):
        """Generate depth map from PIL Image"""
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            depth = outputs.predicted_depth
        
        depth = torch.nn.functional.interpolate(
            depth.unsqueeze(1),
            size=image.size[::-1],
            mode="bicubic",
            align_corners=False,
        ).squeeze()
        
        return depth.cpu().numpy()
    
    def create_3d_mesh(self, image, depth_map, mask=None):
        """Convert depth map to 3D point cloud and mesh"""
        # Generate point cloud
        point_cloud = self._depth_to_pointcloud(image, depth_map, mask)
        
        # Create mesh using Poisson reconstruction
        mesh = self._pointcloud_to_mesh(point_cloud)
        
        return mesh, point_cloud
    
    def _depth_to_pointcloud(self, image, depth, mask=None):
        h, w = depth.shape
        img_array = np.array(image)
        
        # Camera intrinsics (assume standard focal length)
        fx = fy = w * 0.7
        cx, cy = w / 2, h / 2
        
        points = []
        colors = []
        
        for v in range(h):
            for u in range(w):
                if mask is not None and not mask[v, u]:
                    continue
                
                z = depth[v, u]
                x = (u - cx) * z / fx
                y = (v - cy) * z / fy
                
                points.append([x, y, z])
                colors.append(img_array[v, u] / 255.0)
        
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.array(points))
        pcd.colors = o3d.utility.Vector3dVector(np.array(colors))
        
        return pcd
    
    def _pointcloud_to_mesh(self, pcd):
        # Clean point cloud
        pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
        pcd.estimate_normals()
        
        # Poisson surface reconstruction
        mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd, depth=9
        )
        return mesh
