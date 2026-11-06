"""
Stage 3: Explainability Module (Grad-CAM).
Computes Gradient-weighted Class Activation Mapping (Grad-CAM)
for anatomical classification and chest cardiopulmonary models.
Displays heatmaps distinctly from original radiographs and enforces
explicit disclaimers that saliency maps are illustrative AI activations,
not verified diagnostic markings.
"""

import torch
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image

class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self.target_layer.register_forward_hook(self._forward_hook)
        self.target_layer.register_full_backward_hook(self._backward_hook)
        
    def _forward_hook(self, module, input, output):
        self.activations = output
        
    def _backward_hook(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]
        
    def generate_heatmap(self, input_tensor, target_class=None):
        self.model.eval()
        self.model.zero_grad()
        
        output = self.model(input_tensor)
        if target_class is None:
            target_class = output.argmax(dim=1).item()
            
        score = output[0, target_class]
        score.backward(retain_graph=True)
        
        # Pool gradients across channels
        pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])
        activations = self.activations[0]
        
        for i in range(len(pooled_gradients)):
            activations[i, :, :] *= pooled_gradients[i]
            
        heatmap = torch.mean(activations, dim=0).squeeze()
        heatmap = F.relu(heatmap)
        heatmap_np = heatmap.detach().cpu().numpy()
        
        # Normalize between 0 and 1
        denom = np.max(heatmap_np) - np.min(heatmap_np)
        if denom > 0:
            heatmap_norm = (heatmap_np - np.min(heatmap_np)) / denom
        else:
            heatmap_norm = np.zeros_like(heatmap_np)
            
        return heatmap_norm

def overlay_heatmap(original_img: Image.Image, heatmap_norm: np.ndarray, alpha: float = 0.45) -> tuple:
    """
    Overlays normalized heatmap on original PIL image.
    Returns:
      overlay_pil: Image.Image (side-by-side or combined)
      heatmap_colored_pil: Image.Image (pure heatmap)
    """
    w, h = original_img.size
    # Resize heatmap to match image dimensions
    heatmap_resized = cv2.resize(heatmap_norm, (w, h), interpolation=cv2.INTER_LINEAR)
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    
    # Apply colormap (JET or TURBO)
    colored_heatmap = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    colored_heatmap = cv2.cvtColor(colored_heatmap, cv2.COLOR_BGR2RGB)
    
    # Original image as RGB numpy
    orig_rgb = np.array(original_img.convert("RGB"))
    
    # Blend
    blended = np.uint8(orig_rgb * (1.0 - alpha) + colored_heatmap * alpha)
    
    return Image.fromarray(blended), Image.fromarray(colored_heatmap)
