# Voice-to-Text Implementation Plan (Local Whisper)

This document outlines the approach for integrating a local OpenAI Whisper model into the IMS AstroBot project. We will use the `faster-whisper` library inside the FastAPI backend.

## Architecture

We will proxy the audio file from React -> Spring Boot -> FastAPI.
- **Frontend**: Web Audio API (`MediaRecorder`) to capture mic input in `.webm` format.
- **Gateway**: Spring Boot passes the `multipart/form-data` audio blob to FastAPI.
- **Backend**: FastAPI uses `faster-whisper` (base model, ~140MB) on CPU to transcribe the audio. The transcribed text is then piped directly into the existing RAG generation flow.

## Implementation Steps

### 1. React Frontend Subsystem
- **Modify `react-frontend/src/pages/ChatPage.jsx`**: Add a new "Microphone" button next to the chat input box. Manage audio recording states (idle, recording, transcribing). 
- **Modify `react-frontend/src/services/api.js`**: Add `sendAudioMessage` function using Axios `FormData`.

### 2. Spring Boot Gateway
- **Modify `springboot-backend/src/main/java/com/astrobot/controller/ChatController.java`**: Add a `@PostMapping("/audio")` endpoint that consumes `multipart/form-data`.
- **Modify `springboot-backend/src/main/java/com/astrobot/service/PythonApiService.java`**: Map the audio file over Spring WebClient's `MultipartBodyBuilder` to forward to Python.

### 3. Python FastAPI Backend
- **Requirements**: Add `faster-whisper` and `python-multipart` to `requirements.txt`.
- **New Module**: Create `rag/voice_to_text.py` with an LRU cached loader for the Whisper `base.en` model.
- **Modify `api_server.py`**: Add `/api/chat/audio` route, handle temp file save, send to transcription, and pass the text to `generate_response()`.

## System Requirements
- `ffmpeg` must be installed on the host machine to decode audio blobs.
- Base Python dependencies (`faster-whisper`).
