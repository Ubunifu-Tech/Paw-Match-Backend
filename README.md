# 🐾 PawMatch - Backend API

**Find Your Perfect Paw-tner!**

AI-powered dog breed matching system using FastAPI, Google Gemini 2.0, and PostgreSQL.
PawMatch helps users discover their ideal canine companion through conversational AI.

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

The backend integrates with the [Dog-Breeds-Dataset](https://github.com/maartenvandenbroeck/Dog-Breeds-Dataset) (5.32GB, 356 breeds, 35 images each).

**Current Implementation:**
- Uses placeholder images (`placedog.net`) for demo purposes
- Set `use_placeholder = False` in `image_service.py` to use actual dataset

**For Production:**
1. Clone the Dog-Breeds-Dataset repository
2. Download images for the 195 breeds in your dataset
3. Serve images from local storage or CDN
4. Update `image_service.py` with correct paths

## 🏗️ Project Structure

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

- **Breed Traits**: 195 breeds with 17 characteristics (1-5 scale)
- **Trait Descriptions**: Detailed explanations of each trait
- **Images**: Dog-Breeds-Dataset (GitHub)

## 🚧 Known Limitations

1. **Images**: Currently using placeholders; actual dataset needs to be downloaded
2. **Session Storage**: In-memory only (resets on server restart)
3. **Rate Limiting**: Not implemented (consider for production)
4. **Caching**: No caching layer (consider Redis for production)

## 🔮 Future Enhancements

- [ ] Persistent session storage (Redis/Database)
- [ ] Image caching and CDN integration
- [ ] Rate limiting and API throttling
- [ ] User authentication
- [ ] Breed comparison feature
- [ ] Save favorite breeds
- [ ] Email recommendations
- [ ] Video generation for "Day in the Life"

## 📚 Documentation

Comprehensive guides are available in the `docs/` folder:

- **[Application Workflow](docs/APPLICATION_WORKFLOW.md)** - Complete user journey and API flows
- **[Deployment Summary](docs/DEPLOYMENT_SUMMARY.md)** - Quick deployment reference
- **[Railway Deployment](docs/RAILWAY_DEPLOYMENT.md)** - Step-by-step Railway deployment
- **[Frontend Integration](docs/FRONTEND_INTEGRATION_GUIDE.md)** - API integration for frontend
- **[Security Guide](docs/SECURITY.md)** - Security implementation details
- **[Security Audit Report](docs/SECURITY_AUDIT_REPORT.md)** - Audit findings and fixes
- **[Database Setup](docs/DATABASE_SETUP.md)** - Database configuration
- **[User Features](docs/USER_FEATURES_IMPLEMENTATION.md)** - User management features

## 🧪 Testing

Run the complete workflow test:
```bash
python3 test_complete_workflow.py
```

This tests all 12 critical workflows including authentication, chat, recommendations, and security.

## 📝 License

This project is part of a competition submission.

## 🤝 Contributing

This is a competition project. For questions or issues, please contact the development team.

## 📧 Support

For API issues or questions, check:
1. Server logs
2. `/docs` endpoint for API documentation
3. Documentation in `docs/` folder
3. `/health` endpoint for server status
