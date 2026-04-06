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

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteAnnouncement(
            @PathVariable String id,
            @RequestHeader(value = "X-User-ID", defaultValue = "") String userId,
            @RequestHeader(value = "X-User-Role", defaultValue = "") String userRole) {
        try {
            Map<String, Object> result = pythonApi.deleteAnnouncement(id, userId, userRole);
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", "Failed to delete announcement: " + e.getMessage()));
        }
    }
}
