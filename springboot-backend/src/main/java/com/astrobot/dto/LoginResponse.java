package com.astrobot.dto;

import lombok.Data;

@Data
public class LoginResponse {
    private String id;
    private String username;
    private String role;
    private String fullName;
}
