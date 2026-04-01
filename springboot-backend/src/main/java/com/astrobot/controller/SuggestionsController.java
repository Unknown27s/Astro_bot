package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClientResponseException;

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
            @RequestParam(value = "user_id", required = false) String userId) {
        try {
            Map<String, Object> result = pythonApi.getSuggestions(query, userId);
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        } catch (Exception e) {
            return ResponseEntity.ok(Map.of(
                    "suggestions", java.util.Collections.emptyList(),
                    "error", "Suggestions unavailable"
            ));
        }
    }
}
