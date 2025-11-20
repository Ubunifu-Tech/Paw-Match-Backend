# Frontend Integration Guide - PawMatch

## 🎯 Overview

This guide provides everything the frontend team needs to integrate with the PawMatch backend API. All security features are implemented and tested.

---

## 🔐 Authentication Setup

### Environment Variables

Create `.env.local` in your frontend root:

```env
NEXT_APP_API_URL=http://localhost:8000
NEXT_APP_API_TIMEOUT=30000
```

For production (Railway):
```env
NEXT_APP_API_URL=https://your-app.up.railway.app
```

### API Client Configuration

```typescript
// lib/api-client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_APP_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('pawmatch_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - Handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('pawmatch_token');
      localStorage.removeItem('pawmatch_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

## 📡 API Endpoints Reference

### **Authentication Endpoints**

#### 1. Register User
```typescript
POST /users/register

Request:
{
  "email": "user@example.com",
  "username": "JohnDoe",  // Optional
  "password": "SecurePass123"  // Min 8 chars, uppercase, lowercase, digit
}

Response (200):
{
  "user_id": "uuid",
  "email": "user@example.com",
  "username": "JohnDoe",
  "is_anonymous": false,
  "preferences": {},
  "cross_session_memory": {},
  "api_usage": {
    "calls_today": 0,
    "daily_limit": 200,
    "remaining": 200,
    "user_type": "registered"
  },
  "created_at": "2024-11-16T..."
}

Errors:
- 400: Email already exists or weak password
```

#### 2. Login
```typescript
POST /users/token

Request (form-data):
{
  "username": "user@example.com",  // Note: field is 'username' but value is email
  "password": "SecurePass123"
}

Response (200):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

Errors:
- 401: Incorrect credentials
- 429: Too many login attempts
```

#### 3. Create Anonymous User
```typescript
POST /users/anonymous

Request: (empty)

Response (200):
{
  "user_id": "uuid",
  "is_anonymous": true,
  "api_usage": {
    "calls_today": 0,
    "daily_limit": 50,
    "remaining": 50,
    "user_type": "anonymous"
  }
}
```

#### 4. Upgrade Anonymous to Registered
```typescript
POST /users/upgrade

Request:
{
  "user_id": "uuid",
  "email": "user@example.com",
  "username": "JohnDoe",  // Optional
  "password": "SecurePass123"
}

Response (200):
{
  // Same as register response
}

Errors:
- 400: Email exists, user not found, or weak password
```

### **User Management Endpoints** (Protected)

All require `Authorization: Bearer <token>` header.

#### 5. Get Current User
```typescript
GET /users/me

Response (200):
{
  "user_id": "uuid",
  "email": "user@example.com",
  "username": "JohnDoe",
  "is_anonymous": false,
  "preferences": {},
  "cross_session_memory": {},
  "api_usage": {...},
  "created_at": "2024-11-16T..."
}

Errors:
- 401: Unauthorized (invalid/expired token)
```

#### 6. Update Preferences
```typescript
PUT /users/me/preferences

Request:
{
  "preferences": {
    "notifications": true,
    "theme": "dark",
    "favorite_breeds": ["Golden Retriever", "Labrador"]
  }
}

Response (200):
{
  // Updated user object
}
```

#### 7. Get User Sessions
```typescript
GET /users/me/sessions?limit=10

Response (200):
[
  {
    "session_id": "uuid",
    "is_complete": true,
    "created_at": "2024-11-16T...",
    "updated_at": "2024-11-16T...",
    "message_count": 12
  }
]
```

#### 8. Get API Usage
```typescript
GET /users/me/usage

Response (200):
{
  "calls_today": 45,
  "daily_limit": 200,
  "remaining": 155,
  "reset_at": "2024-11-17T00:00:00Z",
  "user_type": "registered"
}
```

#### 9. Delete Account (GDPR)
```typescript
DELETE /users/me

Response (200):
{
  "message": "All user data has been permanently deleted",
  "user_id": "uuid"
}
```

### **Chat Endpoints** (Protected)

#### 10. Send Message
```typescript
POST /chat/message

Request:
{
  "message": "I want a family-friendly dog",
  "session_id": null  // null for first message, uuid for continuing
}

Response (200):
{
  "message": "Great! Do you have children at home?",
  "session_id": "uuid",
  "is_complete": false,
  "user_profile": {
    "family_friendly": true,
    // ... other extracted preferences
  }
}

Errors:
- 401: Unauthorized
- 429: Rate limit exceeded
```

#### 11. Get Session
```typescript
GET /chat/session/{session_id}

