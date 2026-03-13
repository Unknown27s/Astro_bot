package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.Map;

@RestController
@RequestMapping("/api/memory")
public class MemoryController {

    private final PythonApiService pythonApi;

    public MemoryController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    @GetMapping("/stats")
    public ResponseEntity<?> getMemoryStats() {
        try {
            Map<String, Object> stats = pythonApi.getMemoryStats();
            return ResponseEntity.ok(stats);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", "Failed to fetch memory stats: " + e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(503)
                    .body(Map.of("error", "Memory service unavailable"));
        }
    }

    @DeleteMapping("/{memoryId}")
    public ResponseEntity<?> deleteMemoryEntry(@PathVariable String memoryId) {
        try {
            Map<String, Object> result = pythonApi.deleteMemoryEntry(memoryId);
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", "Failed to delete memory entry: " + e.getMessage()));
        }
    }

    @PostMapping("/cleanup")
    public ResponseEntity<?> runMemoryCleanup() {
        try {
            Map<String, Object> result = pythonApi.runMemoryCleanup();
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", "Cleanup failed: " + e.getMessage()));
        }
    }

    @PostMapping("/clear")
    public ResponseEntity<?> clearAllMemory() {
        try {
            Map<String, Object> result = pythonApi.clearAllMemory();
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", "Failed to clear memory: " + e.getMessage()));
        }
    }
}
