"""
AstroBot Lite - Single Service Deployment
Streamlit-only version with cloud LLM and embedded databases
"""

import streamlit as st
import os
import requests
import json
from pathlib import Path
import sqlite3
import hashlib
from datetime import datetime
import tempfile
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Configuration
st.set_page_config(
    page_title="AstroBot Lite",
    page_icon="🤖",
    layout="wide"
)

# Cloud LLM Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama3-8b-8192"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

@st.cache_resource
def init_services():
    """Initialize all services in one place"""
    # Initialize embeddings
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(
        path="./data/chroma_db",
        settings=Settings(allow_reset=True)
    )
    
    # Initialize SQLite
    conn = sqlite3.connect("./data/astrobot.db", check_same_thread=False)
    
    return embedder, chroma_client, conn

def query_groq(messages, context=""):
    """Query Groq API instead of local LLM"""
    if not GROQ_API_KEY:
        return "Error: GROQ_API_KEY not configured"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_msg = {
        "role": "system",
        "content": f"You are a helpful assistant. Use this context to answer: {context}"
    }
    
    data = {
        "model": GROQ_MODEL,
        "messages": [system_msg] + messages,
        "max_tokens": 512,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(GROQ_URL, headers=headers, json=data)
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    embedder, chroma_client, conn = init_services()
    
    st.title("🤖 AstroBot Lite")
    st.markdown("*Single-service RAG chatbot with cloud LLM*")
    
    # Simple file upload
    uploaded_file = st.file_uploader("Upload Document", type=['pdf', 'txt', 'docx'])
    if uploaded_file:
        st.success(f"Uploaded: {uploaded_file.name}")
        # Process document (simplified)
    
    # Chat interface
    user_input = st.text_input("Ask a question:")
    if user_input:
        with st.spinner("Thinking..."):
            # Simple RAG pipeline
            context = "Sample context from documents"
            response = query_groq([{"role": "user", "content": user_input}], context)
            st.write(response)

if __name__ == "__main__":
    main()
