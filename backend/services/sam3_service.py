import torch
from sam3.model_builder import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor
from PIL import Image
import numpy as np

class SAM3Service:
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = build_sam3_image_model()
        self.model.to(self.device)
        self.processor = Sam3Processor(self.model)
    
    def segment_subjects(self, image_path, prompt=None):
        """
        Segment meme subjects from image
        Returns: List of masks and bounding boxes
        """
        image = Image.open(image_path).convert('RGB')
        
        # Auto-detect main subjects or use prompt
        if prompt is None:
            prompt = "people, faces, animals, main character"
        
        masks = self.processor.segment(image, text_prompts=[prompt])
        return self._process_masks(masks, image)
    
    def _process_masks(self, masks, image):
        # Extract individual subject masks with metadata
        subjects = []
        for i, mask in enumerate(masks):
            bbox = self._get_bbox(mask)
            cropped = self._extract_subject(image, mask)
            subjects.append({
                'id': i,
                'mask': mask,
                'bbox': bbox,
                'image': cropped
            })
        return subjects
    
    def _get_bbox(self, mask):
        """Extract bounding box from mask"""
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        return {'x': int(cmin), 'y': int(rmin), 'width': int(cmax - cmin), 'height': int(rmax - rmin)}
    
    def _extract_subject(self, image, mask):
        """Extract subject from image using mask"""
        img_array = np.array(image)
        mask_3d = np.stack([mask] * 3, axis=-1)
        masked = img_array * mask_3d
        return Image.fromarray(masked.astype('uint8'))
