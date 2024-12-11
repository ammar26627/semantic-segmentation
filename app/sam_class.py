import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
import numpy as np
import torch
from PIL import Image
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
import cv2

class SAM2:
    sam2_checkpoint = "./sam2.1_hiera_large.pt"
    model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml" 
    
    def __init__(self):
        if torch.cuda.is_available():
            self.evice = torch.device("cuda")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
            print(f"using device: {device}")

        if self.device.type == "cuda":
            # use bfloat16 for the entire notebook
            torch.autocast("cuda", dtype=torch.bfloat16).__enter__()
            # turn on tfloat32 for Ampere GPUs (https://pytorch.org/docs/stable/notes/cuda.html#tensorfloat-32-tf32-on-ampere-devices)
            if torch.cuda.get_device_properties(0).major >= 8:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
        elif self.device.type == "mps":
                print(
                    "\nSupport for MPS devices is preliminary. SAM 2 is trained with CUDA and might "
                    "give numerically different outputs and sometimes degraded performance on MPS. "
                    "See e.g. https://github.com/pytorch/pytorch/issues/84936 for a discussion."
                )
                
    def predict(self, image, num_point, labels, threshold):
        sam2_model = build_sam2(self.model_cfg, self.sam2_checkpoint, device=self.device)
        image = self.increased_contract_with_covairance_normalized(image, threshold)
        predictor = SAM2ImagePredictor(sam2_model)
        
        predictor.set_image(image)
        
        input_point = np.array([[*num_point]])
        input_label = np.array([labels])
        print(predictor._features["image_embed"].shape, predictor._features["image_embed"][-1].shape)
        masks, scores, logits = predictor.predict(
        point_coords=input_point,
        point_labels=input_label,
        multimask_output=True,
        )
        sorted_ind = np.argsort(scores)[::-1]
        masks = masks[sorted_ind]
        scores = scores[sorted_ind]
        logits = logits[sorted_ind]
        print(masks.shape, scores.shape, logits.shape)
        print(masks, scores, logits)
        return masks
    
@staticmethod
def increase_contrast_with_covariance_normalized(image, factor=1.5):

    b, g, r = cv2.split(image)
    pixel_matrix = np.stack((b.flatten(), g.flatten(), r.flatten()), axis=1)
    covariance_matrix = np.cov(pixel_matrix, rowvar=False)
    variances = np.diag(covariance_matrix)
    std_devs = np.sqrt(variances)
    b = ((b - b.mean()) / std_devs[0]) * factor * std_devs[0] + b.mean()
    g = ((g - g.mean()) / std_devs[1]) * factor * std_devs[1] + g.mean()
    r = ((r - r.mean()) / std_devs[2]) * factor * std_devs[2] + r.mean()

    # Clip values to the valid range [0, 1]
    b = np.clip(b, 0, 1)
    g = np.clip(g, 0, 1)
    r = np.clip(r, 0, 1)

    # Merge channels back into an image
    enhanced_image = cv2.merge((b, g, r))
    
    return enhanced_image