Response (200):
{
  "history": [
    {"role": "user", "content": "I want a family dog"},
    {"role": "assistant", "content": "Great! Do you have children?"}
  ],
  "profile": {...},
  "is_complete": false
}

Errors:
- 401: Unauthorized
- 403: Not your session
- 404: Session not found
```

### **Recommendation Endpoints** (Protected)

#### 12. Get Recommendations
```typescript
GET /recommendations/{session_id}?use_search=true

Response (200):
{
  "session_id": "uuid",
  "top_three": [
    {
      "breed": {
        "breed": "Golden Retriever",
        "traits": {...},
        "images": ["url1", "url2", ...]
      },
      "match_score": 98,
      "explanations": [
        "Excellent with children",
        "Moderate energy matches your lifestyle"
      ],
      "pros": ["Family-friendly", "Trainable", "Gentle"],
      "cons": ["Heavy shedding", "Needs grooming"]
    },
    // ... 2 more breeds
  ],
  "user_profile": {...},
  "day_in_life_content": "Imagine waking up to...",
  "web_research": [...],  // If use_search=true
  "data_source": "195 breeds from curated dataset + web research"
}

Errors:
- 401: Unauthorized
- 403: Not your session
- 404: Session or profile not found
```

### **Video Endpoints** (Protected)

#### 13. Generate Video
```typescript
POST /video/generate

Request (form-data):
{
  "session_id": "uuid",
  "breed_name": "Golden Retriever",
  "selected_image_urls": ["url1", "url2"]  // Max 2 images
}

Response (200):
{
  "video_url": "https://...",
  "status": "generating",  // or "complete"
  "operation_id": "op-123",
  "images_used": ["url1", "url2"],
  "estimated_time": 60,
  "message": "Video generation generating for Golden Retriever"
}

Errors:
- 400: Max 2 images exceeded
- 401: Unauthorized
- 403: Not your session
- 404: Session or breed not found
- 500: Video generation failed
```

#### 14. Check Video Status
```typescript
GET /video/status/{operation_id}

Response (200):
{
  "status": "complete",  // or "generating", "failed"
  "video_url": "https://...",
  "operation_id": "op-123"
}

Errors:
- 401: Unauthorized
- 500: Status check failed
```

---

## 🔑 Authentication Flow Implementation

### React Hook for Authentication

```typescript
// hooks/useAuth.ts
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

interface User {
  user_id: string;
  email: string;
  username: string;
  is_anonymous: boolean;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    // Load from localStorage on mount
    const savedToken = localStorage.getItem('pawmatch_token');
    const savedUser = localStorage.getItem('pawmatch_user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const register = async (email: string, password: string, username?: string) => {
    const response = await apiClient.post('/users/register', {
      email,
      password,
      username,
    });
    
    // Auto-login after registration
    return login(email, password);
  };

  const login = async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await apiClient.post('/users/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const { access_token } = response.data;
    
    // Get user profile
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    const userResponse = await apiClient.get('/users/me');
    
    // Save to localStorage
    localStorage.setItem('pawmatch_token', access_token);
    localStorage.setItem('pawmatch_user', JSON.stringify(userResponse.data));
    
    setToken(access_token);
    setUser(userResponse.data);
    
    return userResponse.data;
  };

  const createAnonymous = async () => {
    const response = await apiClient.post('/users/anonymous');
    const anonymousUser = response.data;
    
    // Save anonymous user (no token needed for some endpoints)
    localStorage.setItem('pawmatch_user', JSON.stringify(anonymousUser));
    setUser(anonymousUser);
    
    return anonymousUser;
  };

  const logout = () => {
    localStorage.removeItem('pawmatch_token');
    localStorage.removeItem('pawmatch_user');
    setToken(null);
    setUser(null);
  };

  return {
    user,
    token,
    loading,
    isAuthenticated: !!token,
    isAnonymous: user?.is_anonymous ?? true,
    register,
    login,
    createAnonymous,
    logout,
  };
}
```

### Protected Route Component

```typescript
// components/ProtectedRoute.tsx
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
```

---

## 💬 Chat Integration Example

```typescript
// components/ChatInterface.tsx
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user' as const, content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await apiClient.post('/chat/message', {
        message: input,
        session_id: sessionId,
      });

      const { message, session_id, is_complete } = response.data;
      
      setSessionId(session_id);
      setIsComplete(is_complete);
      setMessages(prev => [...prev, { role: 'assistant', content: message }]);

      if (is_complete) {
        // Redirect to recommendations
        window.location.href = `/recommendations/${session_id}`;
      }
    } catch (error) {
      console.error('Chat error:', error);
      // Handle error (show toast, etc.)
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] rounded-lg p-3 ${
                msg.role === 'user'
                  ? 'bg-gray-200 text-gray-900'
                  : 'bg-blue-500 text-white'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && <div>AI is typing...</div>}
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border rounded-lg"
            disabled={loading || isComplete}
          />
          <button
            onClick={sendMessage}
            disabled={loading || isComplete}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## 🎨 UI Integration Checklist

