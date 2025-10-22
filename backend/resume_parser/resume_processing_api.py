#!/usr/bin/env python3
"""
Resume Processing API Service
FastAPI-based alternative to n8n workflow
"""

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import asyncio
import logging
from pathlib import Path
import tempfile
import json
from datetime import datetime

# Import your existing modules
import sys
sys.path.append('/mnt/project')

try:
    from text_extractor import DocumentTextExtractor
    from gemini_resume_parser import extract_resume_with_gemini  
    from resume_storage import store_resume_in_neo4j
    from connection import init_neo4j
except ImportError as e:
    logging.error(f"Import error: {e}")
    # We'll handle this gracefully

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Resume Intelligence API",
    description="Process resumes and extract insights using AI",
    version="1.0.0"
)

# Response models
class ProcessingResponse(BaseModel):
    success: bool
    message: str
    job_id: str
    estimated_time: str

class ProcessingResult(BaseModel):
    success: bool
    user_email: str
    extraction_method: str
    skills_extracted: int
    projects_found: int
    experience_level: str
    processing_time: float
    timestamp: str
    error: Optional[str] = None

class JobStatus(BaseModel):
    job_id: str
    status: str  # "processing", "completed", "failed"
    progress: int  # 0-100
    result: Optional[ProcessingResult] = None

# In-memory job tracking (in production, use Redis)
job_tracker: Dict[str, JobStatus] = {}

class ResumeProcessor:
    """Handle the complete resume processing pipeline"""
    
    def __init__(self):
        self.text_extractor = DocumentTextExtractor()
        # Initialize Neo4j connection
        try:
            init_neo4j()
            logger.info("✅ Neo4j connection established")
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed: {e}")
    
    async def process_resume(self, job_id: str, user_email: str, file_path: str, gemini_api_key: str):
        """Complete resume processing pipeline"""
        
        start_time = datetime.now()
        
        try:
            # Update job status
            job_tracker[job_id].status = "processing"
            job_tracker[job_id].progress = 10
            
            # Step 1: Extract text from document
            logger.info(f"🔄 [{job_id}] Extracting text from {file_path}")
            text, error = self.text_extractor.extract_text(file_path)
            
            if error:
                raise Exception(f"Text extraction failed: {error}")
            
            job_tracker[job_id].progress = 30
            
            # Step 2: Analyze with Gemini AI
            logger.info(f"🧠 [{job_id}] Analyzing with Gemini AI...")
            insights = extract_resume_with_gemini(text, gemini_api_key)
            
            if insights.get('extraction_method') == 'fallback':
                logger.warning(f"⚠️ [{job_id}] Gemini extraction failed, using fallback")
            
            job_tracker[job_id].progress = 70
            
            # Step 3: Store in Neo4j
            logger.info(f"💾 [{job_id}] Storing in Neo4j...")
            user_id = store_resume_in_neo4j(user_email, insights)
            
            job_tracker[job_id].progress = 90
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create result
            result = ProcessingResult(
                success=True,
                user_email=user_email,
                extraction_method=insights.get('extraction_method', 'unknown'),
                skills_extracted=len(insights.get('technical_skills', [])),
                projects_found=len(insights.get('projects', [])),
                experience_level=insights.get('experience_level', {}).get('level', 'unknown'),
                processing_time=processing_time,
                timestamp=datetime.now().isoformat()
            )
            
            # Update job status
            job_tracker[job_id].status = "completed"
            job_tracker[job_id].progress = 100
            job_tracker[job_id].result = result
            
            logger.info(f"✅ [{job_id}] Resume processing completed successfully")
            
        except Exception as e:
            logger.error(f"❌ [{job_id}] Processing failed: {e}")
            
            # Create error result
            processing_time = (datetime.now() - start_time).total_seconds()
            result = ProcessingResult(
                success=False,
                user_email=user_email,
                extraction_method="failed",
                skills_extracted=0,
                projects_found=0,
                experience_level="unknown",
                processing_time=processing_time,
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )
            
            # Update job status
            job_tracker[job_id].status = "failed"
            job_tracker[job_id].progress = 0
            job_tracker[job_id].result = result
        
        finally:
            # Clean up temporary file
            try:
                Path(file_path).unlink()
            except:
                pass

# Initialize processor
processor = ResumeProcessor()

@app.post("/upload-resume", response_model=ProcessingResponse)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_email: EmailStr = "user@example.com",
    gemini_api_key: str = "your-api-key-here"
):
    """
    Upload and process a resume file
    """
    
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file type. Please upload PDF or DOCX files."
        )
    
    # Generate job ID
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(user_email) % 10000}"
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            temp_file_path = tmp_file.name
        
        # Initialize job tracking
        job_tracker[job_id] = JobStatus(
            job_id=job_id,
            status="queued",
            progress=0
        )
        
        # Start background processing
        background_tasks.add_task(
            processor.process_resume,
            job_id=job_id,
            user_email=user_email,
            file_path=temp_file_path,
            gemini_api_key=gemini_api_key
        )
        
        return ProcessingResponse(
            success=True,
            message="Resume uploaded successfully. Processing started.",
            job_id=job_id,
            estimated_time="30-60 seconds"
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/job-status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Get the status of a resume processing job
    """
    
    if job_id not in job_tracker:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_tracker[job_id]

@app.get("/job-result/{job_id}", response_model=ProcessingResult)
async def get_job_result(job_id: str):
    """
    Get the final result of a completed job
    """
    
    if job_id not in job_tracker:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_tracker[job_id]
    
    if job.status == "processing" or job.status == "queued":
        raise HTTPException(status_code=202, detail="Job still processing")
    
    if job.result is None:
        raise HTTPException(status_code=404, detail="No result available")
    
    return job.result

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "neo4j_connected": True,  # You can add actual Neo4j health check here
        "active_jobs": len([j for j in job_tracker.values() if j.status == "processing"])
    }

@app.get("/")
async def root():
    """
    API information
    """
    return {
        "message": "Resume Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "upload": "POST /upload-resume",
            "status": "GET /job-status/{job_id}",
            "result": "GET /job-result/{job_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
