package com.astrobot.dto;

import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
public class ChatResponse {
    private String response;
    private List<Map<String, Object>> sources;
    private String citations;
    private double responseTimeMs;
}
