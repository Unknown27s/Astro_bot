package com.astrobot.controller;

import com.astrobot.dto.LoginRequest;
import com.astrobot.dto.RegisterRequest;
import com.astrobot.service.PythonApiService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final PythonApiService pythonApi;

    public AuthController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@Valid @RequestBody LoginRequest req) {
        try {
            Map<String, Object> result = pythonApi.login(req.getUsername(), req.getPassword());
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException.Unauthorized e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Invalid username or password"));
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@Valid @RequestBody RegisterRequest req) {
        try {
            Map<String, Object> result = pythonApi.register(
                    req.getUsername(), req.getPassword(), req.getRole(), req.getFullName());
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException.Conflict e) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of("error", "Username already exists"));
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }
}
