# backend/admin_routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import joblib
import json
from datetime import datetime
import os

router = APIRouter()

MODEL_DIR = "model"
STATUS_FILE = os.path.join(MODEL_DIR, "model_status.json")

@router.post("/admin/upload-model")
def upload_model(file: UploadFile = File(...)):
    """Upload a trained ML model (.pkl or .joblib) and update status dynamically"""
    try:
        # Ensure model folder exists
        os.makedirs(MODEL_DIR, exist_ok=True)

        # Validate file type
        if not (file.filename.endswith(".pkl") or file.filename.endswith(".joblib")):
            raise HTTPException(status_code=400, detail="Only .pkl or .joblib files are allowed")

        save_path = os.path.join(MODEL_DIR, file.filename)

        # Save file to disk
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Verify model can load
        joblib.load(save_path)

        # Create/update model status
        status_data = {
            "model_name": file.filename,
            "status": "active",
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "verified": True,
            "path": save_path
        }

        # Save to JSON
        with open(STATUS_FILE, "w") as status_file:
            json.dump(status_data, status_file, indent=4)

        return {
            "message": f"✅ Model '{file.filename}' uploaded and verified successfully.",
            "status": status_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/model-status")
def get_model_status():
    """Get current model status"""
    try:
        if not os.path.exists(STATUS_FILE):
            return {"status": "No model uploaded yet"}

        with open(STATUS_FILE, "r") as file:
            status = json.load(file)

        return {"status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
