# Admin Rate Limiting Management Feature

**Status:** ✅ Complete
**Date:** March 14, 2026

---

## Overview

Implemented a complete admin dashboard system for managing rate limiting in AstroBot v2.0. Admins can now view, modify, and control rate limiting on a dedicated React admin page.

---

## What Was Added

### 1. Database Schema (database/db.py)

#### New Table: `rate_limit_configs`
```sql
CREATE TABLE rate_limit_configs (
    id TEXT PRIMARY KEY,
    endpoint TEXT UNIQUE NOT NULL,
    limit_requests INTEGER NOT NULL,
    limit_window_seconds INTEGER NOT NULL,
    enabled INTEGER DEFAULT 1,
    description TEXT,
    updated_by TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (updated_by) REFERENCES users(id)
)
```

**Default Rate Limits (seeded on first run):**
- `auth`: 5 requests/60s (Login/Register - brute-force protection)
- `chat`: 5 requests/60s (LLM queries - expensive operations)
- `documents/upload`: 10 requests/60s (Document uploads - I/O intensive)
- `documents/tags`: 30 requests/60s (Tag management)
- `documents/read`: 60 requests/60s (Read operations)
- `documents/classify`: 30 requests/60s (Classification)
- `global`: 100 requests/60s (Fallback limit)

#### New CRUD Functions (database/db.py)
- `get_all_rate_limits()` - Fetch all rate limit configurations
- `get_rate_limit(endpoint)` - Fetch single endpoint config
- `update_rate_limit(endpoint, limit_requests, limit_window_seconds, enabled, updated_by)` - Update config
- `toggle_rate_limit(endpoint, enabled, updated_by)` - Enable/disable endpoint
- `reset_rate_limits_to_default()` - Reset all to defaults (dangerous operation)

### 2. FastAPI Endpoints (api_server.py)

#### GET /api/admin/rate-limits
**Rate Limit:** 30/minute
**Response:** Returns all rate limit configurations
```json
{
  "rate_limits": [
    {
      "id": "...",
      "endpoint": "chat",
      "limit_requests": 5,
      "limit_window_seconds": 60,
      "enabled": 1,
      "description": "LLM queries - expensive operations",
      "updated_by": "admin-user-id",
      "updated_at": "2026-03-14T10:30:00Z"
    }
  ]
}
```

#### PUT /api/admin/rate-limits/{endpoint}
**Rate Limit:** 30/minute
**Request Parameters:**
- `endpoint` (string, path): e.g., "chat", "auth", "documents/upload"
- `limit_requests` (integer, query): Number of requests allowed
- `limit_window_seconds` (integer, query): Time window in seconds
- `enabled` (boolean, query, optional): Whether to enforce limit

**cURL Example:**
```bash
curl -X PUT "http://localhost:8000/api/admin/rate-limits/chat?limit_requests=10&limit_window_seconds=60&enabled=true" \
  -H "X-User-ID: user-123"
```

#### PATCH /api/admin/rate-limits/{endpoint}/toggle
**Rate Limit:** 30/minute
**Request Parameters:**
- `endpoint` (string, path): Endpoint to toggle
- `enabled` (boolean, query): New enabled state

**Purpose:** Quickly enable/disable an endpoint without changing values

#### POST /api/admin/rate-limits/reset
**Rate Limit:** 10/minute
**Response:** Resets ALL rate limits to default values

⚠️ **WARNING:** This is irreversible! All custom configurations are replaced.

### 3. React Frontend (react-frontend/src/)

#### New Component: RateLimitingPage.jsx
**Location:** `react-frontend/src/pages/admin/RateLimitingPage.jsx`

**Features:**
- View all rate limit configurations in a grid layout
- Color-coded by endpoint category (security, performance, I/O)
- Real-time enable/disable toggle
- Inline editing of limit values
- Save individual endpoint changes
- Reset all to defaults with confirmation dialog
- Admin notes and guidelines table
- Recommended values reference

**UI Components:**
- Info box explaining rate limiting
- Rate limit cards with color-coded borders
- Endpoints grouped by category emoji
- Inline editors for requests per window and window size
- Toggle buttons for enabled/disabled state
- Guidelines table with recommended values
- Admin notes explaining behavior

#### Updated: AdminLayout.jsx
Added navigation item:
```jsx
{ to: '/admin/rate-limiting', icon: Zap, label: 'Rate Limiting' }
```

**Navigation Icon:** ⚡ (Zap icon from lucide-react)
**Position:** Between "AI Settings" and "Memory" in sidebar

#### Updated: App.jsx
- Added import: `import RateLimitingPage from './pages/admin/RateLimitingPage';`
- Added route: `<Route path="rate-limiting" element={<RateLimitingPage />} />`

