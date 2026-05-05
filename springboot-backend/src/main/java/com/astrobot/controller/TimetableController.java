package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.List;
import java.util.Map;

/**
 * TimetableController - Handles timetable data upload
 * Acts as proxy to Python FastAPI /api/admin/upload/timetable
 */
@RestController
@RequestMapping("/api/admin")
public class TimetableController {

    private final PythonApiService pythonApi;

    public TimetableController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    /**
     * Upload timetable data from CSV/Excel file
     */
    @PostMapping("/upload/timetable")
    public ResponseEntity<?> uploadTimetable(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "uploaded_by", required = false) String uploadedBy) {
        try {
            if (!isValidFileType(file)) {
                return ResponseEntity.badRequest()
                        .body(Map.of("status", "error", "message", "Only CSV and XLSX files are allowed"));
            }

            Map<String, Object> result = pythonApi.uploadTimetable(file, uploadedBy);
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
     * List timetable entries (admin/faculty only).
     */
    @GetMapping("/timetables")
    public ResponseEntity<?> listTimetables(
            @RequestHeader(value = "X-User-ID", required = false) String userId) {
        try {
            List<Map<String, Object>> result = pythonApi.getTimetables(userId);
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
