package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/faq")
public class FaqController {

    private final PythonApiService pythonApi;

    public FaqController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    @PostMapping
    public ResponseEntity<?> addFaq(@RequestBody Map<String, Object> payload) {
        try {
            Map<String, Object> result = pythonApi.addFaq(payload);
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @PostMapping("/bulk")
    public ResponseEntity<?> addFaqBulk(@RequestBody Map<String, Object> payload) {
        try {
            Object entriesObject = payload.get("entries");
            if (!(entriesObject instanceof List<?> entriesRaw)) {
                return ResponseEntity.badRequest().body(Map.of("error", "entries must be a list"));
            }

            @SuppressWarnings("unchecked")
            List<Map<String, Object>> entries = (List<Map<String, Object>>) (List<?>) entriesRaw;
            Map<String, Object> result = pythonApi.addFaqBulk(entries);
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @GetMapping("/stats")
    public ResponseEntity<?> stats() {
        try {
            Map<String, Object> result = pythonApi.getFaqStats();
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @PostMapping("/clear")
    public ResponseEntity<?> clear() {
        try {
            Map<String, Object> result = pythonApi.clearFaq();
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }
}
