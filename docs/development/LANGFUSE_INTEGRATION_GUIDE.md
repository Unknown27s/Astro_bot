# Langfuse Integration Guide

This guide explains how Langfuse is integrated into AstroBot, what telemetry is captured, and how to roll out user-visible improvements.

## 1. What was added (Phase 1)

Backend-only observability was added with safe fallback behavior.

Updated files:

- `config.py`
- `requirements.txt`
- `api_server.py`
- `rag/retriever.py`
- `rag/generator.py`
- `rag/observability/__init__.py`
- `rag/observability/langfuse_client.py`

Behavior is non-breaking:

- If Langfuse is disabled or keys are missing, the app continues normally.
- No request/response schema changes are required for existing clients.

## 2. Environment variables

Add to `.env`:

```env
LANGFUSE_ENABLED=false
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

Set `LANGFUSE_ENABLED=true` after keys are configured.

## 3. Captured trace spans

Current spans include:

- API traces:
  - `api.chat`
  - `api.chat.audio`
- Retrieval:
  - `retrieval`
  - `embedding.query`
  - `vector_search.chromadb`
- Generation:
  - `generation.pipeline`
  - `memory.lookup`
  - `llm.generate`

Typical metadata:

- endpoint and request mode (voice/text)
- elapsed times (per span + total)
- chunk counts and top similarity
- cache hit or miss
- provider/model (when available)
- response length

## 4. Privacy controls

- User identifiers are hashed before being attached to trace metadata.
- Query preview is truncated for observability.
- You can further redact or disable input capture in `rag/observability/langfuse_client.py`.

## 5. Operational impact

Expected improvements:

1. Faster debugging of poor responses (prompt vs retrieval vs model failure)
2. Better latency tuning by step-level timing
3. Better cost tracking via model/provider analysis
4. Better quality tuning via cache/retrieval telemetry

## 6. Phase 2 (user-visible)

Phase 2 adds feedback and transparency to the UI.

Status: Implemented.

Suggested UI changes:

1. Include optional `trace_id` in chat responses
2. Send thumbs up/down from bot message actions with `trace_id`
3. Add admin page widgets:
   - top failing prompts
   - average retrieval score
   - cache hit rate
   - provider error trend

Minimal API additions for Phase 2:

- `POST /api/feedback`
  - payload: `trace_id`, `rating`, `comment`, `user_id`
- Optional `trace_id` in `/api/chat` and `/api/chat/audio` responses

Implemented endpoints and fields:

- `/api/chat` now returns `trace_id`
- `/api/chat/audio` now returns `trace_id`
- `POST /api/feedback` persists feedback in SQLite and stores score in Langfuse when enabled
- `/api/analytics` now includes feedback metrics and daily helpful vs not-helpful trend

Frontend hookup implemented:

- Bot message thumbs up/down now submits feedback with trace id
- Feedback is tied to Langfuse score name: `user_feedback`
- Admin Analytics page shows feedback KPIs and a 14-day helpful/not-helpful trend chart
- Admin Trace Monitor page now shows:
  - trace timeline (`GET /api/monitor/traces`)
  - subsystem alerts and failure trends (`GET /api/monitor/overview`)
  - provider fallback visibility per trace event

## 7. Validation checklist

1. Start app with `LANGFUSE_ENABLED=false` and verify normal behavior.
2. Enable Langfuse, set keys, and send 3 test questions.
3. Confirm traces and spans appear in Langfuse dashboard.
4. Confirm retrieval and generation timings are visible.
5. Confirm voice endpoint traces are visible.

## 8. Troubleshooting

If traces do not appear:

1. Verify `LANGFUSE_ENABLED=true`
2. Verify keys and host
3. Confirm `langfuse` package installed
4. Check backend logs for Langfuse initialization warnings