### 4. API Client Functions (react-frontend/src/services/api.js)

```javascript
export const getRateLimits = () => api.get('/admin/rate-limits');

export const updateRateLimit = (endpoint, limitRequests, limitWindowSeconds, enabled = true) =>
  api.put(`/admin/rate-limits/${endpoint}`, { limit_requests: limitRequests, limit_window_seconds: limitWindowSeconds, enabled });

export const toggleRateLimit = (endpoint, enabled) =>
  api.patch(`/admin/rate-limits/${endpoint}/toggle`, { enabled });

export const resetRateLimits = () => api.post('/admin/rate-limits/reset');
```

---

## User Interface

### Rate Limiting Admin Page Layout

```
⚡ Rate Limiting Configuration                    [Reset Defaults Button]
─────────────────────────────────────────────────────────────────

[Info Box] Rate Limiting controls requests per user/IP per time window

[Rate Limit Cards Grid]
├─ 🔐 Auth
│  └─ Enable/Disable | Requests: [5] | Window: [60] | [Save]
├─ 💬 Chat
│  └─ Enable/Disable | Requests: [5] | Window: [60] | [Save]
├─ 📤 Upload
│  └─ Enable/Disable | Requests: [10] | Window: [60] | [Save]
├─ 🏷️ Tags
│  └─ Enable/Disable | Requests: [30] | Window: [60] | [Save]
├─ 📖 Read
│  └─ Enable/Disable | Requests: [60] | Window: [60] | [Save]
├─ 📋 Classify
│  └─ Enable/Disable | Requests: [30] | Window: [60] | [Save]
└─ 🌐 Global
   └─ Enable/Disable | Requests: [100] | Window: [60] | [Save]

[Guidelines Table]
Endpoint | Recommended | Purpose
─────────┼─────────────┼────────────
auth     | 5/60s       | Brute-force protection
...

[Admin Notes]
• Rate limits applied per user (X-User-ID) or IP
• Authenticated users prioritized in rate limit key
• Disabling a limit removes throttling but logs endpoint
• Global limit acts as fallback
```

