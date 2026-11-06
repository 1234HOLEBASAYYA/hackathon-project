"""Export module for prescription reports in PDF and CSV formats."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_prescription_csv(data: dict[str, Any]) -> str:
    """Generate RFC 4180 CSV representing all extracted and edited prescription fields."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Document Header
    writer.writerow(["PRESCRIPTION EXTRACTION & AUDIT REPORT"])
    writer.writerow(["Exported At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow(["Institution / Clinic", data.get("clinic_header") or "Not detected"])
    writer.writerow([
        "Clinical Verification Status",
        "CLINICALLY VERIFIED" if data.get("is_verified") else "UNVERIFIED - MANUAL CLINICAL REVIEW REQUIRED",
    ])
    writer.writerow([])

    # Doctor Information
    doctor = data.get("doctor", {})
    writer.writerow(["DOCTOR INFORMATION"])
    writer.writerow(["Doctor Name", doctor.get("name") or "Not detected"])
    writer.writerow(["Qualification", doctor.get("qualification") or "Not detected"])
    writer.writerow(["Specialization", doctor.get("specialization") or "Not detected"])
    writer.writerow(["Medical Reg. / Lic. #", doctor.get("registration_number") or "Not detected"])
    writer.writerow(["Clinic / Hospital", doctor.get("clinic_or_hospital") or "Not detected"])
    writer.writerow(["Contact Number", doctor.get("contact_number") or "Not detected"])
    writer.writerow([])

    # Patient Information
    patient = data.get("patient", {})
    writer.writerow(["PATIENT INFORMATION"])
    writer.writerow(["Patient Name", patient.get("name") or "Not detected"])
    writer.writerow(["Age", patient.get("age") or "Not detected"])
    writer.writerow(["Gender", patient.get("gender") or "Not detected"])
    writer.writerow(["Patient Address", patient.get("address") or "Not detected"])
    writer.writerow(["Prescription Date", patient.get("date") or "Not detected"])
    writer.writerow(["Patient ID / UHID", patient.get("patient_id") or "Not detected"])
    writer.writerow([])

    # Clinical Diagnosis & Advice
    writer.writerow(["CLINICAL FINDINGS"])
    writer.writerow(["Diagnosis", data.get("diagnosis") or "Not detected"])
    writer.writerow(["Medical Advice", data.get("advice") or "Not detected"])
    writer.writerow(["Follow-up Instructions", data.get("follow_up") or "Not detected"])
    writer.writerow([])

    # Prescribed Medications Table
    writer.writerow([
        "#",
        "Medicine Name",
        "Strength",
        "Dosage",
        "Frequency",
        "Duration",
        "Route",
        "Food Timing",
        "Special Instructions",
        "Confidence (%)",
        "Verification Status",
    ])

    medicines = data.get("medicines", [])
    for idx, med in enumerate(medicines, start=1):
        writer.writerow([
            idx,
            med.get("medicine_name", ""),
            med.get("strength") or "Not detected",
            med.get("dosage") or "Not detected",
            med.get("frequency") or "Not detected",
            med.get("duration") or "Not detected",
            med.get("route") or "Not detected",
            med.get("food_instructions") or "Not detected",
            med.get("special_instructions") or "Not detected",
            med.get("confidence", 0.0),
            "Unclear - Requires Verification" if med.get("is_unclear") else "Captured",
        ])

    return output.getvalue()


def generate_prescription_pdf(data: dict[str, Any], output_path: str | Path) -> Path:
    """Generate a clean, clinical PDF report with complete full-page prescription details."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(out),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=21,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=10,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=8,
        spaceAfter=4,
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )
    cell_text = ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Italic"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#94a3b8"),
        alignment=1,
    )

    story = []

    # Clinic Header if present
    clinic_h = data.get("clinic_header")
    if clinic_h and clinic_h != "Not detected":
        story.append(Paragraph(f"<b>{clinic_h}</b>", title_style))
        story.append(Paragraph("Prescription Extraction & Clinical Audit Document", subtitle_style))
    else:
        story.append(Paragraph("Medical Prescription Extraction Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", subtitle_style))

    # Verification Banner
    is_verified = bool(data.get("is_verified", False))
    if is_verified:
        banner_bg = colors.HexColor("#dcfce7")
        banner_fg = colors.HexColor("#166534")
        banner_text = "<b>&#x2714; CLINICALLY VERIFIED</b> &mdash; All extracted medications, patient details, and dosages have been verified by a human reviewer."
    else:
        banner_bg = colors.HexColor("#fef3c7")
        banner_fg = colors.HexColor("#92400e")
        banner_text = "<b>&#x26A0; UNVERIFIED EXTRACTION</b> &mdash; Pending human clinical review. Do not administer or dispense without manual prescription cross-reference."

    banner_table = Table(
        [[Paragraph(f"<font color='{banner_fg.hexval()}'>{banner_text}</font>", cell_text)]],
        colWidths=[540],
    )
    banner_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), banner_bg),
            ("BOX", (0, 0), (-1, -1), 1, banner_fg),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(banner_table)
    story.append(Spacer(1, 8))

    # Doctor and Patient Metadata Table
    doc_info = data.get("doctor", {})
    pat_info = data.get("patient", {})

    meta_data = [
        [
            Paragraph("<b>Doctor Information</b>", cell_bold),
            Paragraph("<b>Patient Information</b>", cell_bold),
        ],
        [
            Paragraph(f"<b>Name:</b> {doc_info.get('name') or 'Not detected'}", cell_text),
            Paragraph(f"<b>Name:</b> {pat_info.get('name') or 'Not detected'}", cell_text),
        ],
        [
            Paragraph(f"<b>Qualification:</b> {doc_info.get('qualification') or 'Not detected'}", cell_text),
            Paragraph(f"<b>Age / Gender:</b> {pat_info.get('age') or 'Not detected'} / {pat_info.get('gender') or 'Not detected'}", cell_text),
        ],
        [
            Paragraph(f"<b>Specialization:</b> {doc_info.get('specialization') or 'Not detected'}", cell_text),
            Paragraph(f"<b>Address:</b> {pat_info.get('address') or 'Not detected'}", cell_text),
        ],
        [
            Paragraph(f"<b>Reg / Lic #:</b> {doc_info.get('registration_number') or 'Not detected'}", cell_text),
            Paragraph(f"<b>Date:</b> {pat_info.get('date') or 'Not detected'}", cell_text),
        ],
        [
            Paragraph(f"<b>Clinic / Phone:</b> {doc_info.get('clinic_or_hospital') or 'Not detected'} ({doc_info.get('contact_number') or 'N/A'})", cell_text),
            Paragraph(f"<b>Patient ID:</b> {pat_info.get('patient_id') or 'Not detected'}", cell_text),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # Diagnosis & Clinical Advice
    diag_str = data.get("diagnosis")
    adv_str = data.get("advice")
    fol_str = data.get("follow_up")
    if any(x and x != "Not detected" for x in (diag_str, adv_str, fol_str)):
        clinical_data = [
            [
                Paragraph(f"<b>Diagnosis:</b> {diag_str or 'Not detected'}", cell_text),
                Paragraph(f"<b>Follow-up:</b> {fol_str or 'Not detected'}", cell_text),
            ],
            [
                Paragraph(f"<b>Medical Advice:</b> {adv_str or 'Not detected'}", cell_text),
                Paragraph("", cell_text),
            ],
        ]
        clin_table = Table(clinical_data, colWidths=[270, 270])
        clin_table.setStyle(
            TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(clin_table)
        story.append(Spacer(1, 8))

    # Medicines Table
    story.append(Paragraph("Prescribed Medications", section_heading))

    med_headers = [
        Paragraph("<b>#</b>", cell_bold),
        Paragraph("<b>Medicine</b>", cell_bold),
        Paragraph("<b>Strength</b>", cell_bold),
        Paragraph("<b>Dosage</b>", cell_bold),
        Paragraph("<b>Frequency</b>", cell_bold),
        Paragraph("<b>Duration</b>", cell_bold),
        Paragraph("<b>Route / Timing / Instructions</b>", cell_bold),
        Paragraph("<b>Status</b>", cell_bold),
    ]

    med_rows = [med_headers]
    medicines = data.get("medicines", [])
    for idx, med in enumerate(medicines, start=1):
        is_unc = bool(med.get("is_unclear"))
        name_str = med.get("medicine_name", "")
        if is_unc or name_str == "Unclear – Manual verification required":
            name_p = Paragraph(f"<font color='#dc2626'><b>{name_str}</b></font>", cell_text)
            status_p = Paragraph("<font color='#dc2626'><b>Unclear</b></font>", cell_text)
        else:
            name_p = Paragraph(f"<b>{name_str}</b>", cell_text)
            status_p = Paragraph(f"<font color='#16a34a'>{med.get('confidence', 0)}%</font>", cell_text)

        instr_parts = []
        if med.get("route") and med.get("route") != "Not detected":
            instr_parts.append(f"<b>Route:</b> {med.get('route')}")
        if med.get("food_instructions") and med.get("food_instructions") != "Not detected":
            instr_parts.append(f"<b>Timing:</b> {med.get('food_instructions')}")
        if med.get("special_instructions") and med.get("special_instructions") != "Not detected":
            instr_parts.append(f"<b>Note:</b> {med.get('special_instructions')}")
        instr_p = Paragraph("<br/>".join(instr_parts) if instr_parts else "Not detected", cell_text)

        med_rows.append([
            Paragraph(str(idx), cell_text),
            name_p,
            Paragraph(med.get("strength") or "Not detected", cell_text),
            Paragraph(med.get("dosage") or "Not detected", cell_text),
            Paragraph(med.get("frequency") or "Not detected", cell_text),
            Paragraph(med.get("duration") or "Not detected", cell_text),
            instr_p,
            status_p,
        ])

    col_widths = [20, 110, 50, 50, 80, 50, 135, 45]
    med_table = Table(med_rows, colWidths=col_widths, repeatRows=1)
    med_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    story.append(med_table)
    story.append(Spacer(1, 12))

    # Footer Disclaimer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
    story.append(
        Paragraph(
            "Clinical Safety Notice: This document is produced by an automated prescription OCR review tool for assisted documentation. "
            "It does not constitute automated medical advice or dispensing authorization. Human clinician review is mandatory.",
            disclaimer_style,
        )
    )

    doc.build(story)
    return out