Based on your frontend design docs:

### **Required Components**

- [x] Navbar with auth state
- [x] Hero section with CTAs
- [x] BreedCard component
- [x] FilterSidebar component
- [x] ChatInterface component
- [x] ProfileSidebar component
- [x] MatchResultCard component
- [x] TraitBarChart component
- [x] VideoPlayer component
- [x] ImageGallery component

### **API Integration Points**

- [x] User registration/login forms
- [x] Anonymous user creation
- [x] Chat message sending
- [x] Recommendations fetching
- [x] Video generation
- [x] Session management
- [x] User profile updates

### **State Management**

```typescript
// stores/authStore.ts (Zustand)
import create from 'zustand';

interface AuthState {
  user: User | null;
  token: string | null;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),
  logout: () => set({ user: null, token: null }),
}));
```

---

## 🚨 Error Handling

### Standard Error Responses

```typescript
// All errors follow this format
{
  "detail": "Error message here"
}

// Status codes:
// 400: Bad Request (validation errors)
// 401: Unauthorized (invalid/missing token)
// 403: Forbidden (not authorized for resource)
// 404: Not Found
// 429: Too Many Requests (rate limit)
// 500: Internal Server Error
```

### Error Handling Example

```typescript
try {
  const response = await apiClient.post('/chat/message', data);
  // Handle success
} catch (error) {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const message = error.response?.data?.detail || 'An error occurred';
    
    switch (status) {
      case 400:
        toast.error(`Validation error: ${message}`);
        break;
      case 401:
        toast.error('Please log in to continue');
        router.push('/login');
        break;
      case 403:
        toast.error('You do not have access to this resource');
        break;
      case 429:
        toast.error('Rate limit exceeded. Please try again later.');
        break;
      default:
        toast.error(message);
    }
  }
}
```

---

## 📊 Rate Limiting

### Limits
- **Anonymous users**: 50 API calls per day
- **Registered users**: 200 API calls per day
- **Login attempts**: Rate limited per user

### Display Usage

```typescript
const { data: usage } = useQuery('apiUsage', async () => {
  const response = await apiClient.get('/users/me/usage');
  return response.data;
});

// Show in UI
<div>
  API Usage: {usage.calls_today} / {usage.daily_limit}
  <ProgressBar value={(usage.calls_today / usage.daily_limit) * 100} />
</div>
```

---

## 🧪 Testing the Integration

### 1. Start Backend
```bash
cd backend
uvicorn app.main:app --reload
```

### 2. Run Test Script
```bash
python3 test_complete_workflow.py
```

### 3. Manual Testing Checklist

- [ ] User can register with valid password
- [ ] Weak passwords are rejected
- [ ] User can login and receive token
- [ ] Token is included in subsequent requests
- [ ] Protected endpoints return 401 without token
- [ ] Chat conversation works end-to-end
- [ ] Recommendations are fetched correctly
- [ ] Session ownership is enforced (403 for other users)
- [ ] Rate limiting works
- [ ] User can delete account

---

## 🚀 Deployment

### Frontend Environment Variables (Production)

```env
NEXT_APP_API_URL=https://your-backend.up.railway.app
NEXT_APP_ENVIRONMENT=production
```

### CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:3000` (development)
- Your production frontend URL (set via `FRONTEND_URL` env var)

Make sure to update `FRONTEND_URL` in Railway to your actual frontend domain.

---

## 📚 Additional Resources

- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Application Workflow**: See `APPLICATION_WORKFLOW.md`
- **Security Details**: See `SECURITY.md`
- **Railway Deployment**: See `RAILWAY_DEPLOYMENT.md`
- **Frontend Design**: See `FRONTEND_UI_DESIGN_PART1.md` and `PART2.md`

---

## 🆘 Common Issues & Solutions

### Issue: CORS Error
**Solution**: Ensure `FRONTEND_URL` is set correctly in backend environment variables.

### Issue: 401 Unauthorized
**Solution**: Check that token is being sent in `Authorization: Bearer <token>` header.

### Issue: Token Expired
**Solution**: Tokens expire after 30 minutes. Implement token refresh or re-login.

### Issue: Rate Limit Exceeded
**Solution**: Show user their usage and upgrade prompt for anonymous users.

### Issue: Session Not Found (403)
**Solution**: User trying to access another user's session. Verify session ownership.

---

Your frontend is now ready to integrate with the secure PawMatch backend! 🎉
