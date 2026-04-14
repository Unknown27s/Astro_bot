package com.astrobot.service;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.List;
import java.util.Map;

/**
 * Service that proxies all calls to the Python FastAPI RAG server.
 * Spring Boot acts as an API gateway; Python handles RAG, LLM, embeddings, and
 * DB.
 */
@Service
public class PythonApiService {

    private final WebClient client;

    public PythonApiService(@Qualifier("pythonApiClient") WebClient client) {
        this.client = client;
    }

    // ── Auth ──

    public Map<String, Object> login(String username, String password) {
        return client.post()
                .uri("/api/auth/login")
                .bodyValue(Map.of("username", username, "password", password))
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> register(String username, String password, String role, String fullName) {
        return client.post()
                .uri("/api/auth/register")
                .bodyValue(Map.of("username", username, "password", password, "role", role, "full_name", fullName))
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    // ── Chat ──

    public Map<String, Object> chat(String query, String userId, String username) {
        return client.post()
                .uri("/api/chat")
                .bodyValue(Map.of("query", query, "user_id", userId, "username", username))
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> chatAudio(MultipartFile audio, String userId, String username) {
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        builder.part("audio", audio.getResource());
        builder.part("user_id", userId);
        builder.part("username", username);

        return client.post()
                .uri("/api/chat/audio")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> getChatStatus() {
        return client.get()
                .uri("/api/chat/status")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    // ── Announcements ──

    public List<Map<String, Object>> getAnnouncements(int limit) {
        return client.get()
                .uri(uriBuilder -> uriBuilder.path("/api/announcements").queryParam("limit", limit).build())
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<List<Map<String, Object>>>() {
                })
                .block();
    }

    public Map<String, Object> deleteAnnouncement(String announcementId, String userId, String userRole) {
        return client.delete()
                .uri("/api/announcements/{id}", announcementId)
                .header("X-User-ID", userId)
                .header("X-User-Role", userRole)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    // ── Suggestions ──

    public Map<String, Object> getSuggestions(String query, String userId) {
        return client.get()
                .uri(uriBuilder -> {
                    uriBuilder.path("/api/suggestions");
                    if (query != null && !query.isEmpty()) {
                        uriBuilder.queryParam("q", query);
                    }
                    if (userId != null && !userId.isEmpty()) {
                        uriBuilder.queryParam("user_id", userId);
                    }
                    return uriBuilder.build();
                })
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    // ── Documents ──

    public Map<String, Object> uploadDocument(MultipartFile file, String uploadedBy) {
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        builder.part("file", file.getResource());
        if (uploadedBy != null && !uploadedBy.isEmpty()) {
            builder.part("uploaded_by", uploadedBy);
        }

        return client.post()
                .uri("/api/documents/upload")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> ingestOfficialSite(Map<String, Object> request) {
        return client.post()
                .uri("/api/documents/ingest-url")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public List<Map<String, Object>> listDocuments() {
        return client.get()
                .uri("/api/documents")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<List<Map<String, Object>>>() {
                })
                .block();
    }

    public Map<String, Object> deleteDocument(String docId) {
        return client.delete()
                .uri("/api/documents/{docId}", docId)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    // ── Users ──

    public List<Map<String, Object>> listUsers() {
        return client.get()
                .uri("/api/users")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<List<Map<String, Object>>>() {
                })
                .block();
    }

    public Map<String, Object> createUser(String username, String password, String role, String fullName) {
        return client.post()
                .uri("/api/users")
                .bodyValue(Map.of("username", username, "password", password, "role", role, "full_name", fullName))
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> toggleUser(String userId, boolean isActive) {
        return client.patch()
                .uri("/api/users/{userId}/toggle", userId)
                .bodyValue(Map.of("is_active", isActive))
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> deleteUser(String userId) {
        return client.delete()
                .uri("/api/users/{userId}", userId)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    // ── Analytics ──

    public Map<String, Object> getAnalytics() {
        return client.get()
                .uri("/api/analytics")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public List<Map<String, Object>> getQueryLogs(int limit) {
        return client.get()
                .uri(uriBuilder -> uriBuilder.path("/api/analytics/logs").queryParam("limit", limit).build())
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<List<Map<String, Object>>>() {
                })
                .block();
    }

    // ── Health ──

    public Map<String, Object> getHealth() {
        return client.get()
                .uri("/api/health")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> getProviderStatuses() {
        return client.get()
                .uri("/api/health/providers")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    // ── Settings ──

    public Map<String, Object> getSettings() {
        return client.get()
                .uri("/api/settings")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> updateSettings(Map<String, Object> settings) {
        return client.put()
                .uri("/api/settings")
                .bodyValue(settings)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> testProvider(String provider) {
        return client.post()
                .uri("/api/settings/test-provider/{provider}", provider)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> getKnowledgeBaseStats() {
        return client.get()
                .uri("/api/documents/stats")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    // ── Rate Limiting (Admin) ──

    public Map<String, Object> getRateLimits() {
        return client.get()
                .uri("/api/admin/rate-limits")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> updateRateLimit(String endpoint, Map<String, Object> body) {
        return client.put()
                .uri("/api/admin/rate-limits/{endpoint}", endpoint)
                .bodyValue(body)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> toggleRateLimit(String endpoint, Map<String, Object> body) {
        return client.patch()
                .uri("/api/admin/rate-limits/{endpoint}/toggle", endpoint)
                .bodyValue(body)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> resetRateLimits() {
        return client.post()
                .uri("/api/admin/rate-limits/reset")
                .bodyValue(Map.of())
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    // ── Memory ──

    public Map<String, Object> getMemoryStats() {
        return client.get()
                .uri("/api/memory/stats")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> deleteMemoryEntry(String memoryId) {
        return client.delete()
                .uri("/api/memory/{memoryId}", memoryId)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> runMemoryCleanup() {
        return client.post()
                .uri("/api/memory/cleanup")
                .bodyValue(Map.of())
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }

    public Map<String, Object> clearAllMemory() {
        return client.post()
                .uri("/api/memory/clear")
                .bodyValue(Map.of())
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();
    }
}
