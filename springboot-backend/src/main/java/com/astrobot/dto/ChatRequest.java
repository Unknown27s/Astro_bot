package com.astrobot.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ChatRequest {
    @NotBlank
    private String query;

    @JsonAlias({ "user_id" })
    @NotBlank
    private String userId;

    @NotBlank
    private String username;
}