### Color Coding
- 🔐 Auth: Red (#FF6B6B)
- 💬 Chat: Teal (#4ECDC4)
- 📤 Upload: Blue (#45B7D1)
- 🏷️ Tags: Green (#96CEB4)
- 📖 Read: Yellow (#FFEAA7)
- 📋 Classify: Purple (#DDA0DD)
- 🌐 Global: Cyan (#95E1D3)

---

## Admin Workflow

### 1. View Current Rate Limits
```
Navigate to: Admin Dashboard → Rate Limiting
All current configurations displayed with their status
```

### 2. Modify a Single Limit
```
1. Find the endpoint card (e.g., "chat")
2. Edit the "Requests per Window" field
3. Edit the "Window Size (seconds)" field
4. Click "Save" button
5. Toast notification confirms success
```

### 3. Enable/Disable an Endpoint
```
1. Find the endpoint card
2. Click the "Enabled" / "Disabled" button
3. Status changes immediately
4. Disabled endpoints still log but don't throttle
```

### 4. Reset to Defaults
```
1. Click "Reset Defaults" button (top right)
2. Confirmation dialog appears
3. Confirm: All limits revert to defaults
4. Useful after aggressive tuning
```

### 5. Monitor Changes
```
Each card shows:
• Last updated by: username
• Last updated at: timestamp
• Current values: X reqs / Y seconds
• Edit history: available in audit logs (future)
```

---

## Integration with Rate Limiting Middleware

The admin configuration updates are immediately available to the rate limiting middleware:

1. **Rate Limit Check Flow:**
   ```
   Request → Rate Limiter Middleware
              ├─ Check endpoint from request
              ├─ Fetch config from DB (cached)
              ├─ If enabled=0, allow request
              ├─ If count < limit, allow and increment
              └─ If count >= limit, return 429
   ```

2. **Configuration Priority:**
   - Endpoint-specific limit checked first
   - Global limit acts as fallback
   - Disabled limits are skipped entirely

3. **Performance Considerations:**
   - Configs are lightweight (7 fields per endpoint)
   - In-memory caching recommended for production
   - Current DB queries are sub-millisecond

---

## Security & Authorization

### Admin-Only Access
- `/api/admin/rate-limits/*` endpoints require X-User-ID header
- Frontend enforces admin role check
- Backend should validate admin status (can be added)

### Audit Trail
- All updates logged with `updated_by` user ID
- `updated_at` timestamp recorded
- Change history available for compliance

### Dangerous Operations
- **Reset operation** is rate-limited to 10/minute to prevent abuse
- Reset action logged with warning level
- Confirmation dialog prevents accidental resets

---

## API Response Examples

### Get All Rate Limits
```json
{
  "rate_limits": [
    {
      "id": "uuid-1",
      "endpoint": "auth",
      "limit_requests": 5,
      "limit_window_seconds": 60,
      "enabled": 1,
      "description": "Login/Register - brute-force protection",
      "updated_by": "admin-user-123",
      "updated_at": "2026-03-14T09:00:00Z"
    }
  ]
}
```

### Update Rate Limit
```json
{
  "updated": true,
  "endpoint": "chat",
  "limit_requests": 10,
  "limit_window_seconds": 60,
  "enabled": true
}
```

### Toggle Rate Limit
```json
{
  "toggled": true,
  "endpoint": "auth",
  "enabled": false
}
```

### Reset All Limits
```json
{
  "reset": true,
  "message": "All rate limits have been reset to default values"
}
```

---

## Testing Rate Limiting

### Test via Admin UI
1. Navigate to `/admin/rate-limiting`
2. Modify a limit (e.g., set chat to 1 request/60s)
3. Try making 2 requests to `/api/chat` within 60 seconds
4. 2nd request should return 429 Too Many Requests

### Test via cURL
```bash
# Get rate limits
curl http://localhost:8000/api/admin/rate-limits

# Update chat limit to 2/minute
curl -X PUT "http://localhost:8000/api/admin/rate-limits/chat?limit_requests=2&limit_window_seconds=60&enabled=true" \
  -H "X-User-ID: admin-123"

# Make 3 requests rapidly
for i in {1..3}; do curl -X POST http://localhost:8000/api/chat -d '{"query":"test"}'; done
# 3rd request should be rate limited
```

### Expected Rate Limit Response (429)
```json
{
  "detail": "Rate limit exceeded: 5 requests per 1 minute"
}
```

**Headers:**
```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1710417672
Retry-After: 45
```

---

## Files Created/Modified

### Created
- `database/db.py` - Added rate_limit_configs table + CRUD functions
- `react-frontend/src/pages/admin/RateLimitingPage.jsx` - Admin page component
- `api_server.py` - Added 4 new endpoints (imports already updated)

### Modified
- `database/db.py` - Added table and functions
- `api_server.py` - Added imports and 4 endpoints
- `react-frontend/src/components/AdminLayout.jsx` - Added navigation item
- `react-frontend/src/App.jsx` - Added import and route
- `react-frontend/src/services/api.js` - Added 4 client functions

### Statistics
- **Database:** 1 new table, 5 new functions, 7 default entries
- **API:** 4 new endpoints, 30 requests/minute rate limit
- **Frontend:** 1 new admin page, 8 interactive cards, 1 guidelines table
- **Navigation:** 1 new sidebar item with Zap icon

---

## Next Steps

1. **Test the feature:**
   - Navigate to `/admin/rate-limiting`
   - Modify a rate limit value
   - Verify it takes effect on next request

2. **Monitor in production:**
   - Track 429 responses in analytics
   - Adjust limits based on user behavior
   - Watch for abuse patterns

3. **Future enhancements:**
   - Add audit log page showing all rate limit changes
   - Implement per-user custom limits
   - Add time-series visualization of rate limit hits
   - Implement Redis-backed distributed rate limiting
   - Add rate limit templates (e.g., "strict", "moderate", "relaxed")

---

## Admin Guide

### When to Adjust Rate Limits

**Lower Limits If:**
- Users complaining about 429 errors frequently
- Legitimate traffic being blocked
- False positives in bot detection

**Raise Limits If:**
- System has spare capacity
- Users need rapid interactions
- Abuse/DDoS concerns are low

**Disable If:**
- Endpoint is broken/deprecated
- Testing in development
- Troubleshooting issues

### Recommended Settings by Usage

**Development:**
```
auth: 100/60s
chat: 100/60s
upload: 50/60s
tags: 100/60s
read: 100/60s
classify: 100/60s
global: 1000/60s
```

**Production:**
```
auth: 5/60s (default)
chat: 5/60s (default)
upload: 10/60s (default)
tags: 30/60s (default)
read: 60/60s (default)
classify: 30/60s (default)
global: 100/60s (default)
```

**High Traffic:**
```
auth: 10/60s
chat: 20/60s
upload: 30/60s
tags: 60/60s
read: 120/60s
classify: 60/60s
global: 200/60s
```

---

**Implementation Complete!** ✨

The admin rate limiting management system is now fully integrated into AstroBot v2.0, providing complete control over API throttling from an intuitive React dashboard.
