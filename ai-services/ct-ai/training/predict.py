import os
import sys
import json
import torch
from PIL import Image

try:
    from training.config import (
        DEVICE, MODEL_SAVE_PATH, CLASS_MAPPING_PATH, RESULTS_DIR, TEST_DIR
    )
    from training.preprocessing import preprocess_image
    from training.gradcam import GradCAM
    from training.evaluate import load_model_for_eval
except ImportError:
    from config import (
        DEVICE, MODEL_SAVE_PATH, CLASS_MAPPING_PATH, RESULTS_DIR, TEST_DIR
    )
    from preprocessing import preprocess_image
    from gradcam import GradCAM
    from evaluate import load_model_for_eval


class ChestXRayInference:
    """Reusable, cached inference engine for Chest X-Ray Abnormality Detection."""
    def __init__(self, model_path=MODEL_SAVE_PATH, mapping_path=CLASS_MAPPING_PATH):
        self.device = DEVICE
        self.model = load_model_for_eval(model_path)
        self.gradcam = GradCAM(self.model)

        with open(mapping_path, "r") as f:
            mapping_data = json.load(f)
            self.idx_to_class = {int(k): v for k, v in mapping_data.get("idx_to_class", {0: "NORMAL", 1: "PNEUMONIA"}).items()}
            self.classes = mapping_data.get("classes", ["NORMAL", "PNEUMONIA"])

    def predict(self, image_source, generate_gradcam=True, alpha=0.45):
        """
        Runs inference on an image.
        Returns dictionary with predicted class, confidence, probabilities, and Grad-CAM data.
        """
        if isinstance(image_source, str) or hasattr(image_source, "read"):
            pil_img = Image.open(image_source).convert("RGB")
        elif isinstance(image_source, Image.Image):
            pil_img = image_source.convert("RGB")
        else:
            raise ValueError(f"Unsupported image type: {type(image_source)}")

        input_tensor = preprocess_image(pil_img).to(self.device)

        # Get logits and probabilities
        with torch.no_grad():
            logits = self.model(input_tensor)
            probs = torch.softmax(logits, dim=1).squeeze().cpu().numpy()

        pred_idx = int(probs.argmax())
        pred_class = self.idx_to_class.get(pred_idx, "UNKNOWN")
        confidence = float(probs[pred_idx])

        probabilities = {
            self.idx_to_class.get(i, f"Class {i}"): float(prob)
            for i, prob in enumerate(probs)
        }

        result = {
            "prediction": pred_class,
            "confidence": round(confidence, 4),
            "probabilities": {k: round(v, 4) for k, v in probabilities.items()},
            "is_abnormal": pred_class != "NORMAL"
        }

        if generate_gradcam:
            # Grad-CAM requires grad
            with torch.enable_grad():
                cam_heatmap, _, _ = self.gradcam.generate(input_tensor, target_class=pred_idx)
                overlay, raw_heatmap, rois = self.gradcam.overlay_heatmap(
                    pil_img, cam_heatmap, alpha=alpha
                )
                try:
                    from training.gradcam import encode_image_to_base64
                except ImportError:
                    from gradcam import encode_image_to_base64
                result["gradcam_overlay_b64"] = encode_image_to_base64(overlay)
                result["gradcam_raw_b64"] = encode_image_to_base64(raw_heatmap)
                result["roi_bounding_boxes"] = rois
                # Calculate abnormality opacity score (average activation in top 15% hottest pixels)
                top_values = cam_heatmap[cam_heatmap > 0.5]
                opacity_score = float(top_values.mean()) if len(top_values) > 0 else 0.0
                result["opacity_score"] = round(opacity_score, 4)

        return result


def find_sample_test_image():
    """Finds a valid sample chest X-ray image from the test set for verification."""
    for cls in ["PNEUMONIA", "NORMAL"]:
        cls_dir = os.path.join(str(TEST_DIR), cls)
        if os.path.exists(cls_dir):
            files = [f for f in os.listdir(cls_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            if files:
                return os.path.join(cls_dir, files[0]), cls
    return None, None


if __name__ == "__main__":
    test_img_path = None
    if len(sys.argv) > 1:
        test_img_path = sys.argv[1]
    else:
        sample_path, true_label = find_sample_test_image()
        test_img_path = sample_path
        print(f"Using test sample: {sample_path} (True label: {true_label})")

    if not test_img_path or not os.path.exists(test_img_path):
        print("No valid test image found.")
        sys.exit(1)

    service = ChestXRayInference()
    res = service.predict(test_img_path)
    print("\n--- INFERENCE RESULT ---")
    print(f"Predicted Class: {res['prediction']}")
    print(f"Confidence:      {res['confidence'] * 100:.2f}%")
    print(f"Probabilities:   {res['probabilities']}")
    print(f"Is Abnormal:     {res['is_abnormal']}")
    if "opacity_score" in res:
        print(f"Opacity Score:   {res['opacity_score']}")
    if "roi_bounding_boxes" in res:
        print(f"ROIs Detected:   {len(res['roi_bounding_boxes'])}")
