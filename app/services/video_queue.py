"""
Video Generation Queue Service

Uses Redis Queue (RQ) for async video generation.

Author: PawMatch Team
Version: 1.0.0
"""

import json
from typing import Dict, Optional
from rq import Queue
from rq.job import Job
from redis import Redis
from app.core.config import get_settings
from app.services.content_generator import ContentGenerator
from app.services.gemini_service import GeminiService
from app.models.user_profile import UserProfile
from app.models.breed import BreedTraits
import logging

logger = logging.getLogger(__name__)

settings = get_settings()


def generate_video_task(
    user_profile_dict: Dict,
    breed_name: str,
    breed_traits_dict: Dict,
    image_urls: Optional[list] = None
) -> Dict:
    """
    Background task for video generation.
    This runs in a separate worker process.
    
    Args:
        user_profile_dict: User profile as dictionary
        breed_name: Name of the breed
        breed_traits_dict: Breed traits as dictionary
        image_urls: Optional list of image URLs
        
    Returns:
        Dict with video generation result
    """
    try:
        # Reconstruct objects from dicts
        user_profile = UserProfile(**user_profile_dict)
        breed_traits = BreedTraits(**breed_traits_dict)
        
        # Initialize Gemini service and content generator
        gemini_service = GeminiService(api_key=settings.gemini_api_key)
        generator = ContentGenerator(gemini_service=gemini_service)
        
        # Generate video
        result = generator.generate_day_in_life_video(
            user_profile=user_profile,
            breed_name=breed_name,
            breed_traits=breed_traits,
            image_urls=image_urls
        )
        
        logger.info(f"Video generated successfully for {breed_name}")
        return {
            'status': 'completed',
            'result': result
        }
        
    except Exception as e:
        logger.error(f"Video generation failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }


class VideoQueue:
    """
    Redis Queue service for async video generation.
    
    Attributes:
        redis_conn: Redis connection
        queue: RQ Queue instance
    """
    
    def __init__(self):
        """Initialize Redis Queue connection."""
        self.redis_conn = Redis.from_url(settings.redis_url)
        self.queue = Queue('video_generation', connection=self.redis_conn)
        logger.info("Video queue initialized")
    
    def enqueue_video_generation(
        self,
        user_profile: UserProfile,
        breed_name: str,
        breed_traits: BreedTraits,
        image_urls: Optional[list] = None
    ) -> str:
        """
        Enqueue a video generation task.
        
        Args:
            user_profile: User profile object
            breed_name: Name of the breed
            breed_traits: Breed traits object
            image_urls: Optional list of image URLs
            
        Returns:
            Job ID for tracking
        """
        try:
            # Convert objects to dicts for JSON serialization
            user_profile_dict = user_profile.dict()
            breed_traits_dict = breed_traits.dict()
            
            # Enqueue the job with 10 minute timeout
            job = self.queue.enqueue(
                generate_video_task,
                user_profile_dict,
                breed_name,
                breed_traits_dict,
                image_urls,
                job_timeout='10m',
                result_ttl=3600  # Keep result for 1 hour
            )
            
            logger.info(f"Video generation job enqueued: {job.id} for breed {breed_name}")
            return job.id
            
        except Exception as e:
            logger.error(f"Failed to enqueue video job: {str(e)}")
            raise
    
    def get_job_status(self, job_id: str) -> Dict:
        """
        Get the status of a video generation job.
        
        Args:
            job_id: The job ID
            
        Returns:
            Dict with job status and result if completed
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            
            if job.is_finished:
                return {
                    'status': 'completed',
                    'result': job.result
                }
            elif job.is_failed:
                return {
                    'status': 'failed',
                    'error': str(job.exc_info)
                }
            elif job.is_started:
                return {
                    'status': 'processing',
                    'progress': job.meta.get('progress', 0)
                }
            else:
                return {
                    'status': 'queued',
                    'position': job.get_position()
                }
                
        except Exception as e:
            logger.error(f"Failed to fetch job status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a video generation job.
        
        Args:
            job_id: The job ID
            
        Returns:
            True if cancelled successfully
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            job.cancel()
            logger.info(f"Job {job_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel job: {str(e)}")
            return False


# Singleton instance
_video_queue = None

def get_video_queue() -> VideoQueue:
    """Get or create the video queue singleton."""
    global _video_queue
    if _video_queue is None:
        _video_queue = VideoQueue()
    return _video_queue
