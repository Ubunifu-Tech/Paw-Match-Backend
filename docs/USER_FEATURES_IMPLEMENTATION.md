# User Features Implementation Plan

**Status**: In Progress  
**Date**: November 13, 2025

## ✅ Completed

### 1. Database Models
- ✅ **User Model** - Created with authentication, preferences, rate limiting
- ✅ **Session Updates** - Added user_id foreign key and summary field
- ✅ **SavedResult Updates** - Added user_id foreign key
- ✅ **Migration** - Applied successfully (8cd45bb1dde1)

### Database Schema
```sql
users:
  - id (UUID, PK)
  - email (VARCHAR, unique, nullable)
  - username (VARCHAR)
  - is_anonymous (BOOLEAN)
  - preferences (JSONB)
  - cross_session_memory (JSONB)
  - api_calls_today (INTEGER)
  - api_calls_reset_at (TIMESTAMP)
  - created_at, last_active_at

sessions:
  - user_id (UUID, FK → users.id) ← NEW
  - summary (TEXT) ← NEW for context optimization
  
saved_results:
  - user_id (UUID, FK → users.id) ← NEW
```

## 🚧 To Build

### 2. User Service
**File**: `app/services/user_service.py`

Features:
- Create anonymous user
- Register user (email + username)
- Get or create user
- Update user preferences
- Check rate limits
- Update cross-session memory
- Delete user data (GDPR compliance)

### 3. Session Service (Database-backed)
**File**: `app/services/session_service.py`

Features:
- Create session (linked to user)
- Save session to database
- Load session from database
- Resume conversation
- Summarize old messages (context optimization)
- List user's sessions
- Delete session

### 4. Rate Limiting Service
**File**: `app/services/rate_limit_service.py`

Features:
- Check Gemini API rate limits
- Track API calls per user
- Daily limits (configurable)
- Graceful degradation
- Admin override

### 5. Context Optimization
**File**: Update `app/services/gemini_service.py`

Features:
- Summarize conversations > 10 messages
- Keep recent messages (last 5)
- Store summary in session.summary
- Reduce token usage
- Maintain context quality

### 6. User API Endpoints
**File**: `app/api/users.py`

Endpoints:
- `POST /api/users/anonymous` - Create anonymous user
- `POST /api/users/register` - Register with email
- `GET /api/users/me` - Get current user
- `PUT /api/users/me` - Update preferences
- `GET /api/users/me/sessions` - List sessions
- `DELETE /api/users/me` - Delete all data
- `GET /api/users/me/memory` - Get cross-session memory

### 7. Enhanced Chat API
**File**: Update `app/api/chat.py`

Changes:
- Accept user_id in requests
- Save sessions to database
- Load previous sessions
- Apply rate limiting
- Use context optimization
- Support session resume

## 📋 Implementation Order

### Phase 1: Core Services (30 min)
1. ✅ User model
2. ⏳ User service
3. ⏳ Rate limiting service
4. ⏳ Session service

### Phase 2: API Integration (20 min)
5. ⏳ User API endpoints
6. ⏳ Update chat API
7. ⏳ Update recommendations API

### Phase 3: Advanced Features (20 min)
8. ⏳ Context optimization
9. ⏳ Cross-session memory
10. ⏳ Data deletion

### Phase 4: Testing (15 min)
11. ⏳ Test user creation
12. ⏳ Test rate limiting
13. ⏳ Test session persistence
14. ⏳ Test data deletion

## 🎯 Rate Limiting Strategy

### Default Limits (Free Tier)
```python
RATE_LIMITS = {
    "anonymous": {
        "chat_messages_per_day": 50,
        "recommendations_per_day": 10,
        "sessions_per_day": 5
    },
    "registered": {
        "chat_messages_per_day": 200,
        "recommendations_per_day": 50,
        "sessions_per_day": 20
    }
}
```

### Gemini API Protection
- Track API calls per user
- Reset daily at midnight UTC
- Return 429 (Too Many Requests) when exceeded
- Provide clear error messages
- Allow admin override

## 🔒 Data Privacy & Deletion

### GDPR Compliance
```python
# Delete all user data
DELETE /api/users/me

Deletes:
- User account
- All sessions (CASCADE)
- All chat messages (CASCADE)
- All saved results (CASCADE)
- Cross-session memory
- API call history
```

### Anonymous Users
- No email required
- Identified by UUID only
- Can upgrade to registered
- Auto-expire after 30 days inactive

## 💾 Session Persistence Flow

### Old (In-Memory)
```
User → Chat → ConversationAgent.sessions[id] → Lost on restart
```

### New (Database)
```
User → Chat → SessionService
           ↓
       PostgreSQL (persistent)
           ↓
       Can resume anytime
```

## 🧠 Context Optimization

### Problem
- Long conversations = many tokens
- Gemini has token limits
- Expensive API calls

### Solution
```python
if len(messages) > 10:
    # Keep last 5 messages
    recent = messages[-5:]
    
    # Summarize older messages
    summary = gemini.summarize(messages[:-5])
    
    # Store summary in session.summary
    session.summary = summary
    
    # Send to Gemini: summary + recent messages
    context = f"Previous conversation: {summary}\n\nRecent messages: {recent}"
```

## 🔄 Cross-Session Memory

### Use Cases
1. **Preferences**: "I prefer large dogs" → Remember for next session
2. **Lifestyle**: "I have 2 kids" → Don't ask again
3. **Dislikes**: "No shedding breeds" → Filter automatically
4. **Favorites**: Track breeds user liked

### Implementation
```python
# Store in user.cross_session_memory
{
    "preferred_size": "large",
    "has_children": true,
    "children_ages": [5, 8],
    "no_shedding": true,
    "favorite_breeds": ["Labrador", "Golden Retriever"],
    "last_recommendation_date": "2025-11-13"
}

# Use in new sessions
if user.get_memory("has_children"):
    # Skip asking about children
    profile.has_children = True
```

## 📊 Expected Benefits

### Performance
- ✅ Sessions survive server restarts
- ✅ Users can resume conversations
- ✅ Reduced token usage (summarization)
- ✅ Faster responses (cached memory)

### User Experience
- ✅ "Remember me" functionality
- ✅ Don't repeat questions
- ✅ Personalized experience
- ✅ Session history

### Cost Savings
- ✅ Rate limiting prevents abuse
- ✅ Context optimization reduces tokens
- ✅ Caching reduces API calls
- ✅ Sustainable for free tier

### Compliance
- ✅ GDPR-compliant data deletion
- ✅ User privacy controls
- ✅ Transparent data usage
- ✅ Audit trail

## 🚀 Next Steps

1. **Build User Service** - Core user management
2. **Build Session Service** - Database persistence
3. **Build Rate Limiting** - Protect API
4. **Update Chat API** - Integrate services
5. **Test Everything** - Comprehensive testing
6. **Documentation** - API docs and examples

## 📝 Notes

- All features designed for free tier sustainability
- Anonymous users supported (no email required)
- Easy to upgrade limits later
- GDPR-compliant from day one
- Backward compatible with existing code

---

**Total Estimated Time**: ~90 minutes  
**Priority**: High (enables production deployment)  
**Complexity**: Medium (well-defined requirements)
