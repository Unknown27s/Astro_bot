package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * REST API Controller for Rate Limiting Management (Admin)
 * Proxies all rate limit requests to the Python FastAPI backend
 */
@RestController
@RequestMapping("/api/admin/rate-limits")
public class RateLimitController {

    @Autowired
    private PythonApiService pythonApiService;

    /**
     * Get all rate limit configurations
     */
    @GetMapping
    public ResponseEntity<Map<String, Object>> getRateLimits() {
        try {
            Map<String, Object> response = pythonApiService.getRateLimits();
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of(
                    "detail", "Failed to fetch rate limits: " + e.getMessage()
            ));
        }
    }

    /**
     * Update rate limit configuration for an endpoint
     * @param endpoint The endpoint name (e.g., "auth", "chat", "upload")
     */
    @PutMapping("/{endpoint}")
    public ResponseEntity<Map<String, Object>> updateRateLimit(
            @PathVariable String endpoint,
            @RequestBody Map<String, Object> body) {
        try {
            Map<String, Object> response = pythonApiService.updateRateLimit(endpoint, body);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of(
                    "detail", "Failed to update rate limit: " + e.getMessage()
            ));
        }
    }

    /**
     * Toggle rate limit enabled/disabled for an endpoint
     * @param endpoint The endpoint name (e.g., "auth", "chat", "upload")
     */
    @PatchMapping("/{endpoint}/toggle")
    public ResponseEntity<Map<String, Object>> toggleRateLimit(
            @PathVariable String endpoint,
            @RequestBody Map<String, Object> body) {
        try {
            Map<String, Object> response = pythonApiService.toggleRateLimit(endpoint, body);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of(
                    "detail", "Failed to toggle rate limit: " + e.getMessage()
            ));
        }
    }

    /**
     * Reset all rate limits to default values (Dangerous!)
     */
    @PostMapping("/reset")
    public ResponseEntity<Map<String, Object>> resetRateLimits() {
        try {
            Map<String, Object> response = pythonApiService.resetRateLimits();
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of(
                    "detail", "Failed to reset rate limits: " + e.getMessage()
            ));
        }
    }
}
