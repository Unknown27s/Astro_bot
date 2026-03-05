package com.astrobot.controller;

import com.astrobot.dto.CreateUserRequest;
import com.astrobot.dto.ToggleUserRequest;
import com.astrobot.service.PythonApiService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final PythonApiService pythonApi;

    public UserController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    @GetMapping
    public ResponseEntity<?> list() {
        try {
            List<Map<String, Object>> users = pythonApi.listUsers();
            return ResponseEntity.ok(users);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @PostMapping
    public ResponseEntity<?> create(@Valid @RequestBody CreateUserRequest req) {
        try {
            Map<String, Object> result = pythonApi.createUser(
                    req.getUsername(), req.getPassword(), req.getRole(), req.getFullName());
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException.Conflict e) {
            return ResponseEntity.status(409).body(Map.of("error", "Username already exists"));
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @PatchMapping("/{userId}/toggle")
    public ResponseEntity<?> toggle(@PathVariable String userId, @RequestBody ToggleUserRequest req) {
        try {
            return ResponseEntity.ok(pythonApi.toggleUser(userId, req.isActive()));
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @DeleteMapping("/{userId}")
    public ResponseEntity<?> delete(@PathVariable String userId) {
        try {
            return ResponseEntity.ok(pythonApi.deleteUser(userId));
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }
}
