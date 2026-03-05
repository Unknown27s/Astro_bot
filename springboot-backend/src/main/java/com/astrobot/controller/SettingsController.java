package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.Map;

@RestController
@RequestMapping("/api/settings")
public class SettingsController {

    private final PythonApiService pythonApi;

    public SettingsController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    @GetMapping
    public ResponseEntity<?> get() {
        try {
            return ResponseEntity.ok(pythonApi.getSettings());
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @PutMapping
    public ResponseEntity<?> update(@RequestBody Map<String, Object> settings) {
        try {
            return ResponseEntity.ok(pythonApi.updateSettings(settings));
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @PostMapping("/test-provider/{provider}")
    public ResponseEntity<?> testProvider(@PathVariable String provider) {
        try {
            return ResponseEntity.ok(pythonApi.testProvider(provider));
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }
}
