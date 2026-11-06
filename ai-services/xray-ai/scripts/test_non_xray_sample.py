from PIL import Image, ImageDraw
import os
from google import genai
import json

# Create a sample non-X-ray color photo (e.g. colorful geometric icon/drawing)
img = Image.new("RGB", (400, 400), color=(50, 150, 240))
draw = ImageDraw.Draw(img)
draw.ellipse([100, 100, 300, 300], fill=(240, 200, 50), outline=(200, 50, 50), width=8)
draw.rectangle([50, 320, 350, 380], fill=(50, 200, 80))
test_path = "backend/static/uploads/non_xray_test.png"
img.save(test_path)

api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY_XRAY")
client = genai.Client(api_key=api_key)
uploaded = client.files.upload(file=test_path)

prompt = """
You are a senior radiological imaging AI.
FIRST: Carefully verify whether this image is an authentic medical projection radiograph (X-ray, fluoroscopy, or radiographic study).
If this image is NOT a medical X-ray (e.g. it is a photograph of a person, animal, car, nature, artwork, drawing, cartoon, screenshot, document, or non-medical graphic):
You MUST set "is_radiograph": false and return JSON:
{
  "is_radiograph": false,
  "detected_image_type": string (e.g. "Color illustration/drawing", "Photograph of a cat", "Selfie", "Digital graphic"),
  "rejection_reason": string explaining clearly that this is not a medical X-ray and no skeletal or thoracic pathology can be evaluated.
}

Only if it IS an authentic medical X-ray, set "is_radiograph": true and return the anatomical_region, is_abnormal, primary_diagnosis, etc.
"""

res = client.interactions.create(
    model='gemini-3.5-flash-lite',
    input=[
        {'type': 'text', 'text': prompt},
        {'type': 'image', 'uri': uploaded.uri, 'mime_type': 'image/png'}
    ]
)
print("Gemini Non-X-Ray Output:\n", res.output_text)
