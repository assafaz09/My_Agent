from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List, Optional
import uuid
import os
import aiofiles
from datetime import datetime

from app.models.knowledge import KnowledgeDocument, UploadStatus
from app.services.file_processor import FileProcessor
from app.core.config import settings

router = APIRouter()

# In-memory upload status tracking (in production, use database)
upload_status: dict = {}

# Global file processor instance
file_processor = FileProcessor()

@router.post("/", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    """Upload a personal file for knowledge extraction"""
    try:
        # Validate file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size / (1024*1024):.1f}MB"
            )
        
        # Validate file extension
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if file_extension not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
            )
        
        # Generate unique upload ID and filename
        upload_id = str(uuid.uuid4())
        safe_filename = f"{upload_id}_{file.filename}"
        file_path = os.path.join(settings.upload_dir, safe_filename)
        
        # Reset file pointer and save file
        await file.seek(0)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create upload status
        upload_status[upload_id] = UploadStatus(
            upload_id=upload_id,
            filename=file.filename,
            status="processing",
            progress=0.0,
            created_at=datetime.now()
        )
        
        # Start background processing
        await file_processor.process_file_async(
            upload_id=upload_id,
            filename=file.filename,
            file_path=file_path,
            file_type=file_extension
        )
        
        return {
            "upload_id": upload_id,
            "filename": file.filename,
            "status": "processing",
            "message": "File uploaded successfully and processing started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/status/{upload_id}", response_model=UploadStatus)
async def get_upload_status(upload_id: str):
    """Get the processing status of an uploaded file"""
    if upload_id not in upload_status:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    return upload_status[upload_id]

@router.get("/uploads")
async def list_uploads():
    """List all upload statuses"""
    return {
        "uploads": [
            {
                "upload_id": uid,
                "filename": status.filename,
                "status": status.status,
                "progress": status.progress,
                "created_at": status.created_at.isoformat()
            }
            for uid, status in upload_status.items()
        ]
    }

@router.delete("/{upload_id}")
async def delete_upload(upload_id: str):
    """Delete an uploaded file and its processed data"""
    if upload_id not in upload_status:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    try:
        # Delete file and processed data
        await file_processor.delete_file_data(upload_id)
        del upload_status[upload_id]
        
        return {"message": "Upload deleted successfully", "upload_id": upload_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
