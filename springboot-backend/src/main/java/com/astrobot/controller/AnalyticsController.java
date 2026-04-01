package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class AnalyticsController {

    private final PythonApiService pythonApi;

    public AnalyticsController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    @GetMapping("/analytics")
    public ResponseEntity<?> analytics() {
        try {
            return ResponseEntity.ok(pythonApi.getAnalytics());
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @GetMapping("/analytics/logs")
    public ResponseEntity<?> queryLogs(@RequestParam(defaultValue = "50") int limit) {
        try {
            List<Map<String, Object>> logs = pythonApi.getQueryLogs(limit);
            return ResponseEntity.ok(logs);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @GetMapping("/health")
    public ResponseEntity<?> health() {
        try {
            Map<String, Object> health = pythonApi.getHealth();
            // Add Spring Boot itself as healthy
            health.put("spring_boot", Map.of("status", "ok", "message", "Running"));
            return ResponseEntity.ok(health);
        } catch (Exception e) {
            // Return 503 Service Unavailable when Python API is down
            return ResponseEntity.status(503).body(Map.of(
                    "spring_boot", Map.of("status", "ok", "message", "Running"),
                    "python_api", Map.of("status", "error", "message", "Python API unreachable: " + e.getMessage())
            ));
        }
    }

    @GetMapping("/health/providers")
    public ResponseEntity<?> providerStatuses() {
        try {
            return ResponseEntity.ok(pythonApi.getProviderStatuses());
        } catch (Exception e) {
            return ResponseEntity.status(503)
                    .body(Map.of("error", "Python API unreachable"));
        }
    }
}
