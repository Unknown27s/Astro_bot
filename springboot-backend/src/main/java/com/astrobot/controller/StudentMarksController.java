package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.Map;

/**
 * StudentMarksController - Handles student and marks data upload/management
 * Acts as proxy to Python FastAPI /api/admin/upload/* endpoints
 */
@RestController
@RequestMapping("/api/admin/students")
public class StudentMarksController {

    private final PythonApiService pythonApi;

    public StudentMarksController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    /**
     * Upload student data from CSV/Excel file
     * Expected columns: roll_no, name, email, phone, department, semester, gpa
     */
    @PostMapping("/upload")
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
     * Upload student marks from CSV/Excel file
     * Expected columns: roll_no, subject_code, subject_name, semester,
     * internal_marks, external_marks, grade
     */
    @PostMapping("/marks/upload")
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
     * Validate file extension
     */
    private boolean isValidFileType(MultipartFile file) {
        String filename = file.getOriginalFilename();
        if (filename == null)
            return false;
        return filename.endsWith(".csv") || filename.endsWith(".xlsx");
    }
}
