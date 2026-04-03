package com.astrobot.controller;

import com.astrobot.dto.ChatRequest;
import com.astrobot.service.PythonApiService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.Map;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private final PythonApiService pythonApi;

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
