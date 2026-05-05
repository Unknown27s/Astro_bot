package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.Map;

/**
 * AdminUploadController - Accepts legacy/admin upload paths used by React UI.
 * Proxies to Python FastAPI /api/admin/upload/* endpoints.
 */
@RestController
@RequestMapping("/api/admin/upload")
public class AdminUploadController {

    private final PythonApiService pythonApi;

    public AdminUploadController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    /**
     * Upload student data from CSV/XLSX (admin only).
     */
    @PostMapping("/students")
    public ResponseEntity<?> uploadStudents(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "uploaded_by", required = false) String uploadedBy) {
        try {
            if (!isValidFileType(file)) {
                return ResponseEntity.badRequest()
                        .body(Map.of("status", "error", "message", "Only CSV and XLSX files are allowed"));
            }

            Map<String, Object> result = pythonApi.uploadStudents(file, uploadedBy);
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("status", "error", "error", e.getResponseBodyAsString()));
        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                    .body(Map.of("status", "error", "error", e.getMessage()));
        }
    }

    /**
     * Upload student marks from CSV/XLSX (admin/faculty).
     */
    @PostMapping("/marks")
    public ResponseEntity<?> uploadMarks(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "uploaded_by", required = false) String uploadedBy) {
        try {
            if (!isValidFileType(file)) {
                return ResponseEntity.badRequest()
                        .body(Map.of("status", "error", "message", "Only CSV and XLSX files are allowed"));
            }

            Map<String, Object> result = pythonApi.uploadMarks(file, uploadedBy);
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("status", "error", "error", e.getResponseBodyAsString()));
        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                    .body(Map.of("status", "error", "error", e.getMessage()));
        }
    }

    /**
     * Upload unified student + marks data (admin/faculty).
     */
    @PostMapping("/unified")
    public ResponseEntity<?> uploadUnified(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "uploaded_by", required = false) String uploadedBy) {
        try {
            if (!isValidFileType(file)) {
                return ResponseEntity.badRequest()
                        .body(Map.of("status", "error", "message", "Only CSV and XLSX files are allowed"));
            }

            Map<String, Object> result = pythonApi.uploadUnified(file, uploadedBy);
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("status", "error", "error", e.getResponseBodyAsString()));
        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                    .body(Map.of("status", "error", "error", e.getMessage()));
        }
    }

    private boolean isValidFileType(MultipartFile file) {
        String filename = file.getOriginalFilename();
        if (filename == null) {
            return false;
        }
        return filename.endsWith(".csv") || filename.endsWith(".xlsx");
    }
}
