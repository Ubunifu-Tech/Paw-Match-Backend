# PawMatch Application Workflow

## 🎯 Complete End-to-End Flow

### 1️⃣ User Onboarding

```
┌─────────────────────────────────────────────────────────────┐
│                    User Arrives at App                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
                ┌───────────────────────┐
                │   Choose User Type    │
                └───────────────────────┘
                            ↓
            ┌───────────────┴───────────────┐
            ↓                               ↓
    ┌──────────────┐              ┌──────────────────┐
    │  Anonymous   │              │   Register       │
    │  User        │              │   (Email + Pwd)  │
    └──────────────┘              └──────────────────┘
            ↓                               ↓
    POST /users/anonymous         POST /users/register
    Returns: user_id              Returns: user details
    Rate Limit: 50/day            Rate Limit: 200/day
```

**API Endpoints:**
- `POST /users/anonymous` - Create anonymous user
- `POST /users/register` - Register with email/password (requires strong password)
- `POST /users/upgrade` - Convert anonymous → registered

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

---

### 2️⃣ Authentication Flow (Registered Users)

```
┌─────────────────────────────────────────────────────────────┐
│              User Logs In (Registered Only)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
                POST /users/token
                (email + password)
                            ↓
                ┌───────────────────────┐
                │  Backend Validates:   │
                │  1. User exists       │
                │  2. Password correct  │
                │  3. Rate limit OK     │
                └───────────────────────┘
                            ↓
                ┌───────────────────────┐
                │  Returns JWT Token    │
                │  Expires: 30 minutes  │
                └───────────────────────┘
                            ↓
            Frontend stores token
            Includes in all requests:
            Authorization: Bearer <token>
```

**Security Features:**
- Password validation (8+ chars, uppercase, lowercase, digit)
- Bcrypt hashing
- Rate limiting on login attempts
- JWT with 30-minute expiration
- User existence verified on every request

---

### 3️⃣ Conversational Matching Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 User Starts Conversation                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
                POST /chat/message
                {
                  "message": "I want a family dog",
                  "session_id": null  // First message
                }
                            ↓
                ┌───────────────────────┐
                │  Backend Creates:     │
                │  1. New session       │
                │  2. Ties to user_id   │
                │  3. Initializes state │
                └───────────────────────┘
                            ↓
                ┌───────────────────────┐
                │  Gemini AI Processes: │
                │  1. Extract prefs     │
                │  2. Ask follow-up     │
                │  3. Update profile    │
                └───────────────────────┘
                            ↓
                Returns: {
                  "message": "Great! Do you have kids?",
                  "session_id": "uuid",
                  "is_complete": false,
                  "user_profile": {...}
                }
                            ↓
        ┌───────────────────────────────────────┐
        │  User Continues Conversation          │
        │  (Multiple back-and-forth messages)   │
        └───────────────────────────────────────┘
                            ↓
                POST /chat/message
                {
                  "message": "Yes, 2 kids ages 5 and 8",
                  "session_id": "existing-uuid"
                }
                            ↓
                ┌───────────────────────┐
                │  AI Extracts More:    │
                │  - has_children: true │
                │  - child_ages: [5,8]  │
                │  - Asks next question │
                └───────────────────────┘
                            ↓
        ... Conversation continues until ...
                            ↓
                ┌───────────────────────┐
                │  Profile Complete!    │
                │  is_complete: true    │
                └───────────────────────┘
```

**Conversation Data Extracted:**
- Living situation (apartment, house, yard)
- Activity level (couch potato, active, very active)
- Experience level (first-time, experienced)
- Family composition (kids, other pets)
- Size preference (small, medium, large)
- Grooming tolerance
- Training commitment
- Special needs (allergies, etc.)

---

### 4️⃣ Breed Recommendation Flow

```
┌─────────────────────────────────────────────────────────────┐
│          Profile Complete → Get Recommendations              │
└─────────────────────────────────────────────────────────────┘
                            ↓
        GET /recommendations/{session_id}
        ?use_search=true
                            ↓
        ┌───────────────────────────────────────┐
        │  Backend Validates:                   │
        │  1. Session exists                    │
        │  2. User owns session (403 if not)    │
        │  3. Profile is complete               │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  Matching Engine:                     │
        │  1. Loads 195 breed dataset           │
        │  2. Scores each breed vs profile      │
        │  3. Ranks by compatibility            │
        │  4. Returns top 3 matches             │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  For Each Top 3 Breed:                │
        │  1. Get breed traits                  │
        │  2. Generate pros/cons                │
        │  3. Fetch 5 images                    │
        │  4. (Optional) Web research           │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  Content Generator:                   │
        │  Creates "Day in the Life" story      │
        │  for #1 recommended breed             │
        └───────────────────────────────────────┘
                            ↓
        Returns: {
          "top_three": [
            {
              "breed": {...},
              "match_score": 95,
              "explanations": [...],
              "pros": [...],
              "cons": [...],
              "images": [...]
            },
            // ... 2 more breeds
          ],
          "day_in_life_content": "...",
          "web_research": [...],
          "user_profile": {...}
        }
