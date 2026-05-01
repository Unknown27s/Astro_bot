package com.astrobot.controller;

import com.astrobot.dto.ChatRequest;
import com.astrobot.service.PythonApiService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private final PythonApiService pythonApi;
    // Use a dedicated thread pool for SSE to avoid blocking main threads
    private final ExecutorService sseExecutor = Executors.newCachedThreadPool();

    public ChatController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    @PostMapping
    public ResponseEntity<?> chat(@Valid @RequestBody ChatRequest req) {
        try {
            Map<String, Object> result = pythonApi.chat(
                    req.getQuery(), req.getUserId(), req.getUsername());
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", "Chat request failed: " + e.getMessage()));
        }
    }

    /**
     * Optimized SSE streaming endpoint.
     * Directly relays tokens from Python to the Frontend.
     */
    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chatStream(@Valid @RequestBody ChatRequest req) {
        // Set a long timeout (5 minutes) for LLM generation
        SseEmitter emitter = new SseEmitter(300_000L);

        sseExecutor.execute(() -> {
            try {
                pythonApi.chatStream(req.getQuery(), req.getUserId(), req.getUsername())
                        .subscribe(
                            data -> {
                                try {
                                    // Send the raw JSON string as the data payload
                                    // SseEmitter.send(Object) wraps it in "data:<content>\n\n"
                                    emitter.send(data);
                                } catch (Exception e) {
                                    emitter.completeWithError(e);
                                }
                            },
                            error -> {
                                System.err.println("SSE Stream Error: " + error.getMessage());
                                emitter.completeWithError(error);
                            },
                            () -> {
                                emitter.complete();
                            }
                        );
            } catch (Exception e) {
                emitter.completeWithError(e);
            }
        });

        return emitter;
    }

    @PostMapping(value = "/audio", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> chatAudio(
            @RequestParam("audio") MultipartFile audio,
            @RequestParam("user_id") String userId,
            @RequestParam("username") String username) {
        try {
            Map<String, Object> result = pythonApi.chatAudio(audio, userId, username);
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", "Audio chat request failed: " + e.getMessage()));
        }
    }

    @GetMapping("/status")
    public ResponseEntity<?> status() {
        try {
            return ResponseEntity.ok(pythonApi.getChatStatus());
        } catch (Exception e) {
            return ResponseEntity.ok(Map.of("available", false,
                    "status", Map.of("status", "error", "message", "Python API unreachable")));
        }
    }
}
