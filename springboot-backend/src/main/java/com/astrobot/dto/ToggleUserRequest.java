package com.astrobot.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class ToggleUserRequest {
    @JsonProperty("is_active")
    private boolean isActive;
}
