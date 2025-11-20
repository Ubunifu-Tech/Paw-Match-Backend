"""
Video Queue API Routes

Endpoints for async video generation using Redis Queue.

Author: PawMatch Team
Version: 1.0.0
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict
from app.services.video_queue import get_video_queue, VideoQueue
from app.models.user_profile import UserProfile
from app.models.breed import BreedTraits
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video-queue", tags=["video_queue"])


class VideoGenerationRequest(BaseModel):
    """Request model for video generation."""
    user_profile: UserProfile
    breed_name: str
    breed_traits: BreedTraits
    image_urls: Optional[list] = None


class VideoJobResponse(BaseModel):
    """Response model for video job."""
    job_id: str
    status: str
    message: str


class VideoStatusResponse(BaseModel):
    """Response model for video status."""
    job_id: str
    status: str
    result: Optional[Dict] = None
    error: Optional[str] = None
    progress: Optional[int] = None
    position: Optional[int] = None


@router.post("/generate", response_model=VideoJobResponse)
async def generate_video(
    request: VideoGenerationRequest,
    queue: VideoQueue = Depends(get_video_queue)
):
    """
    Enqueue a video generation job.
    
    This endpoint immediately returns a job ID and processes the video
    generation in the background using Redis Queue.
    
    Args:
        request: Video generation request with user profile, breed info, and images
        queue: Video queue service (injected)
        
    Returns:
        Job ID for tracking the video generation status
    """
    try:
        job_id = queue.enqueue_video_generation(
            user_profile=request.user_profile,
            breed_name=request.breed_name,
            breed_traits=request.breed_traits,
            image_urls=request.image_urls
        )
        
        return VideoJobResponse(
            job_id=job_id,
            status="queued",
            message=f"Video generation job queued for {request.breed_name}"
        )
        
    except Exception as e:
        logger.error(f"Failed to enqueue video generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=VideoStatusResponse)
async def get_video_status(
    job_id: str,
    queue: VideoQueue = Depends(get_video_queue)
):
    """
    Get the status of a video generation job.
    
    Args:
        job_id: The job ID returned from the generate endpoint
        queue: Video queue service (injected)
        
    Returns:
        Current status of the video generation job
        
    Status values:
        - queued: Job is waiting to be processed
        - processing: Video is currently being generated
        - completed: Video generation finished successfully
        - failed: Video generation failed
        - error: Error fetching job status
    """
    try:
        status = queue.get_job_status(job_id)
        
        return VideoStatusResponse(
            job_id=job_id,
            **status
        )
        
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}")
        raise HTTPException(status_code=404, detail="Job not found")


@router.delete("/cancel/{job_id}")
async def cancel_video_job(
    job_id: str,
    queue: VideoQueue = Depends(get_video_queue)
):
    """
    Cancel a video generation job.
    
    Args:
        job_id: The job ID to cancel
        queue: Video queue service (injected)
        
    Returns:
        Success message
    """
    try:
        success = queue.cancel_job(job_id)
        
        if success:
            return {"message": "Job cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel job")
            
    except Exception as e:
        logger.error(f"Failed to cancel job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def queue_health():
    """
    Check video queue health.
    
    Returns:
        Queue connection status and worker info
    """
    try:
        queue = get_video_queue()
        
        # Check queue connection
        queue_size = len(queue.queue)
        
        return {
            "status": "healthy",
            "queue_size": queue_size,
            "message": "Video queue is operational"
        }
        
    except Exception as e:
        logger.error(f"Queue health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
