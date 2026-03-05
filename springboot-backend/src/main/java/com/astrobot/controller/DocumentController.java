package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/documents")
public class DocumentController {

    private final PythonApiService pythonApi;

    public DocumentController(PythonApiService pythonApi) {
        this.pythonApi = pythonApi;
    }

    @PostMapping("/upload")
    public ResponseEntity<?> upload(
            @RequestParam("file") MultipartFile file,
            @RequestParam("uploaded_by") String uploadedBy) {
        try {
            Map<String, Object> result = pythonApi.uploadDocument(file, uploadedBy);
            return ResponseEntity.ok(result);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @GetMapping
    public ResponseEntity<?> list() {
        try {
            List<Map<String, Object>> docs = pythonApi.listDocuments();
            return ResponseEntity.ok(docs);
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @DeleteMapping("/{docId}")
    public ResponseEntity<?> delete(@PathVariable String docId) {
        try {
            return ResponseEntity.ok(pythonApi.deleteDocument(docId));
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getStatusCode())
                    .body(Map.of("error", e.getResponseBodyAsString()));
        }
    }

    @GetMapping("/stats")
    public ResponseEntity<?> stats() {
        try {
            return ResponseEntity.ok(pythonApi.getKnowledgeBaseStats());
        } catch (Exception e) {
            return ResponseEntity.ok(Map.of("total_chunks", 0));
        }
    }
}