```

**Matching Algorithm:**
- Weighted scoring across 20+ attributes
- Considers dealbreakers (e.g., allergies → hypoallergenic only)
- Balances user preferences with breed characteristics
- Provides detailed explanations for each match

---

### 5️⃣ Video Generation Flow

```
┌─────────────────────────────────────────────────────────────┐
│        User Selects Breed → Generate Custom Video            │
└─────────────────────────────────────────────────────────────┘
                            ↓
        POST /video/generate
        {
          "session_id": "uuid",
          "breed_name": "Golden Retriever",
          "selected_image_urls": ["url1", "url2"]  // Max 2
        }
                            ↓
        ┌───────────────────────────────────────┐
        │  Backend Validates:                   │
        │  1. Session ownership                 │
        │  2. Breed exists in dataset           │
        │  3. Max 2 images (cost control)       │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  Gemini AI Video Generation:          │
        │  1. Creates personalized script       │
        │  2. Generates video with images       │
        │  3. Returns operation_id              │
        └───────────────────────────────────────┘
                            ↓
        Returns: {
          "video_url": "...",
          "status": "generating",
          "operation_id": "op-123",
          "estimated_time": 60
        }
                            ↓
        ┌───────────────────────────────────────┐
        │  Poll for Status:                     │
        │  GET /video/status/{operation_id}     │
        └───────────────────────────────────────┘
                            ↓
        Video ready → Display to user
```

---

### 6️⃣ User Management Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  Authenticated User Actions                  │
└─────────────────────────────────────────────────────────────┘

GET /users/me
├─ View profile
├─ Check API usage (calls_today, remaining)
└─ See preferences

PUT /users/me/preferences
├─ Update notification settings
├─ Save favorite breeds
└─ Set communication preferences

GET /users/me/sessions
├─ View conversation history
├─ Resume previous sessions
└─ See all past matches

GET /users/me/usage
├─ API calls today
├─ Daily limit (50 or 200)
└─ Reset time

DELETE /users/me
├─ GDPR compliance
├─ Deletes ALL data:
│   ├─ User account
│   ├─ All sessions
│   ├─ All messages
│   └─ All saved results
└─ Permanent & irreversible
```

---

## 🔄 Complete User Journey Example

### **Scenario: Sarah wants to find a dog**

**1. ARRIVAL**
```
└─ Sarah visits app
└─ Chooses "Register" (wants to save data)
└─ POST /users/register
   {
     "email": "sarah@example.com",
     "username": "Sarah",
     "password": "Sarah1234"
   }
└─ Receives user_id + confirmation
```

**2. LOGIN**
```
└─ POST /users/token
   Form data:
   username: sarah@example.com
   password: Sarah1234
└─ Receives JWT token (valid 30 min)
└─ Frontend stores token in localStorage/sessionStorage
```

**3. CONVERSATION** (Session: abc-123)
```
└─ POST /chat/message
   Headers: Authorization: Bearer <token>
   Body: {"message": "I want a family-friendly dog"}
└─ AI: "Great! Do you have children?"

└─ POST /chat/message
   Body: {"message": "Yes, ages 5 and 8", "session_id": "abc-123"}
└─ AI: "Do you have a yard?"

└─ POST /chat/message
   Body: {"message": "Yes, large fenced yard", "session_id": "abc-123"}
└─ AI: "How active are you?"

└─ POST /chat/message
   Body: {"message": "We hike every weekend", "session_id": "abc-123"}
└─ AI: "Any allergies?"

└─ POST /chat/message
   Body: {"message": "No allergies", "session_id": "abc-123"}
└─ AI: "Perfect! I have enough info"
   Response: is_complete: true
```

**4. RECOMMENDATIONS**
```
└─ GET /recommendations/abc-123?use_search=true
   Headers: Authorization: Bearer <token>
└─ Returns:
   #1: Golden Retriever (98% match)
       Pros: Family-friendly, active, trainable
       Cons: Heavy shedding, needs grooming
       
   #2: Labrador Retriever (96% match)
       Pros: Great with kids, energetic
       Cons: Can be mouthy, needs exercise
       
   #3: Australian Shepherd (94% match)
       Pros: Intelligent, athletic
       Cons: Needs mental stimulation
```

