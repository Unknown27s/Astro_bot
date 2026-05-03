package com.astrobot.dto;

public class MarksUploadResponse {
    private String status;
    private int marksAdded;
    private int totalRecords;
    private String message;
    private String error;

    public MarksUploadResponse() {
    }

    public MarksUploadResponse(String status, int marksAdded, int totalRecords) {
        this.status = status;
        this.marksAdded = marksAdded;
        this.totalRecords = totalRecords;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public int getMarksAdded() {
        return marksAdded;
    }

    public void setMarksAdded(int marksAdded) {
        this.marksAdded = marksAdded;
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
