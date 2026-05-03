package com.astrobot.dto;

public class StudentUploadResponse {
    private String status;
    private int studentsAdded;
    private int totalRecords;
    private String message;
    private String error;

    public StudentUploadResponse() {
    }

    public StudentUploadResponse(String status, int studentsAdded, int totalRecords) {
        this.status = status;
        this.studentsAdded = studentsAdded;
        this.totalRecords = totalRecords;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public int getStudentsAdded() {
        return studentsAdded;
    }

    public void setStudentsAdded(int studentsAdded) {
        this.studentsAdded = studentsAdded;
    }

    public int getTotalRecords() {
        return totalRecords;
    }

    public void setTotalRecords(int totalRecords) {
        this.totalRecords = totalRecords;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public String getError() {
        return error;
    }

    public void setError(String error) {
        this.error = error;
    }
}
