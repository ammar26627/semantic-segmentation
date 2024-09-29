import os
import pandas as pd
import cv2
import torch
import torch.nn.utils
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from sklearn.model_selection import train_test_split
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

class Deeplearning():
    def __init__(self, png, mask) -> None:
        self.png = png
        self.mask = mask
        self.predictor = None


    def buildmodel(self, path_to_pt, path_to_yaml, path_to_fine_tune):
        FINE_TUNED_MODEL_WEIGHTS = path_to_fine_tune
        sam2_checkpoint = path_to_pt
        model_cfg = path_to_yaml
        sam2_model = build_sam2(model_cfg, sam2_checkpoint, device="cuda")
        self.predictor = SAM2ImagePredictor(sam2_model)
        self.predictor.model.load_state_dict(torch.load(FINE_TUNED_MODEL_WEIGHTS))

    def predict(self):
        image, mask = self.read_image(self.png, self.mask)
        num_samples = 30  # Number of points per segment to sample
        input_points = self.get_points(mask, num_samples)
        with torch.no_grad():
            self.predictor.set_image(image)
            masks, scores, logits = self.predictor.predict(
                point_coords=input_points,
                point_labels=np.ones([input_points.shape[0], 1]))
        np_masks = np.array(masks[:, 0])
        np_scores = scores[:, 0]
        sorted_masks = np_masks[np.argsort(np_scores)][::-1]
        np_masks = np.array(masks[:, 0])
        np_scores = scores[:, 0]
        sorted_masks = np_masks[np.argsort(np_scores)][::-1]
        seg_map = np.zeros_like(sorted_masks[0], dtype=np.uint8)
        occupancy_mask = np.zeros_like(sorted_masks[0], dtype=bool)
        for i in range(sorted_masks.shape[0]):
            mask = sorted_masks[i]
            if (mask * occupancy_mask).sum() / mask.sum() > 0.15:
                continue
            mask_bool = mask.astype(bool)
            mask_bool[occupancy_mask] = False  # Set overlapping areas to False in the mask
            seg_map[mask_bool] = i + 1  # Use boolean mask to index seg_map
            occupancy_mask[mask_bool] = True  # Update occupancy_mask
        return seg_map


    @classmethod
    def read_image(cls, image_path, mask_path):  # read and resize image and mask
        img = cv2.imread(image_path)[..., ::-1]  # Convert BGR to RGB
        mask = cv2.imread(mask_path, 0)
        r = np.min([1024 / img.shape[1], 1024 / img.shape[0]])
        img = cv2.resize(img, (int(img.shape[1] * r), int(img.shape[0] * r)))
        mask = cv2.resize(mask, (int(mask.shape[1] * r), int(mask.shape[0] * r)), interpolation=cv2.INTER_NEAREST)
        return img, mask
    
    @classmethod
    def get_points(cls, mask, num_points):  # Sample points inside the input mask
        points = []
        coords = np.argwhere(mask > 0)
        for i in range(num_points):
            yx = np.array(coords[np.random.randint(len(coords))])
            points.append([[yx[1], yx[0]]])
        return np.array(points)
