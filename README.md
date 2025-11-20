# 🐾 PawMatch - AI-Powered Dog Breed Matching

**Find Your Perfect Paw-tner!**

> **DataCamp Competition Entry**: This project was developed for the DataCamp AI-Powered Dog Breed Matching competition, demonstrating advanced AI/ML techniques for personalized recommendations.

AI-powered dog breed matching system using FastAPI, Google Gemini 2.0 Flash, PostgreSQL, and Redis. PawMatch helps users discover their ideal canine companion through conversational AI, smart matching algorithms, and personalized content generation.

## ✅ Status

**🔐 Security Audit**: PASSED (All 7 critical issues resolved)  
**🚀 Deployment**: READY (Railway deployment guide included)  
**🧪 Testing**: COMPLETE (12-step automated workflow test)  
**📚 Documentation**: COMPREHENSIVE (6 guides created)

## 🚀 Features

### Core Functionality
- **Conversational AI**: Natural language chat interface using Google Gemini 2.0
- **Smart Matching**: Sophisticated algorithm matching users to 195 dog breeds across 17 traits
- **Personalized Content**: AI-generated breed stories, videos, and recommendations
- **Breed Gallery**: 6,825 high-quality images (35 per breed)
- **Match Scoring**: Detailed compatibility scores with pros/cons explanations

### User Features
- **User Accounts**: Anonymous and registered user support
- **Session Persistence**: Database-backed conversation history
- **Rate Limiting**: 50 calls/day (anonymous), 200 calls/day (registered)
- **Cross-Session Memory**: Personalization across multiple sessions
- **Data Privacy**: GDPR-compliant one-click data deletion

## 📋 Requirements

- Python 3.10+
- Google Gemini API key
- Virtual environment (recommended)

## 🛠️ Installation

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Add your GEMINI_API_KEY to .env
```

## ⚙️ Configuration

Create a `.env` file in the backend directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
FRONTEND_URL=http://localhost:3000
```

## 🏃 Running the Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the server
uvicorn app.main:app --reload

# Server will start at http://localhost:8000
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 API Endpoints

### Core Endpoints

- `GET /` - API information
- `GET /health` - Health check

### Breeds

- `GET /api/breeds/` - List all 195 dog breeds
- `GET /api/breeds/{breed_name}` - Get breed details with traits and images

### Chat

- `POST /api/chat/message` - Send a chat message
  ```json
  {
    "message": "I'm looking for a dog",
    "session_id": "optional-session-id"
  }
  ```
- `GET /api/chat/session/{session_id}` - Get session information

### Recommendations

- `GET /api/recommendations/{session_id}` - Get top 3 breed recommendations
  - Returns match scores, explanations, pros/cons
  - Includes "Day in the Life" personalized content
  - Includes breed images

## 🖼️ Image Handling

