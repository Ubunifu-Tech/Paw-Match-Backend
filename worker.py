"""
Redis Queue Worker for Video Generation

This script starts a worker process that listens to the video generation queue
and processes jobs in the background.

Usage:
    python worker.py

Environment Variables:
    REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)

Author: PawMatch Team
Version: 1.0.0
"""

import sys
import os
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from redis import Redis
from rq import Worker, Queue
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Start the RQ worker."""
    try:
        settings = get_settings()
        
        # Connect to Redis
        redis_conn = Redis.from_url(settings.redis_url)
        logger.info(f"Connected to Redis at {settings.redis_url}")
        
        # Create queue
        queue = Queue('video_generation', connection=redis_conn)
        logger.info(f"Listening to queue: video_generation")
        
        # Start worker
        worker = Worker([queue], connection=redis_conn)
        logger.info("Worker started. Press Ctrl+C to stop.")
        
        worker.work()
        
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {str(e)}")
        raise


if __name__ == '__main__':
    main()
