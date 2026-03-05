package com.astrobot.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ChatRequest {
    @NotBlank
    private String query;
    @NotBlank
    private String userId;
    @NotBlank
    private String username;
}
