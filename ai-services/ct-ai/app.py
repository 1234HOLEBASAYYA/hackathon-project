"""
MedVision-AI — AI-Powered CT Scan Image Analyzer
Flask Application Server
"""

import os
import sys
import uuid
import json
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load environment configuration
load_dotenv(ROOT_DIR / ".env")

from services.image_preprocessing import preprocess_ct_image, validate_image_file, ImageValidationError, IncompatibleImageModalityError
from services.gemini_service import analyze_ct_scan_image, get_gemini_client, GeminiAnalysisError, GeminiConfigurationError, GeminiIncompatibleModalityError
from services.report_service import generate_pdf_report
from services.mongo_service import mongo_service

app = Flask(
    __name__,
    template_folder=str(ROOT_DIR / "templates"),
    static_folder=str(ROOT_DIR / "static")
)
CORS(app)

# Configuration
app.config["UPLOAD_FOLDER"] = str(ROOT_DIR / "uploads")
app.config["REPORT_FOLDER"] = str(ROOT_DIR / "generated_reports")
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 15 * 1024 * 1024))  # 15 MB

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["REPORT_FOLDER"], exist_ok=True)


@app.route("/")
def index():
    """Renders the MedVision-AI CT Image Analyzer dashboard."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Checks server status and verifies whether the Gemini API key and configuration are active.
    """
    api_key_configured = bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "YOUR_GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    
    client_status = "unconfigured"
    if api_key_configured:
        try:
            get_gemini_client()
            client_status = "ready"
        except Exception as e:
            client_status = f"error: {str(e)}"

    return jsonify({
        "status": "healthy",
        "service": "MedVision-AI CT Scan Image Analyzer",
        "version": "2.0.0",
        "framework": "Flask",
        "gemini": {
            "api_key_configured": api_key_configured,
            "configured_model": model_name,
            "client_status": client_status
        }
    }), 200


@app.route("/api/analyze", methods=["POST"])
def analyze_image_endpoint():
    """
    Accepts an uploaded medical image, validates and preprocesses it,
    sends it to Gemini for visual analysis, and returns a structured report.
    """
    file = request.files.get("file") or request.files.get("image")
    if not file or file.filename == "":
        return jsonify({
            "error": "No file uploaded",
            "message": "Please select a CT scan or medical image file (PNG, JPG, JPEG) to analyze."
        }), 400

    # Secure file saving with UUID prefix to prevent collisions
    original_filename = file.filename
    clean_stem = Path(original_filename).stem[:40]
    ext = Path(original_filename).suffix.lower()
    safe_filename = f"{uuid.uuid4().hex[:10]}_{clean_stem}{ext}"
    saved_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_filename)

    try:
        file.save(saved_path)

        # 1. Preprocess & validate image with strict CT modality enforcement
        prep_result = preprocess_ct_image(
            saved_path,
            output_dir=app.config["UPLOAD_FOLDER"],
            enforce_ct_modality=True
        )

        dimensions_str = prep_result["original_dimensions"]["formatted"]

        # 2. Run Gemini Vision Analysis
        analysis_report = analyze_ct_scan_image(
            image_input=prep_result["processed_path"],
            filename=original_filename,
            dimensions_str=dimensions_str
        )

        analysis_id = f"cxa_{uuid.uuid4().hex[:10]}"
        patient_id = request.form.get("patient_id") or request.form.get("patientId") or "guest_patient_001"
        analysis_report["analysis_id"] = analysis_id
        analysis_report["patient_id"] = patient_id
        analysis_report["modality"] = "ct_scan"

        # Attach image preprocessing metadata to response
        analysis_report["image_preprocessing"] = {
            "original_dimensions": prep_result["original_dimensions"],
            "processed_dimensions": prep_result["processed_dimensions"],
            "file_size": prep_result["file_size_formatted"],
            "server_image_id": safe_filename
        }

        # Save actual CT analysis result into MongoDB
        mongo_service.save_analysis_result(
            analysis_id=analysis_id,
            modality="ct_scan",
            report_title=analysis_report.get("report_title", "AI-Assisted CT Image Analysis Report"),
            model_name=analysis_report.get("model_used", "gemini-3.5-flash"),
            patient_id=patient_id,
            primary_finding=(analysis_report.get("potential_findings") or [{}])[0],
            full_report=analysis_report,
            filename=original_filename
        )

        return jsonify({
            "status": "success",
            "data": analysis_report
        }), 200

    except (IncompatibleImageModalityError, GeminiIncompatibleModalityError) as ime:
        return jsonify({
            "error": "Incompatible Image Modality",
            "detected_modality": getattr(ime, "detected_modality", "incompatible"),
            "message": ime.message
        }), 400

    except ImageValidationError as ive:
        return jsonify({
            "error": "Image validation failed",
            "message": str(ive)
        }), 400

    except GeminiConfigurationError as gce:
        return jsonify({
            "error": "Gemini configuration error",
            "message": str(gce)
        }), 503

    except GeminiAnalysisError as gae:
        return jsonify({
            "error": "AI analysis error",
            "message": gae.message,
            "retryable": gae.retryable
        }), gae.status_code

    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": "An unexpected error occurred during image processing. Please retry."
        }), 500


