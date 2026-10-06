import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.models.schemas import FileMetadata, FileMeasurementsResponse, ErrorResponse
from app.services.file_processor import process_file
from app.storage.memory_store import get_file_record
from app.core.config import settings

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=FileMetadata, responses={400: {"model": ErrorResponse}})
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a .kml file or a .zip archive containing an ESRI Shapefile."
        )
        
    temp_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        if os.path.getsize(temp_path) == 0:
            raise ValueError("Empty file.")
            
        record = process_file(temp_path, file.filename)
        
        return FileMetadata(
            id=record["id"],
            filename=record["filename"],
            feature_count=record["feature_count"],
            crs=record["original_crs"],
            status=record["status"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/{file_id}/", response_model=FileMetadata, responses={404: {"model": ErrorResponse}})
async def get_file_info(file_id: str):
    record = get_file_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"File with ID '{file_id}' not found.")
        
    return FileMetadata(
        id=record["id"],
        filename=record["filename"],
        feature_count=record["feature_count"],
        crs=record["original_crs"],
        status=record["status"]
    )

@router.get("/{file_id}/measurements/", response_model=FileMeasurementsResponse, responses={404: {"model": ErrorResponse}})
async def get_file_measurements(file_id: str):
    record = get_file_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"File with ID '{file_id}' not found.")
        
    return FileMeasurementsResponse(**record)
