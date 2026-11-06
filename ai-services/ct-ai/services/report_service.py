"""
PDF Report Generation Service for MedVision-AI CT Scan Image Analyzer
Generates high-resolution, professional clinical reports adhering to medical
decision-support standards using ReportLab.
"""

import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from PIL import Image

REPORTS_DIR = Path("generated_reports")


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print 'Page X of Y' and confidential headers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Top Header Bar
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0284c7"))
        self.drawString(54, 755, "MEDVISION-AI • CLINICAL DECISION SUPPORT")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawRightString(558, 755, "AI-ASSISTED CT IMAGE ANALYSIS • CONFIDENTIAL")

        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.75)
        self.line(54, 747, 558, 747)

        # Bottom Footer Bar
        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#94a3b8"))
        self.drawString(54, 32, "Medical Disclaimer: AI decision support output only. Requires formal interpretation by a qualified radiologist.")
        self.drawRightString(558, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def get_scaled_report_image(image_path: str, max_width: float = 240, max_height: float = 220) -> Optional[RLImage]:
    """
    Calculates constrained dimensions for the uploaded CT scan image to fit elegantly into the PDF.
    """
    if not image_path or not os.path.exists(image_path):
        return None

    try:
        with Image.open(image_path) as img:
            w, h = img.size
            aspect = w / float(h)

            if w > max_width or h > max_height:
                if (max_width / aspect) <= max_height:
                    target_w = max_width
                    target_h = max_width / aspect
                else:
                    target_h = max_height
                    target_w = max_height * aspect
            else:
                target_w = float(w)
                target_h = float(h)

        return RLImage(image_path, width=target_w, height=target_h)
    except Exception:
        return None


def generate_pdf_report(
    report_data: Dict[str, Any],
    image_path: Optional[str] = None,
    output_dir: Optional[str] = None
) -> str:
    """
    Builds a professional multi-section PDF medical report from structured Gemini analysis.
    
    Returns the absolute path to the generated PDF.
    """
    target_dir = Path(output_dir) if output_dir else REPORTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    report_id = str(uuid.uuid4())[:8]
    pdf_filename = f"MedVision_Report_{report_id}.pdf"
    pdf_path = target_dir / pdf_filename

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Medical Styling
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )
    section_h1 = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#0369a1"),
        spaceBefore=10,
        spaceAfter=5
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b")
    )
    body_bold = ParagraphStyle(
        "BodyDarkBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0f172a")
    )
    badge_uncertain = ParagraphStyle(
        "BadgeUncertain",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#d97706")
    )
    disclaimer_style = ParagraphStyle(
        "DisclaimerText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#991b1b")
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("MedVision-AI — CT Image Analysis Report", title_style))
    gen_time = report_data.get("generated_at", "N/A")
    filename = report_data.get("filename", "CT_Scan_Image")
    model_name = report_data.get("model_used", "Gemini Clinical Vision")
    story.append(Paragraph(
        f"<b>Case File:</b> {filename} &nbsp;|&nbsp; <b>Analysis Timestamp:</b> {gen_time} &nbsp;|&nbsp; <b>AI Engine:</b> {model_name}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0284c7"), spaceAfter=10))

    # 2. Side-by-Side: Image and Image Information Table
    img_element = get_scaled_report_image(image_path)
    img_info = report_data.get("image_information", {})
    
    info_table_data = [
        [Paragraph("<b>Image Attribute</b>", body_bold), Paragraph("<b>Visual Observation</b>", body_bold)],
        [Paragraph("Image Type / Modality", body_style), Paragraph(str(img_info.get("image_type", "Indeterminate")), body_style)],
        [Paragraph("Image Dimensions", body_style), Paragraph(str(img_info.get("image_dimensions", "N/A")), body_style)],
        [Paragraph("Image Quality Assessment", body_style), Paragraph(str(img_info.get("image_quality", "Adequate")), body_style)],
    ]
    
    info_table = Table(info_table_data, colWidths=[130, 160])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    if img_element:
        # Layout image on the left, table on the right
        composite_data = [[img_element, info_table]]
        composite_table = Table(composite_data, colWidths=[200, 304])
        composite_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(composite_table)
    else:
        story.append(info_table)

    story.append(Spacer(1, 10))

    # 3. Visual Observations (Physical Image Evidence)
    story.append(Paragraph("A. Visible Anatomical & Density Observations", section_h1))
    visual_obs = report_data.get("visual_observations", [])
    if visual_obs:
        obs_rows = [
            [
                Paragraph("<b>Feature / Observation</b>", body_bold),
                Paragraph("<b>Visible Location</b>", body_bold),
                Paragraph("<b>Detailed Visual Appearance</b>", body_bold),
                Paragraph("<b>Status</b>", body_bold),
            ]
        ]
        for obs in visual_obs:
            obs_rows.append([
                Paragraph(str(obs.get("observation", "")), body_bold),
                Paragraph(str(obs.get("location", "Indeterminate")), body_style),
                Paragraph(str(obs.get("description", "")), body_style),
                Paragraph("Observed", body_style)
            ])
        obs_table = Table(obs_rows, colWidths=[120, 110, 214, 60])
        obs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(obs_table)
    else:
        story.append(Paragraph("No unusual gross visual opacities detected on screening view.", body_style))

    story.append(Spacer(1, 10))

    # 4. Potential Findings (Differential Considerations with uncertainty)
    story.append(Paragraph("B. Potential Clinical Considerations (Differential / Non-Definitive)", section_h1))
    pot_findings = report_data.get("potential_findings", [])
    if pot_findings:
        findings_rows = [
            [
                Paragraph("<b>Consideration</b>", body_bold),
                Paragraph("<b>Location</b>", body_bold),
                Paragraph("<b>Visual Correlation & Reasoning</b>", body_bold),
                Paragraph("<b>Certainty</b>", body_bold),
            ]
        ]
        for f in pot_findings:
            findings_rows.append([
                Paragraph(str(f.get("finding", "")), body_bold),
                Paragraph(str(f.get("location", "Indeterminate")), body_style),
                Paragraph(
                    f"{f.get('description', '')} <i>(Visual Basis: {f.get('supporting_visual_observation', 'Density contrast')})</i>",
                    body_style
                ),
                Paragraph("Uncertain", badge_uncertain)
            ])
        findings_table = Table(findings_rows, colWidths=[120, 100, 224, 60])
        findings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#fffbeb")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#fde68a")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(findings_table)
    else:
        story.append(Paragraph("No specific focal pathology identified requiring differential highlight.", body_style))

    story.append(Spacer(1, 10))

    # 5. Clinical Summary
    story.append(Paragraph("C. Image-Based Summary", section_h1))
    summary_text = report_data.get("summary", "Image-based screening completed.")
    story.append(Paragraph(summary_text, body_style))

    story.append(Spacer(1, 8))

    # 6. Technical Limitations & Review Recommendations
    recs = report_data.get("recommendations_for_review", [])
    limits = report_data.get("limitations", [])

    rec_elements = [Paragraph(f"• {r}", body_style) for r in recs]
    limit_elements = [Paragraph(f"• {l}", body_style) for l in limits]

    review_table_data = [
        [
            Paragraph("<b>Recommended Next Actions</b>", body_bold),
            Paragraph("<b>Study & System Limitations</b>", body_bold)
        ],
        [
            rec_elements,
            limit_elements
        ]
    ]
    review_table = Table(review_table_data, colWidths=[252, 252])
    review_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(KeepTogether(review_table))

    story.append(Spacer(1, 10))

    # 7. Medical Disclaimer Box
    disclaimer_box_data = [
        [
            Paragraph(
                "<b>CRITICAL MEDICAL DISCLAIMER:</b> "
                "This report was generated by an artificial intelligence decision-support model (MedVision-AI). "
                "It is strictly intended for educational and auxiliary diagnostic assistance and does NOT constitute "
                "a definitive medical diagnosis. A single static 2D image cannot replace a complete multi-slice volumetric CT study. "
                "All visual observations and clinical differentials MUST be reviewed and validated by a board-certified radiologist.",
                disclaimer_style
            )
        ]
    ]
    disclaimer_table = Table(disclaimer_box_data, colWidths=[504])
    disclaimer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#ef4444")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(KeepTogether(disclaimer_table))

    # Build document with custom canvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return str(pdf_path.resolve())
