package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class SuggestionsController {

    private final PythonApiService pythonApi;

    public SuggestionsController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    @GetMapping("/suggestions")
    public ResponseEntity<?> getSuggestions(
            @RequestParam(value = "q", required = false, defaultValue = "") String query,
            @RequestParam(value = "user_id", required = false) String userId,
            @RequestParam(value = "user_role", required = false, defaultValue = "") String userRole) {
        try {
            Map<String, Object> result = pythonApi.getSuggestions(query, userId, userRole);
            return ResponseEntity.ok(withCommandSuggestions(result, query, userRole));
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        } catch (Exception e) {
            return ResponseEntity.ok(buildFallbackSuggestions(query, userRole));
        }
    }

    private Map<String, Object> withCommandSuggestions(Map<String, Object> result, String query, String userRole) {
        Map<String, Object> response = new LinkedHashMap<>();
        if (result != null) {
            response.putAll(result);
        }
        response.put("command_suggestions", buildCommandSuggestions(query, userRole));
        return response;
    }

    private Map<String, Object> buildFallbackSuggestions(String query, String userRole) {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("suggestions", java.util.Collections.emptyList());
        response.put("command_suggestions", buildCommandSuggestions(query, userRole));
        response.put("error", "Suggestions unavailable");
        return response;
    }

    private List<String> buildCommandSuggestions(String query, String userRole) {
        String normalizedQuery = query == null ? "" : query.trim().toLowerCase();
        String normalizedRole = userRole == null ? "" : userRole.trim().toLowerCase();
        boolean canUseCommands = "admin".equals(normalizedRole) || "faculty".equals(normalizedRole);
        List<String> commands = new ArrayList<>();

        if (!canUseCommands || normalizedQuery.isEmpty()) {
            return commands;
        }

        boolean showAnnouncement = normalizedQuery.startsWith("@")
                || "@announcement".startsWith(normalizedQuery)
                || normalizedQuery.contains("announce");
        boolean showDatabase = normalizedQuery.startsWith("@")
                || "@database".startsWith(normalizedQuery)
                || normalizedQuery.contains("database");

        if (showAnnouncement) {
            commands.add("@Announcement ");
        }
        if (showDatabase) {
            commands.add("@Database ");
        }
        return commands;
    }
}
