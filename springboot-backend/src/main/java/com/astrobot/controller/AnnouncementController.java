package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/announcements")
public class AnnouncementController {

    private final PythonApiService pythonApi;

    public AnnouncementController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    @GetMapping
    public ResponseEntity<?> getAnnouncements(
            @RequestParam(value = "limit", defaultValue = "50") int limit) {
        try {
            List<Map<String, Object>> result = pythonApi.getAnnouncements(limit);
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", "Failed to get announcements: " + e.getMessage()));
        }
    }
}
