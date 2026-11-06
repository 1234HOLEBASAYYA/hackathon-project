import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


def save_upload_file(upload_file: UploadFile, destination_dir: Path) -> Path:
    """
    Validates file extension and securely writes file to disk.
    """
    destination_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload_file.filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{suffix}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    unique_name = f"{uuid.uuid4().hex}_{upload_file.filename}"
    file_path = destination_dir / unique_name

    with open(file_path, "wb") as buffer:
        buffer.write(upload_file.file.read())

    # Reset file cursor in case caller wants to read again
    upload_file.file.seek(0)
    return file_path
