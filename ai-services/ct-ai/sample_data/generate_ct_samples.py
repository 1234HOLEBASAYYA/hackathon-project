import os
from PIL import Image, ImageDraw
import numpy as np

def create_chest_ct(filename, has_nodule=True):
    w, h = 512, 512
    img = np.zeros((h, w), dtype=np.float32)
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2

    # Thoracic body contour (oval)
    dist_body = ((x - cx)**2) / (210**2) + ((y - cy)**2) / (180**2)
    body_mask = dist_body <= 1.0
    chest_wall = (dist_body > 0.88) & (dist_body <= 1.0)

    # Subcutaneous fat & muscle
    tissue = np.where(body_mask, 80.0, 0.0)

    # Spine (posterior dense bone at bottom)
    spine = np.exp(-((x - cx)**2 / (2 * 18**2) + (y - (cy + 120))**2 / (2 * 20**2))) * 220
    sternum = np.exp(-((x - cx)**2 / (2 * 15**2) + (y - (cy - 140))**2 / (2 * 12**2))) * 180

    # Bilateral lungs (dark air attenuation / Hounsfield units ~ -800 to -500)
    lung_l = np.exp(-((x - (cx - 75))**2 / (2 * 55**2) + (y - cy)**2 / (2 * 90**2))) * 160
    lung_r = np.exp(-((x - (cx + 75))**2 / (2 * 55**2) + (y - cy)**2 / (2 * 90**2))) * 160

    # Mediastinum (central heart and great vessels)
    heart = np.exp(-((x - (cx + 15))**2 / (2 * 45**2) + (y - (cy - 10))**2 / (2 * 50**2))) * 120

    base_ct = tissue + spine + sternum + heart
    base_ct = np.where(body_mask, np.clip(base_ct - lung_l - lung_r, 10, 240), 0.0)
    base_ct = np.where(chest_wall, 160.0, base_ct)

    if has_nodule:
        # Solitary pulmonary nodule in right lung (viewer's left)
        nx, ny = cx - 85, cy + 25
        nodule = np.exp(-((x - nx)**2 / (2 * 12**2) + (y - ny)**2 / (2 * 12**2))) * 140
        base_ct = np.where(body_mask, np.clip(base_ct + nodule, 0, 255), base_ct)

    noise = np.random.normal(0, 3.5, (h, w))
    final_np = np.clip(base_ct + noise, 0, 255).astype(np.uint8)

    rgb_img = Image.fromarray(np.stack([final_np]*3, axis=-1))
    rgb_img.save(filename, quality=95)
    print(f"Generated CT Scan: {filename}")

if __name__ == "__main__":
    os.makedirs("sample_data/ct_scans", exist_ok=True)
    os.makedirs("frontend/public/sample_data/ct_scans", exist_ok=True)
    create_chest_ct("sample_data/ct_scans/ct_nodule.jpg", has_nodule=True)
    create_chest_ct("sample_data/ct_scans/ct_normal.jpg", has_nodule=False)
    create_chest_ct("frontend/public/sample_data/ct_scans/ct_nodule.jpg", has_nodule=True)
    create_chest_ct("frontend/public/sample_data/ct_scans/ct_normal.jpg", has_nodule=False)

