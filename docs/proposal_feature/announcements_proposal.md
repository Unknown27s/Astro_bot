# Discord-Style Institutional Announcements Feature: Proposal & Implementation Plan

## Problem Statement
The institution needs a reliable way to broadcast important updates (e.g., event schedules, holidays, emergencies) to all students via the AstroBot platform. The current chat interface only supports conversational RAG, with no centralized location for global announcements.

## Solution
Introduce an Announcements Feature accessible from the Chat Page, resembling a Discord announcements channel. Students will view announcements, while Faculty and Admins can easily create them directly from the chat interface using AI formatting.

## Workflows

### 1. Announcement Creation (Faculty/Admin Only)
- A faculty member or admin logs into AstroBot.
- They type an announcement trigger into the chat: `@Announcement Tomorrow there is a holiday due to heavy rain. Classes will resume the day after.`
- The backend intercepts the `@Announcement` tag.
- It verifies the user's role. If the user is a student, the request is rejected as unauthorized, and the `@Announcement` autocomplete option won't even appear for them.
- The raw text is sent directly to the LLM backend with a system prompt to format it into a professional, engaging institutional announcement (with suitable emojis).
- The LLM's response is captured and saved asynchronously to the `announcements` database table attached to that faculty member's profile.
- A success message with the formatted announcement preview is returned in the chat.

### 2. Announcement Retrieval & Display (All Users)
- When any user logs in, the React Frontend fetches the latest announcements from a new `/api/announcements` endpoint.
- Announcements are displayed in a right-side sliding panel or section on `ChatPage.jsx`.
- A notification badge (e.g., 🔴 1) appears in the corner if new announcements are available, grabbing the user's attention.
- Older announcements are kept indefinitely (no automatic expiration or TTL). All students globally see the same announcements feed.

## Architectural Changes

### Database Layer (`database/db.py`)
- Define `announcements` table:
  ```sql
  CREATE TABLE IF NOT EXISTS announcements (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      author_name TEXT NOT NULL,
      content TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY (user_id) REFERENCES users(id)
  )
  ```
- Implement `create_announcement(user_id, author_name, content)` and `get_recent_announcements(limit=50)`.
- No TTL logic needed at this time.

### Python API Server (`api_server.py`)
- Modifying `api_chat`: Before running RAG, parse `query`. If `startswith("@Announcement")`, bypass retrieval context and instead format using LLM.
- **Role Verification**: Fetch user's role. Students are blocked from the endpoint.
- **Formatting Prompt Example**: "You are an institutional announcer. Please re-write the following details into a well-structured, professional, engaging announcement with emojis..."
- Create the HTTP `GET /api/announcements` endpoint.

### Spring Boot Gateway Layers
- Create `AnnouncementController.java` mapped to `/api/announcements` for proxying.
- Extend `PythonApiService.java` with a `getAnnouncements()` standard web client proxy call to bridge traffic to the Python service.

### React UI Additions
- Extend `/src/services/api.js` to hit `/api/announcements`.
- Layout update in `ChatPage.jsx` to render a sidebar for announcements.
- Add an unread notification count badge in the UI header.
- Conditionally render autocomplete tools so that only 'faculty' and 'admin' roles see the `@Announcement` command hint.

---
*Drafted: April 2026*
