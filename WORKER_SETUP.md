# 🚀 Redis Worker Setup for Railway

## Current Status
✅ Redis database deployed
✅ Backend API deployed  
❌ Worker process NOT running

## Why You Need the Worker

The video generation API can **enqueue jobs**, but without a worker running, the jobs will never be processed. They'll just sit in the queue forever.

## Setup Instructions

### Option 1: Add Worker as Separate Service (Recommended)

1. **In Railway Dashboard:**
   - Click "New" → "Empty Service"
   - Name it "paw-match-worker"
   - Connect to your GitHub repo (same as backend)
   - Set root directory: `/` (same as backend)

2. **Configure Worker Service:**
   - Go to service Settings → Deploy
   - Set **Custom Start Command**:
     ```bash
     python -m rq.cli worker video_generation --url $REDIS_URL
     ```
   
   **OR** use the worker.py script (simpler):
     ```bash
     python worker.py
     ```

3. **Add Environment Variables:**
   - Copy ALL environment variables from your backend service:
     - `REDIS_URL` (should auto-link from Redis service)
     - `GEMINI_API_KEY`
     - `DATABASE_URL`
     - `SECRET_KEY`
     - `FRONTEND_URL`
   - The worker needs the same env vars as the API

4. **Deploy:**
   - Click "Deploy"
   - Worker will start processing jobs from the queue

### Option 2: Use Railway CLI (Faster)

```bash
# In your backend directory
railway link  # Link to your project

# Add worker service
railway service create paw-match-worker

# Set start command
railway run --service paw-match-worker rq worker video_generation --url $REDIS_URL

# Deploy
railway up --service paw-match-worker
```

### Option 3: Modify Existing Service (Not Recommended)

Add to your existing backend start command:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT & rq worker video_generation --url $REDIS_URL
```

**Warning:** This runs both in one container. If one crashes, both crash.

## Verify It's Working

### 1. Check Worker is Running
In Railway logs for worker service, you should see:
```
Worker started
Listening on video_generation queue
```

### 2. Test Video Generation
```bash
# From your local machine
curl -X POST https://your-api.railway.app/api/video-queue/health

# Should return:
{
  "status": "healthy",
  "queue_size": 0,
  "message": "Video queue is operational"
}
```

### 3. Generate a Test Video
1. Go to any breed detail page on your deployed frontend
2. Scroll to "Day-in-the-Life Video" section
3. Click "Generate Video"
4. Wait 60-90 seconds
5. Video should appear!

## Troubleshooting

### Worker Not Starting
- Check REDIS_URL is set correctly
- Verify all dependencies are installed (requirements.txt)
- Check Railway logs for errors

### Jobs Not Processing
```bash
# Check queue status
rq info --url $REDIS_URL

# Should show:
# - Workers: 1
# - Queues: video_generation
# - Jobs: 0 queued, X finished
```

### Video Generation Fails
- Check GEMINI_API_KEY has Veo access
- Run test locally: `python test_video_direct.py`
- Check worker logs for errors

## Cost Considerations

**Railway Costs:**
- Redis: ~$5/month (512MB)
- Worker: ~$5/month (minimal resources)
- Total additional: ~$10/month

**Google Veo Costs:**
- Check Google AI Studio pricing
- Each video generation costs $ (varies)
- Consider rate limiting in production

## Quick Test Command

Once worker is deployed, test end-to-end:

```bash
# 1. Generate video
curl -X POST https://your-api.railway.app/api/video-queue/generate \
  -H "Content-Type: application/json" \
  -d '{
    "breed_name": "Labrador Retriever",
    "breed_traits": {
      "size": "Large",
      "energy_level": 4,
      "trainability": 5,
      "grooming_needs": 2,
      "good_with_children": 5,
      "good_with_other_dogs": 4,
      "shedding_level": 4,
      "barking_level": 3
    },
    "user_profile": {
      "living_space": "house",
      "has_yard": true,
      "family_members": 3,
      "has_children": true,
      "has_other_pets": false,
      "work_schedule": "full_time",
      "activity_level": "moderate",
      "experience_level": "intermediate"
    },
    "image_urls": []
  }'

# Response: {"job_id": "abc123", "status": "queued", ...}

# 2. Check status (wait 60-90 seconds)
curl https://your-api.railway.app/api/video-queue/status/abc123

# Response: {"status": "completed", "result": {"video_url": "https://..."}}
```

## Next Steps

1. ✅ Add worker service to Railway
2. ✅ Copy environment variables
3. ✅ Deploy worker
4. ✅ Test video generation
5. ✅ Monitor logs for errors
6. ✅ Celebrate! 🎉

---

**Estimated Time:** 15-30 minutes
**Difficulty:** Easy (just configuration, no code changes)