@app.route("/api/generate-report", methods=["POST"])
def generate_report_endpoint():
    """
    Accepts validated analysis JSON and generates a downloadable PDF medical report.
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "error": "Invalid request body",
            "message": "A valid JSON report object is required to generate the PDF."
        }), 400

    report_content = data.get("report") or data
    server_image_id = data.get("server_image_id") or report_content.get("image_preprocessing", {}).get("server_image_id")
    
    image_path = None
    if server_image_id:
        candidate_path = os.path.join(app.config["UPLOAD_FOLDER"], server_image_id)
        if os.path.exists(candidate_path):
            image_path = candidate_path

    try:
        pdf_path = generate_pdf_report(
            report_data=report_content,
            image_path=image_path,
            output_dir=app.config["REPORT_FOLDER"]
        )
        pdf_filename = Path(pdf_path).name

        return jsonify({
            "status": "success",
            "filename": pdf_filename,
            "download_url": f"/api/reports/download/{pdf_filename}",
            "message": "PDF report successfully generated."
        }), 200

    except Exception as e:
        return jsonify({
            "error": "PDF generation failed",
            "message": f"Unable to generate PDF report: {str(e)}"
        }), 500


@app.route("/api/reports/download/<filename>", methods=["GET"])
def download_report(filename):
    """Downloads a generated PDF report."""
    safe_filename = Path(filename).name
    report_file = os.path.join(app.config["REPORT_FOLDER"], safe_filename)
    if not os.path.exists(report_file):
        return jsonify({"error": "Report not found"}), 404

    return send_file(
        report_file,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=safe_filename
    )


@app.route("/api/records/<analysis_id>", methods=["GET"])
def get_record(analysis_id):
    """Retrieves an analysis record from MongoDB by analysisId."""
    record = mongo_service.get_analysis_by_id(analysis_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404
    return jsonify({"status": "success", "record": record}), 200


@app.route("/api/records/patient/<patient_id>", methods=["GET"])
def get_patient_records(patient_id):
    """Retrieves all medical records for a specific patientId from MongoDB."""
    records = mongo_service.get_records_by_patient(patient_id)
    return jsonify({"status": "success", "patientId": patient_id, "count": len(records), "records": records}), 200


@app.route("/api/sample", methods=["GET"])
def get_sample_ct_scan():
    """
    Returns a sample medical image from dataset for immediate testing.
    """
    sample_path = ROOT_DIR / "dataset" / "chest_xray" / "test" / "PNEUMONIA" / "person1_virus_6.jpeg"
    if not sample_path.exists():
        return jsonify({"error": "Sample dataset image not found"}), 404

    return send_file(str(sample_path), mimetype="image/jpeg")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"[MedVision-AI] Starting Flask CT Image Analyzer on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
