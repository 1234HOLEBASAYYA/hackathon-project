import os
from google import genai
import json

api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY_XRAY")
client = genai.Client(api_key=api_key)
prompt = """
You are a radiological image classifier.
Inspect whether the given input is an authentic medical radiograph (X-ray, fluoroscopy, CT projection, or DICOM radiograph) or a non-medical photograph/graphic.
If the input is NOT an X-ray (e.g. photo of an animal, human face, selfie, car, landscape, graphic, document, food):
Return JSON:
{
  "is_radiograph": false,
  "detected_image_type": "Photograph of a dog",
  "reason": "Not a medical radiograph displaying bone or tissue radiodensity."
}
"""
res = client.interactions.create(
    model='gemini-3.5-flash-lite',
    input=[{'type': 'text', 'text': prompt}]
)
print("Output:\n", res.output_text)
