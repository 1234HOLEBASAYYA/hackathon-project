import torch
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image
import base64
import io


class GradCAM:
    """
    Gradient-weighted Class Activation Mapping (Grad-CAM)
    Targeted for ResNet architectures (specifically target layer: model.layer4).
    """
    def __init__(self, model, target_layer=None):
        self.model = model
        self.model.eval()

        if target_layer is None:
            # Default to the last convolutional block in ResNet
            self.target_layer = self.model.layer4[-1]
        else:
            self.target_layer = target_layer

        self.gradients = None
        self.activations = None
        self._hooks = []
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        self._hooks.append(self.target_layer.register_forward_hook(forward_hook))
        self._hooks.append(self.target_layer.register_full_backward_hook(backward_hook))

    def remove_hooks(self):
        for hook in self._hooks:
            hook.remove()
        self._hooks.clear()

    def generate(self, input_tensor, target_class=None):
        """
        Generate Grad-CAM heatmap for a given input tensor.
        input_tensor: shape (1, 3, H, W)
        target_class: integer index (0 for NORMAL, 1 for PNEUMONIA), or None to use predicted class
        """
        self.model.zero_grad()
        output = self.model(input_tensor)

        if target_class is None:
            target_class = output.argmax(dim=1).item()

        # Score for target class
        score = output[0, target_class]
        score.backward()

        # Gradients: (1, C, H, W)
        # Global average pool the gradients over spatial dimensions (H, W)
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)  # (1, C, 1, 1)

        # Weighted combination of activation maps
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)  # (1, 1, H, W)
        cam = F.relu(cam)  # Apply ReLU (we only care about positive influences)

        # Upsample to match input tensor spatial size
        _, _, H, W = input_tensor.shape
        cam = F.interpolate(cam, size=(H, W), mode="bilinear", align_corners=False)
        cam = cam.squeeze().cpu().numpy()

        # Normalize to [0, 1]
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max - cam_min > 1e-8:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        return cam, target_class, output

    def overlay_heatmap(self, original_image, heatmap, alpha=0.45, colormap=cv2.COLORMAP_JET):
        """
        Overlays the Grad-CAM heatmap onto the original image.
        original_image: PIL Image or RGB numpy array (H, W, 3)
        heatmap: 2D numpy array (H, W) with values in [0, 1]
        """
        if isinstance(original_image, Image.Image):
            orig_np = np.array(original_image.convert("RGB"))
        else:
            orig_np = original_image.copy()

        H, W = orig_np.shape[:2]
        heatmap_resized = cv2.resize(heatmap, (W, H))

        # Convert to uint8 (0-255) and apply colormap
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_color = cv2.applyColorMap(heatmap_uint8, colormap)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

        # Blend
        overlay = np.float32(heatmap_color) * alpha + np.float32(orig_np) * (1 - alpha)
        overlay = np.clip(overlay, 0, 255).astype(np.uint8)

        # Find high activation bounding boxes (Region of Interest / ROI)
        roi_boxes = []
        _, thresh = cv2.threshold(heatmap_uint8, int(255 * 0.65), 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area > (H * W * 0.02):  # Filter out tiny noise spots (>2% area)
                x, y, w, h = cv2.boundingRect(c)
                roi_boxes.append({"x": int(x), "y": int(y), "width": int(w), "height": int(h)})

        return overlay, heatmap_color, roi_boxes


def encode_image_to_base64(img_np):
    """Encodes a uint8 RGB numpy array to base64 data URI."""
    pil_img = Image.fromarray(img_np)
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"