**5. VIDEO GENERATION**
```
└─ Sarah loves Golden Retriever
└─ POST /video/generate
   Headers: Authorization: Bearer <token>
   Form data:
   session_id: "abc-123"
   breed_name: "Golden Retriever"
   selected_image_urls: ["url1", "url2"]
└─ Returns operation_id: "op-xyz"

└─ Poll GET /video/status/op-xyz
   Headers: Authorization: Bearer <token>
└─ Status: "generating" → "complete"
└─ Video ready!
└─ Watches personalized "Day in the Life"
```

**6. SAVE & SHARE**
```
└─ Sarah saves her results
└─ Shares with family
└─ Decides to adopt!
```

---

## 🔐 Security Throughout Workflow

### **Every Protected Request:**
```
1. Client sends: Authorization: Bearer <jwt_token>
2. Backend validates:
   ├─ Token signature valid?
   ├─ Token not expired?
   ├─ User exists in database?
   └─ User owns requested resource?
3. If all pass → Process request
4. If any fail → 401/403 error
```

### **Rate Limiting:**
```
Anonymous Users: 50 API calls/day
Registered Users: 200 API calls/day
Login Attempts: Rate limited per user

Tracked per user, resets daily at midnight UTC
```

---

## 📊 Data Flow Architecture

```
┌─────────────┐
│   Frontend  │
│  (React)    │
└──────┬──────┘
       │ HTTP/REST + JWT
       ↓
┌─────────────────────────────────────┐
│         FastAPI Backend             │
│  ┌─────────────────────────────┐   │
│  │  Authentication Layer       │   │
│  │  (JWT validation)           │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  API Endpoints              │   │
│  │  /users, /chat, /recs, etc  │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  Business Logic             │   │
│  │  - ConversationAgent        │   │
│  │  - MatchingEngine           │   │
│  │  - ContentGenerator         │   │
│  └─────────────────────────────┘   │
└───────┬─────────────┬───────────────┘
        │             │
        ↓             ↓
┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │  Gemini AI   │
│  (User data, │  │  (NLP, Video)│
│   Sessions,  │  │              │
│   Messages)  │  │              │
└──────────────┘  └──────────────┘
```

---

## 🎯 Key Features

✅ **Anonymous & Registered Users**  
✅ **Conversational AI matching**  
✅ **195 breed dataset**  
✅ **Personalized recommendations**  
✅ **Custom video generation**  
✅ **Session persistence**  
✅ **Rate limiting**  
✅ **GDPR compliance**  
✅ **Secure authentication**  
✅ **Cross-session memory**

---

## 🧪 API Testing Guide

### **1. Test User Registration**
```bash
curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "TestUser",
    "password": "Test1234"
  }'
```

### **2. Test Login**
```bash
curl -X POST http://localhost:8000/users/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=Test1234"
```

### **3. Test Protected Endpoint**
```bash
# Replace <TOKEN> with actual JWT from login
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer <TOKEN>"
```

### **4. Test Chat Flow**
```bash
# Start conversation
curl -X POST http://localhost:8000/chat/message \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want a family dog",
    "session_id": null
  }'

# Continue conversation (use session_id from response)
curl -X POST http://localhost:8000/chat/message \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Yes, I have 2 kids",
    "session_id": "<SESSION_ID>"
  }'
```

### **5. Test Recommendations**
```bash
curl -X GET http://localhost:8000/recommendations/<SESSION_ID> \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 📱 Frontend Integration Checklist

### **Required Environment Variables**
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_TIMEOUT=30000
```

### **Authentication Setup**
- [ ] Store JWT token in localStorage or secure cookie
- [ ] Include token in all API requests: `Authorization: Bearer <token>`
- [ ] Handle 401 errors (redirect to login)
- [ ] Handle 403 errors (show "access denied")
- [ ] Implement token refresh or re-login on expiration

### **API Client Configuration**
```javascript
// Example axios setup
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  timeout: 30000,
});

// Add token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('jwt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      localStorage.removeItem('jwt_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### **Key API Endpoints for Frontend**

**Authentication:**
- `POST /users/register` - User registration
- `POST /users/token` - Login (returns JWT)
- `POST /users/anonymous` - Create anonymous user
- `GET /users/me` - Get current user profile

**Chat:**
- `POST /chat/message` - Send message, get AI response
- `GET /chat/session/{session_id}` - Get session details

**Recommendations:**
- `GET /recommendations/{session_id}` - Get top 3 breed matches

**Video:**
- `POST /video/generate` - Generate custom video
- `GET /video/status/{operation_id}` - Check video status

**User Management:**
- `GET /users/me/sessions` - Get user's sessions
- `GET /users/me/usage` - Get API usage stats
- `PUT /users/me/preferences` - Update preferences
- `DELETE /users/me` - Delete account

---

## 🚂 Railway Deployment

See `RAILWAY_DEPLOYMENT.md` for complete deployment guide.

---

This is the complete workflow from user arrival to getting personalized dog breed recommendations with custom videos!
