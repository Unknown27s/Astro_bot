package com.astrobot.dto;

import lombok.Data;

@Data
public class ProviderSettingsRequest {
    private String llmMode;
    private String primaryProvider;
    private String fallbackProvider;
    private String ollamaBaseUrl;
    private String ollamaModel;
    private String grokApiKey;
    private String grokModel;
    private String geminiApiKey;
    private String geminiModel;
    private Double temperature;
    private Integer maxTokens;
}
