"""
Generates high-fidelity demonstration images for testing:
1. Chest X-Rays (Normal and Pneumonia with focal consolidation)
2. Brain MRIs (Normal and Focal tumor mass effect)
3. Medical Prescriptions (Formatted clinic layout with typed and cursive text)
4. Unsupported Non-Medical Images (Color photographic scenery / nature)
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

def create_chest_xray(filename, is_pneumonia=False):
    w, h = 512, 512
    # Base radiograph background
    img = np.zeros((h, w), dtype=np.float32)

    # Anatomic chest geometry: ribs and spine
    y, x = np.ogrid[:h, :w]
    # Mediastinum and spine (vertical dense opacity in center)
    spine = np.exp(-((x - w/2)**2) / (2 * 28**2)) * 140
    # Heart silhouette (shifted left, which is viewer's right)
    heart = np.exp(-((x - (w/2 + 35))**2 / (2 * 45**2) + (y - (h/2 + 40))**2 / (2 * 50**2))) * 110
    # Diaphragm domes
    diaphragm_left = np.exp(-((x - w*0.3)**2 / (2 * 80**2) + (y - h*0.82)**2 / (2 * 60**2))) * 180
    diaphragm_right = np.exp(-((x - w*0.7)**2 / (2 * 80**2) + (y - h*0.85)**2 / (2 * 60**2))) * 180

    # Lung fields (radiolucent = darker)
    lung_field_l = np.exp(-((x - w*0.32)**2 / (2 * 55**2) + (y - h*0.52)**2 / (2 * 90**2))) * 130
    lung_field_r = np.exp(-((x - w*0.68)**2 / (2 * 55**2) + (y - h*0.50)**2 / (2 * 85**2))) * 130

    # Thoracic rib cage arcs
    ribs = np.zeros((h, w), dtype=np.float32)
    for ry in range(120, 420, 36):
        rib_arc = np.sin((x / float(w)) * np.pi) * 35
        dist = np.abs((y - ry) - rib_arc)
        ribs += np.exp(-(dist**2) / (2 * 4.0**2)) * 30

    base_cxr = spine + heart + diaphragm_left + diaphragm_right + ribs + 45
    # Subtract lung lucency
    base_cxr = np.clip(base_cxr - lung_field_l * 0.45 - lung_field_r * 0.45, 10, 240)

    if is_pneumonia:
        # Add focal pneumonic consolidation in right lower lobe
        consolidation = np.exp(-((x - w*0.70)**2 / (2 * 32**2) + (y - h*0.58)**2 / (2 * 38**2))) * 125
        base_cxr = np.clip(base_cxr + consolidation, 10, 250)

    # Add realistic radiographic grain / noise
    noise = np.random.normal(0, 4.0, (h, w))
    final_np = np.clip(base_cxr + noise, 0, 255).astype(np.uint8)

    # Save 3-channel RGB JPEG
    rgb_img = Image.fromarray(np.stack([final_np]*3, axis=-1))
    rgb_img.save(filename, quality=94)
    print(f"Generated CXR: {filename}")

def create_brain_mri(filename, has_tumor=False):
    w, h = 512, 512
    img = np.zeros((h, w), dtype=np.float32)
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2

    # Oval skull contour
    dist_skull = ((x - cx)**2) / (180**2) + ((y - cy)**2) / (210**2)
    brain_mask = dist_skull <= 1.0
    skull_bone = (dist_skull > 0.92) & (dist_skull <= 1.0)

    # Brain parenchyma background
    parenchyma = np.where(brain_mask, 110.0, 0.0)

    # Ventricular system (bilateral butterfly shape in center, CSF is dark on T1)
    ventricle_l = np.exp(-((x - (cx - 22))**2 / (2 * 12**2) + (y - cy)**2 / (2 * 35**2))) * 80
    ventricle_r = np.exp(-((x - (cx + 22))**2 / (2 * 12**2) + (y - cy)**2 / (2 * 35**2))) * 80
    parenchyma = np.clip(parenchyma - ventricle_l - ventricle_r, 0, 255)

    # Gyri / sulcal texture
    sulci = (np.sin(x / 6.0) * np.cos(y / 6.0)) * 14.0
    parenchyma = np.where(brain_mask, np.clip(parenchyma + sulci, 20, 230), 0.0)

    # Skull bone hyperintensity
    img = np.where(skull_bone, 220.0, parenchyma)

    if has_tumor:
        # Add focal hyperintense enhancing mass lesion with surrounding edema
        tx, ty = cx + 65, cy - 40
        tumor_core = np.exp(-((x - tx)**2 / (2 * 24**2) + (y - ty)**2 / (2 * 22**2))) * 140
        edema = np.exp(-((x - tx)**2 / (2 * 45**2) + (y - ty)**2 / (2 * 40**2))) * 50
        img = np.where(brain_mask, np.clip(img + tumor_core + edema, 0, 255), img)

    noise = np.random.normal(0, 3.0, (h, w))
    final_np = np.clip(img + noise, 0, 255).astype(np.uint8)

    rgb_img = Image.fromarray(np.stack([final_np]*3, axis=-1))
    rgb_img.save(filename, quality=94)
    print(f"Generated MRI: {filename}")

def create_prescription_image(filename):
    w, h = 800, 1000
    img = Image.new("RGB", (w, h), color=(253, 253, 250)) # Off-white medical prescription paper
    draw = ImageDraw.Draw(img)

    # Blue header band
    draw.rectangle([(0, 0), (w, 140)], fill=(16, 42, 67)) # Primary Navy #102A43
    draw.rectangle([(0, 140), (w, 146)], fill=(13, 148, 136)) # Teal bar #0D9488

    # Clinic title and logo text
    draw.text((40, 30), "ST. JUDE MEMORIAL CLINIC & DIAGNOSTICS", fill=(255, 255, 255))
    draw.text((40, 65), "Department of Internal Medicine & Pulmonology | Reg # MD-2024-8172", fill=(204, 251, 241))
    draw.text((40, 95), "Phone: (555) 234-8900 | 742 Evergreen Healthcare Way, Suite 400", fill=(148, 163, 184))

    # Patient info box
    draw.rectangle([(40, 170), (w - 40, 250)], outline=(226, 232, 240), width=2, fill=(248, 250, 252))
    draw.text((60, 185), "Patient Name: Eleanor Vance            Age / Gender: 42Y / Female", fill=(16, 42, 67))
    draw.text((60, 215), "Date: 05-Nov-2026                       Rx Ref: RX-2026-9042-EV", fill=(100, 116, 139))

    # Rx symbol
    draw.text((50, 280), "Rx", fill=(13, 148, 136))

    # Prescription items
    items = [
        "1. Amoxicillin 500mg - 1 capsule TID (three times daily) x 7 days [After food]",
        "2. Paracetamol 650mg - 1 tablet SOS (as needed for body pain/fever) x 3 days",
        "3. Cetirizine 10mg - 1 tablet OD (once daily at bedtime) x 5 days",
        "4. Pantoprazole 40mg - 1 tablet OD before breakfast x 7 days",
    ]

    y_pos = 340
    for it in items:
        draw.text((80, y_pos), it, fill=(16, 42, 67))
        y_pos += 60

    # Clinical advice
    draw.line([(50, y_pos + 40), (w - 50, y_pos + 40)], fill=(226, 232, 240), width=1)
    draw.text((60, y_pos + 60), "Clinical Advice & Follow-up Instructions:", fill=(16, 42, 67))
    draw.text((80, y_pos + 95), "- Maintain adequate oral hydration (2.5L water daily).", fill=(100, 116, 139))
    draw.text((80, y_pos + 125), "- Complete full 7-day antibiotic course even if symptoms resolve early.", fill=(100, 116, 139))
    draw.text((80, y_pos + 155), "- Follow up in OPD after 7 days or sooner if fever spikes > 101F.", fill=(100, 116, 139))

    # Doctor signature
    draw.text((w - 280, h - 120), "Dr. Kenneth Vance, MD", fill=(16, 42, 67))
    draw.text((w - 280, h - 95), "Internal Medicine Specialist", fill=(100, 116, 139))
    draw.line([(w - 290, h - 130), (w - 50, h - 130)], fill=(13, 148, 136), width=2)

    img.save(filename, quality=95)
    print(f"Generated Prescription: {filename}")

def create_unsupported_photo(filename):
    w, h = 512, 512
    # Colorful sunset landscape photo (definitely not medical)
    img = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        ratio = y / float(h)
        # Red/Orange sky transitioning to blue sea/green trees
        r = int(255 * (1.0 - ratio * 0.5))
        g = int(120 * (1.0 - ratio * 0.3) + 100 * ratio)
        b = int(40 * (1.0 - ratio) + 220 * ratio)
        img[y, :] = [r, g, b]

    Image.fromarray(img).save(filename, quality=92)
    print(f"Generated Unsupported Photo: {filename}")

if __name__ == "__main__":
    os.makedirs("sample_data/chest_xray", exist_ok=True)
    os.makedirs("sample_data/brain_mri", exist_ok=True)
    os.makedirs("sample_data/prescriptions", exist_ok=True)
    os.makedirs("sample_data/unsupported", exist_ok=True)

    create_chest_xray("sample_data/chest_xray/cxr_normal.jpg", is_pneumonia=False)
    create_chest_xray("sample_data/chest_xray/cxr_pneumonia.jpg", is_pneumonia=True)
    create_brain_mri("sample_data/brain_mri/mri_normal.jpg", has_tumor=False)
    create_brain_mri("sample_data/brain_mri/mri_glioma.jpg", has_tumor=True)
    create_prescription_image("sample_data/prescriptions/sample_prescription.jpg")
    create_unsupported_photo("sample_data/unsupported/landscape_photo.jpg")

