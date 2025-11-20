# Security Implementation Guide

## Overview
This document outlines the security measures implemented in the PawMatch backend API and provides guidance for maintaining security in production.

## Authentication & Authorization

### JWT-Based Authentication
- **Token Type**: JWT (JSON Web Tokens)
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Token Expiration**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Token URL**: `/users/token` (OAuth2 compatible)

### Password Security
- **Hashing Algorithm**: bcrypt (via passlib)
- **Password Requirements**:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  
### User Authentication Flow
1. User registers with email and password (`POST /users/register`)
2. Password is validated for strength
3. Password is hashed using bcrypt
4. User logs in with credentials (`POST /users/token`)
5. Server returns JWT access token
6. Client includes token in `Authorization: Bearer <token>` header
7. Protected endpoints validate token and fetch user from database

## Protected Endpoints

All endpoints requiring authentication use the `get_current_user` dependency:

### User Endpoints
- `GET /users/me` - Get current user profile
- `PUT /users/me/preferences` - Update user preferences
- `GET /users/me/sessions` - Get user's sessions
- `GET /users/me/usage` - Get API usage statistics
- `DELETE /users/me` - Delete user data (GDPR compliance)

### Chat Endpoints
- `POST /chat/message` - Send chat message
- `GET /chat/session/{session_id}` - Get session details

### Recommendation Endpoints
- `GET /recommendations/{session_id}` - Get breed recommendations

### Video Endpoints
- `POST /video/generate` - Generate custom video
- `GET /video/status/{operation_id}` - Check video status

## Security Features Implemented

### 1. Complete User Validation
- JWT tokens are validated on every request
- User existence is verified in database (prevents deleted users from accessing API)
- Session ownership is verified (users can only access their own sessions)

### 2. Rate Limiting
- **Anonymous users**: 50 API calls per day
- **Registered users**: 200 API calls per day
- **Login endpoint**: Rate limited to prevent brute force attacks
- Rate limits reset daily

### 3. Password Validation
- Enforces strong password requirements
- Validates on registration and account upgrade
- Returns clear error messages for weak passwords

### 4. Secure Token Generation
- Uses timezone-aware datetime (Python 3.12+ compatible)
- Tokens include expiration timestamp
- Secret key must be provided via environment variables

### 5. Authorization Checks
- Session ownership verification on all session-based endpoints
- Returns 403 Forbidden if user tries to access another user's data
- Returns 401 Unauthorized for invalid/expired tokens

## Environment Variables

### Required Variables
```bash
SECRET_KEY=<strong-random-secret>  # REQUIRED - No default value
GEMINI_API_KEY=<your-api-key>
DATABASE_URL=<postgresql-connection-string>
```

### Optional Variables (with defaults)
```bash
REDIS_URL=redis://localhost:6379/0
FRONTEND_URL=http://localhost:3000
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=False
```

## Production Deployment Checklist

### Critical Security Steps

1. **Generate Strong SECRET_KEY**
   ```bash
   openssl rand -hex 32
   ```
   - Add to `.env` file
   - NEVER commit to version control
   - Use different keys for dev/staging/production

2. **Environment Variables**
   - Set all required environment variables
   - Use secrets management service (AWS Secrets Manager, Azure Key Vault, etc.)
   - Never hardcode sensitive values

3. **Database Security**
   - Use strong database passwords
   - Enable SSL/TLS for database connections
   - Restrict database access to application servers only
   - Regular backups with encryption

4. **HTTPS/TLS**
   - Enable HTTPS in production
   - Use valid SSL certificates (Let's Encrypt, etc.)
   - Redirect HTTP to HTTPS
   - Enable HSTS headers

5. **CORS Configuration**
   - Set `FRONTEND_URL` to your actual frontend domain
   - Don't use wildcard (`*`) in production
   - Validate origin headers

6. **Rate Limiting**
   - Consider adding additional rate limiting at API gateway level
   - Monitor for abuse patterns
   - Implement IP-based rate limiting for login attempts

7. **Logging & Monitoring**
   - Log authentication failures
   - Monitor for suspicious activity
   - Set up alerts for security events
   - Don't log sensitive data (passwords, tokens)

8. **Dependencies**
   - Keep all dependencies up to date
   - Run security audits: `pip-audit`
   - Monitor for CVEs

9. **API Documentation**
   - Disable `/docs` and `/redoc` in production (or add authentication)
   - Use API keys for external access if needed

10. **Database Migrations**
    - Review all migrations before applying
    - Test in staging environment first
    - Backup database before migrations

## Security Best Practices

### For Developers

1. **Never commit secrets**
   - Add `.env` to `.gitignore`
   - Use `.env.example` for documentation
   - Rotate keys if accidentally committed

2. **Input Validation**
   - All user inputs are validated via Pydantic models
   - SQL injection prevented by SQLAlchemy ORM
   - XSS prevention via proper output encoding

3. **Error Handling**
   - Don't expose stack traces in production
   - Use generic error messages for authentication failures
   - Log detailed errors server-side only

4. **Session Management**
   - Sessions are tied to users
   - Session IDs are UUIDs (not sequential)
   - Sessions can be invalidated by deleting user

5. **Password Reset** (TODO)
   - Implement secure password reset flow
   - Use time-limited tokens
   - Send reset links via email only

### For Operators

1. **Regular Security Audits**
   - Review access logs
   - Check for failed login attempts
   - Monitor API usage patterns

2. **Incident Response**
   - Have a plan for security incidents
   - Know how to revoke tokens (change SECRET_KEY)
   - Document incident response procedures

3. **Backup & Recovery**
   - Regular database backups
   - Test restore procedures
   - Encrypt backups

## Known Limitations & Future Improvements

### Current Limitations
1. **No Token Refresh**: Users must re-authenticate after 30 minutes
2. **No Token Revocation**: Cannot invalidate individual tokens (only by changing SECRET_KEY)
3. **No Password Reset**: Users cannot reset forgotten passwords
4. **No Email Verification**: Email addresses are not verified
5. **No 2FA**: Two-factor authentication not implemented
6. **No Account Lockout**: No automatic lockout after failed login attempts

### Planned Improvements
1. Implement refresh tokens for longer sessions
2. Add token blacklist for revocation
3. Implement password reset via email
4. Add email verification on registration
5. Optional 2FA for enhanced security
6. Account lockout after N failed attempts
7. Security headers (CSP, X-Frame-Options, etc.)
8. API key authentication for service-to-service calls

## Compliance

### GDPR Compliance
- Users can delete all their data via `DELETE /users/me`
- Cascade deletion removes all associated data:
  - User account
  - All sessions
  - All chat messages
  - All saved results
  - Cross-session memory

### Data Retention
- User data is retained until user deletes account
- Sessions persist indefinitely (consider adding expiration)
- API usage counters reset daily

## Security Contact

For security issues or questions:
1. Do not open public GitHub issues for security vulnerabilities
2. Contact the security team directly
3. Allow reasonable time for fixes before disclosure

## Audit Log

| Date | Change | Author |
|------|--------|--------|
| 2024-11-16 | Initial security implementation | PawMatch Team |
| 2024-11-16 | Added password validation | Security Audit |
| 2024-11-16 | Fixed get_current_user to fetch from DB | Security Audit |
| 2024-11-16 | Added rate limiting to login | Security Audit |
| 2024-11-16 | Made SECRET_KEY required | Security Audit |
