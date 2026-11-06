"""
Visualizer and Clinical Report Generator.
Features:
  1. Side-by-side visualization: Original radiograph beside annotated AI damage overlay.
  2. Bounding box rendering with bone identification tags and confidence badges.
  3. PDF clinical summary report generator (educational / non-diagnostic).
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def draw_damage_annotations(original_img: Image.Image, findings: list, bone_structures: list = None) -> Image.Image:
    """
    Renders high-visibility bounding boxes and clinical tags on a copy of the radiograph.
    """
    annotated = original_img.convert("RGB").copy()
    draw = ImageDraw.Draw(annotated)
    w, h = annotated.size
    
    # Try loading a readable default font
    try:
        font = ImageFont.truetype("arial.ttf", size=max(14, int(h * 0.025)))
        small_font = ImageFont.truetype("arial.ttf", size=max(11, int(h * 0.018)))
    except Exception:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        
    for idx, f in enumerate(findings):
        bbox = f.get("bbox_pixels")
        if not bbox or len(bbox) != 4:
            continue
            
        x1, y1, x2, y2 = bbox
        conf = f.get("confidence", 0.0)
        bone = f.get("affected_bone", "Unspecified bone")
        label = f.get("finding_type", "Cortical Discontinuity")
        
        # Color: Red/Crimson for high-confidence fracture, Amber for moderate
        box_color = (220, 38, 38) if conf >= 0.70 else (217, 119, 6)
        
        # Draw bounding rectangle with thickness 3
        for t in range(3):
            draw.rectangle([x1 - t, y1 - t, x2 + t, y2 + t], outline=box_color)
            
        # Truncate label if too long for badge
        short_label = label[:35] + "..." if len(label) > 35 else label
        badge_text = f" {short_label} ({conf*100:.1f}%) | {bone} "
        try:
            bbox_text = draw.textbbox((x1, max(0, y1 - 24)), badge_text, font=small_font)
            bw = bbox_text[2] - bbox_text[0]
            bh = bbox_text[3] - bbox_text[1]
            badge_x1 = max(2, min(x1, w - bw - 4))
            badge_x2 = min(w - 2, badge_x1 + bw + 6)
            badge_y1 = max(2, y1 - bh - 6)
            badge_y2 = max(bh + 8, y1)
            draw.rectangle([badge_x1, badge_y1, badge_x2, badge_y2], fill=box_color)
            draw.text((badge_x1 + 3, badge_y1 + 2), badge_text, fill=(255, 255, 255), font=small_font)
        except Exception:
            draw.text((x1, max(0, y1 - 15)), badge_text, fill=box_color, font=small_font)
            
    return annotated

def create_side_by_side_specimen(original_img: Image.Image, annotated_img: Image.Image) -> Image.Image:
    """
    Creates an editorial side-by-side comparison:
    [ Left: Original Radiograph ] [ Right: AI Damage Localization ]
    """
    orig = original_img.convert("RGB")
    annot = annotated_img.convert("RGB")
    
    # Normalize heights
    target_h = 600
    w1 = int(orig.width * (target_h / orig.height))
    w2 = int(annot.width * (target_h / annot.height))
    
    orig_resized = orig.resize((w1, target_h), Image.Resampling.LANCZOS)
    annot_resized = annot.resize((w2, target_h), Image.Resampling.LANCZOS)
    
    # Combined canvas with 24px gutter and header space
    header_h = 48
    canvas_w = w1 + w2 + 24
    canvas_h = target_h + header_h + 30
    
    canvas = Image.new("RGB", (canvas_w, canvas_h), color=(248, 250, 252)) # Slate-50
    draw = ImageDraw.Draw(canvas)
    
    # Paste images
    canvas.paste(orig_resized, (0, header_h))
    canvas.paste(annot_resized, (w1 + 24, header_h))
    
    # Header labels
    try:
        font = ImageFont.truetype("arial.ttf", size=16)
    except Exception:
        font = ImageFont.load_default()
        
    draw.text((12, 14), "PRIMARY RADIOGRAPH (UNPROCESSED)", fill=(15, 23, 42), font=font)
    draw.text((w1 + 36, 14), "AI DAMAGE LOCALIZATION OVERLAY", fill=(185, 28, 28), font=font)
    
    return canvas

def generate_pdf_report(
    output_pdf_path: str,
    analysis_result: dict,
    specimen_image_path: str
):
    """
    Generates a professional downloadable PDF medical analysis summary report.
    """
    doc = SimpleDocTemplate(output_pdf_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569')
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#DC2626')
    )
    
    # 1. Header
    story.append(Paragraph("MULTI-REGION X-RAY ANALYSIS AI PLATFORM", title_style))
    story.append(Paragraph("AI-Assisted Diagnostic Screening Summary & Anatomical Damage Report", subtitle_style))
    story.append(Spacer(1, 14))
    
    # 2. Metadata Table
    reg = analysis_result.get("anatomical_region", "Unknown").upper()
    model_name = analysis_result.get("model_name", "Multi-Region Neural Pipeline")
    conf = analysis_result.get("confidence", 0.0)
    abnormal = analysis_result.get("is_abnormal", False)
    
    meta_data = [
        ["Identified Region:", reg, "Analysis Status:", "ABNORMALITY DETECTED" if abnormal else "NORMAL / NO ACUTE LESION"],
        ["Inference Pipeline:", model_name, "Overall Confidence:", f"{conf*100:.1f}%"],
        ["Report Timestamp:", analysis_result.get("timestamp", "N/A"), "Pediatric Assessment:", str(analysis_result.get("is_pediatric", False))]
    ]
    meta_table = Table(meta_data, colWidths=[120, 160, 120, 140])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTNAME', (3,0), (3,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1E293B')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))
    
    # 3. Side-by-side Visual Specimen
    if os.path.exists(specimen_image_path):
        img_element = RLImage(specimen_image_path, width=540, height=270)
        story.append(img_element)
        story.append(Spacer(1, 14))
        
    # 4. Detected Findings Table
    story.append(Paragraph("<b>PRIMARY PREDICTED FINDINGS & DAMAGE LOCALIZATION:</b>", styles['Heading3']))
    findings = analysis_result.get("findings", [])
    if not findings:
        findings = [{"finding_type": "No acute fracture or focal consolidation", "affected_bone": "N/A", "confidence": conf, "location": "N/A"}]
        
    find_data = [["Finding Description", "Affected Bone", "Confidence", "Coordinates / Location"]]
    for f in findings:
        bbox_str = str(f.get("bbox_pixels", "N/A"))
        find_data.append([
            Paragraph(f.get("finding_type", "Cortical Disruption"), styles['Normal']),
            Paragraph(f.get("affected_bone", "N/A"), styles['Normal']),
            f"{f.get('confidence', 0.0)*100:.1f}%",
            bbox_str
        ])
        
    find_table = Table(find_data, colWidths=[180, 120, 90, 150])
    find_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(find_table)
    story.append(Spacer(1, 16))
    
    # 5. Regulatory & Clinical Disclaimer
    disclaimer_text = (
        "<b>CLINICAL SAFETY NOTICE & MEDICAL DISCLAIMER:</b> This report is generated by an experimental research AI prototype. "
        "It does NOT constitute a confirmed medical diagnosis or professional radiological interpretation. Saliency maps, "
        "bounding boxes, and confidence scores are probabilistic computer vision estimates. All radiographic assessments must "
        "be reviewed and verified by a licensed medical practitioner or certified radiologist."
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))
    
    doc.build(story)
    return output_pdf_path
