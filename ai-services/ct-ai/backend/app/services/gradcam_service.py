import torch
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image
import base64
import io


class GradCAMService:
    """
    Grad-CAM service for visualizing explainable diagnostic heatmaps.
    Hooks into ResNet18's layer4 to extract feature activations and gradients.
    """
    def __init__(self, model, target_layer=None):
        self.model = model
        self.model.eval()

        if target_layer is None:
            # Use layer4[-1] of ResNet18
            if hasattr(self.model, "get_target_layer"):
                self.target_layer = self.model.get_target_layer()
            elif hasattr(self.model, "layer4"):
                self.target_layer = self.model.layer4[-1]
            elif hasattr(self.model, "model") and hasattr(self.model.model, "layer4"):
                self.target_layer = self.model.model.layer4[-1]
            else:
                raise AttributeError("Unable to locate layer4 in model for Grad-CAM.")
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

    def generate_heatmap(self, input_tensor, target_class=None):
        """
        Calculates 2D normalized Grad-CAM heatmap array in range [0, 1].
        """
        self.model.zero_grad()
        output = self.model(input_tensor)

        if target_class is None:
            target_class = output.argmax(dim=1).item()

        score = output[0, target_class]
        score.backward()

        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)
        cam = F.relu(cam)

        _, _, H, W = input_tensor.shape
        cam = F.interpolate(cam, size=(H, W), mode="bilinear", align_corners=False)
        cam = cam.squeeze().cpu().numpy()

        cam_min, cam_max = cam.min(), cam.max()
        if cam_max - cam_min > 1e-8:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        return cam, target_class

    def create_visualization(self, original_img: Image.Image, cam_heatmap: np.ndarray, alpha=0.45):
        """
        Generates overlaid image, pure heatmap, detected ROIs, and opacity score.
        """
        orig_np = np.array(original_img.convert("RGB"))
        H, W = orig_np.shape[:2]

        heatmap_resized = cv2.resize(cam_heatmap, (W, H))
        heatmap_uint8 = np.uint8(255 * heatmap_resized)

        # Apply JET colormap
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

        # Alpha blending
        overlay = np.float32(heatmap_color) * alpha + np.float32(orig_np) * (1 - alpha)
        overlay = np.clip(overlay, 0, 255).astype(np.uint8)

        # Region of Interest (ROI) contours for pneumonia consolidation areas
        rois = []
        _, thresh = cv2.threshold(heatmap_uint8, int(255 * 0.60), 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area > (H * W * 0.015):
                x, y, w, h = cv2.boundingRect(c)
                rois.append({
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h),
                    "relative_x": round(x / W, 3),
                    "relative_y": round(y / H, 3),
                    "relative_width": round(w / W, 3),
                    "relative_height": round(h / H, 3)
                })

        # Opacity score (mean intensity of active regions)
        active_pixels = cam_heatmap[cam_heatmap > 0.5]
        opacity_score = float(active_pixels.mean()) if len(active_pixels) > 0 else 0.0

        return {
            "overlay_b64": self._to_base64(overlay),
            "heatmap_b64": self._to_base64(heatmap_color),
            "rois": rois,
            "opacity_score": round(opacity_score, 4)
        }

    @staticmethod
    def _to_base64(arr_uint8: np.ndarray) -> str:
        pil_img = Image.fromarray(arr_uint8)
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