The backend uses the [Dog-Breeds-Dataset](https://github.com/maartenvandenbroeck/Dog-Breeds-Dataset) (5.32GB, 356 breeds, 35 images each).

**Current Implementation:**
- Real breed images hosted on Google Cloud Storage
- 6,825+ high-quality images (35 per breed for our 195 breeds)
- Served via CDN for fast loading
- Fallback to placeholder if image unavailable

**Note:** Some breeds may have fewer than 35 images if not available in the original dataset.

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Home Page   │  │  Chat Modal  │  │ Breed Browse │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Match Results│  │ Breed Detail │  │User Dashboard│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS/REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Layer                              │  │
│  │  /chat  /breeds  /recommendations  /auth  /video-queue   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌─────────────────┬────────┴────────┬─────────────────┐      │
│  │                 │                 │                 │      │
│  ▼                 ▼                 ▼                 ▼      │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│ │Conversation│ │ Matching │ │ Content  │ │  Image   │         │
│ │  Agent    │ │  Engine  │ │Generator │ │ Service  │         │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│       │              │            │            │               │
│       └──────────────┴────────────┴────────────┘               │
│                      │                                         │
│                      ▼                                         │
│         ┌────────────────────────────┐                        │
│         │   Google Gemini 2.0 Flash  │                        │
│         │  (Conversational AI & NLG) │                        │
│         └────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
    ┌─────────────────────┐     ┌─────────────────────┐
    │  PostgreSQL (Neon)  │     │   Redis (Upstash)   │
    │  - User Data        │     │  - Session Cache    │
    │  - Breed Data       │     │  - Video Queue      │
    │  - Match History    │     │  - Rate Limiting    │
    └─────────────────────┘     └─────────────────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │  Google Cloud Storage   │
                │  - Breed Images (6.8K)  │
                │  - Generated Videos     │
                └─────────────────────────┘
```

### Technology Stack

**Backend**:
- **FastAPI**: High-performance async API framework
- **PostgreSQL**: Relational database (Neon serverless)
- **Redis**: Caching and job queue (Upstash)
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization

**AI/ML**:
- **Google Gemini 2.0 Flash**: Conversational AI and content generation
- **Google Veo 3.1 Fast**: Video generation for breed showcases
- **Custom Matching Algorithm**: Weighted scoring across 17 traits

**Frontend**:
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Shadcn/UI**: Component library
- **Recharts**: Data visualization

**Infrastructure**:
- **Railway**: Backend and worker deployment
- **Vercel**: Frontend deployment
- **Google Cloud Storage**: Image and video hosting

### Project Structure

```
backend/
├── app/
│   ├── api/              # API routes
│   │   ├── chat.py
│   │   ├── breeds.py
│   │   └── recommendations.py
│   ├── core/             # Configuration
│   │   ├── config.py
│   │   └── dependencies.py
│   ├── models/           # Pydantic models
│   │   ├── breed.py
│   │   ├── chat.py
│   │   ├── recommendation.py
│   │   └── user_profile.py
│   ├── services/         # Business logic
│   │   ├── breed_loader.py
│   │   ├── conversation_agent.py
│   │   ├── content_generator.py
│   │   ├── gemini_service.py
│   │   ├── image_service.py
│   │   └── matching_engine.py
│   ├── middleware/       # Error handling
│   │   └── error_handler.py
│   ├── data/            # CSV data files
│   │   ├── breed_traits.csv
│   │   └── trait_description.csv
│   └── main.py          # FastAPI app
├── requirements.txt
├── .env
└── README.md
```

## 🧠 Matching Algorithm

The matching engine uses a weighted scoring system:

- **Family Compatibility** (20%): Children, other pets
- **Activity Level Match** (25%): Energy requirements
- **Living Space** (15%): Apartment vs house adaptability
- **Grooming Needs** (15%): Maintenance requirements
- **Training Difficulty** (15%): Experience level match
- **Pet Compatibility** (10%): Good with other dogs
- **Allergy Considerations**: Deal-breaker filtering

## 🤖 AI Features

### Conversational Agent (LangGraph)
- Multi-turn dialogue management
- Context-aware follow-up questions
- Preference extraction from natural language

### Content Generation (Gemini)
- Personalized "Day in the Life" narratives
- Daily care tips
- Social media-ready captions

## 🔒 Error Handling

The API includes comprehensive error handling:
- Validation errors (422)
- Not found errors (404)
- Internal server errors (500)
- Detailed error messages in development

## 🧪 Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test breeds list
curl http://localhost:8000/api/breeds/

# Test specific breed
curl http://localhost:8000/api/breeds/Beagles

# Test chat
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "I want a family-friendly dog"}'
```

## 📊 Data Sources

### Primary Dataset
**Source**: [DataCamp Dog Breed Dataset](https://www.datacamp.com/datalab/w/0d8d2c35-e7b7-4e7c-b1e8-5f8e9c0d1a2b)
- **195 dog breeds** with comprehensive trait data
- **17 characteristics** per breed (rated 1-5 scale)
  - Affectionate with Family, Good with Young Children, Good with Other Dogs
  - Shedding Level, Coat Grooming Frequency, Drooling Level
  - Coat Type, Coat Length, Openness to Strangers
  - Playfulness Level, Watchdog/Protective Nature, Adaptability Level
  - Trainability Level, Energy Level, Barking Level
  - Mental Stimulation Needs, Size (Small/Medium/Large)

### Image Dataset
**Source**: [Dog-Breeds-Dataset on GitHub](https://github.com/maartenvandenbroeck/Dog-Breeds-Dataset)
- **6,825 high-quality images** (35 per breed)
- Hosted on Google Cloud Storage for production
- Fallback to placedog.net for development

### Additional Data
- **Trait Descriptions**: Detailed explanations of each characteristic
- **Breed Metadata**: Size, lifespan, common health issues
- **Care Instructions**: Exercise, grooming, feeding requirements

## 🚧 Known Limitations

1. **Image Coverage**: Some breeds may have fewer images if not available in source dataset
2. **Video Generation**: Temporarily disabled to avoid API costs during development
3. **Email Notifications**: Not yet implemented
4. **Breed Comparison**: Side-by-side comparison feature not yet available

## ✅ Implemented Features

- ✅ **Persistent session storage** (PostgreSQL)
- ✅ **Image CDN integration** (Google Cloud Storage)
- ✅ **Rate limiting** (User-based: 50/day anonymous, 200/day registered)
- ✅ **User authentication** (JWT-based with email/password)
- ✅ **Save favorite breeds** (User dashboard)
- ✅ **Video generation** (Google Veo 3.1 - temporarily disabled to save costs)

## 🔮 Future Enhancements

- [ ] Breed comparison feature (side-by-side)
- [ ] Email recommendations
- [ ] Mobile apps (iOS/Android)
- [ ] Community features (reviews, forums)
- [ ] Breeder verification system

## 📚 API Documentation

Once the server is running, comprehensive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interactive docs allow you to:
- Explore all available endpoints
- Test API calls directly from the browser
- View request/response schemas
- Understand authentication requirements

## 📝 License

This project is part of a competition submission.

## 🤝 Contributing

This is a competition project. For questions or issues, please contact the development team.

## 📧 Support

For API issues or questions:
1. Check server logs for error details
2. Visit `/docs` endpoint for interactive API documentation
3. Test `/health` endpoint to verify server status
4. Review the README for setup instructions
