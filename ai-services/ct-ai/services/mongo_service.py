"""
MongoDB Persistence Service for MedVision-AI
Connects to local MongoDB (medvision_ai database) to persist and retrieve
structured analysis records, patient IDs, and diagnostic reports.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "medvision_ai")


class MongoService:
    def __init__(self, uri: str = MONGODB_URI, db_name: str = DATABASE_NAME):
        self.uri = uri
        self.db_name = db_name
        self._client: Optional[MongoClient] = None
        self._db = None

    def get_database(self):
        """Returns the active MongoDB database handle with lazy connection."""
        if self._db is None:
            try:
                self._client = MongoClient(self.uri, serverSelectionTimeoutMS=3000)
                self._db = self._client[self.db_name]
            except ConnectionFailure as ce:
                print(f"[MongoService] Warning: Could not connect to MongoDB: {ce}")
                return None
        return self._db

    def save_analysis_result(
        self,
        analysis_id: str,
        modality: str,
        report_title: str,
        model_name: str,
        patient_id: str,
        patient_name: str = "Demo Patient",
        primary_finding: Optional[Dict[str, Any]] = None,
        full_report: Optional[Dict[str, Any]] = None,
        gradcam: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Saves a structured clinical analysis record into MongoDB 'analysisresults' collection.
        Enforces storing correct patientId, modality, and actual AI results.
        """
        db = self.get_database()
        if db is None:
            return {"saved": False, "reason": "database_offline"}

        record = {
            "analysisId": analysis_id,
            "patient": patient_id,
            "patientId": patient_id,
            "patientName": patient_name,
            "modality": modality,
            "reportTitle": report_title,
            "status": "completed",
            "modelInfo": {
                "modelName": model_name,
                "version": "2.0.0"
            },
            "primaryFinding": primary_finding or {},
            "report": full_report or {},
            "gradcam": gradcam or {},
            "filename": filename or "",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }

        try:
            res = db["analysisresults"].update_one(
                {"analysisId": analysis_id},
                {"$set": record},
                upsert=True
            )
            return {
                "saved": True,
                "analysisId": analysis_id,
                "patientId": patient_id,
                "modality": modality,
                "upserted_id": str(res.upserted_id) if res.upserted_id else None
            }
        except PyMongoError as pe:
            print(f"[MongoService] Error inserting record: {pe}")
            return {"saved": False, "error": str(pe)}

    def save_prescription_record(
        self,
        prescription_id: str,
        patient_id: str,
        patient_name: str = "Demo Patient",
        raw_text: str = "",
        extracted_medications: Optional[List[Dict[str, Any]]] = None,
        clinical_warnings: Optional[List[str]] = None,
        doctor_guidance: Optional[List[str]] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Saves an extracted prescription record into MongoDB 'prescriptions' and 'analysisresults'.
        """
        db = self.get_database()
        if db is None:
            return {"saved": False, "reason": "database_offline"}

        rx_doc = {
            "prescriptionId": prescription_id,
            "analysisId": prescription_id,
            "patient": patient_id,
            "patientId": patient_id,
            "patientName": patient_name,
            "modality": "prescription_doc",
            "reportTitle": "Clinical Prescription Analysis Report",
            "rawOcrText": raw_text,
            "extractedItems": extracted_medications or [],
            "clinicalWarnings": clinical_warnings or [],
            "doctorGuidance": doctor_guidance or [],
            "filename": filename or "",
            "status": "extracted",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }

        try:
            db["prescriptions"].update_one(
                {"prescriptionId": prescription_id},
                {"$set": rx_doc},
                upsert=True
            )
            db["analysisresults"].update_one(
                {"analysisId": prescription_id},
                {"$set": rx_doc},
                upsert=True
            )
            return {
                "saved": True,
                "prescriptionId": prescription_id,
                "patientId": patient_id,
                "modality": "prescription_doc"
            }
        except PyMongoError as pe:
            print(f"[MongoService] Error saving prescription: {pe}")
            return {"saved": False, "error": str(pe)}

    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an analysis record from MongoDB by analysisId."""
        db = self.get_database()
        if db is None:
            return None
        doc = db["analysisresults"].find_one({"analysisId": analysis_id})
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def get_records_by_patient(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieves all records for a given patientId."""
        db = self.get_database()
        if db is None:
            return []
        cursor = db["analysisresults"].find({"$or": [{"patientId": patient_id}, {"patient": patient_id}]}).sort("createdAt", -1)
        results = []
        for doc in cursor:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results


# Global singleton
mongo_service = MongoService()

