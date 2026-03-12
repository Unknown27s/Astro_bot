"""
IMS AstroBot — Admin Views
Document management + AI Settings page.
"""

import os
import time
import streamlit as st
from pathlib import Path

from config import (
    UPLOAD_DIR, SUPPORTED_EXTENSIONS,
    MODEL_MAX_TOKENS, MODEL_TEMPERATURE,
    EMBEDDING_MODEL, SYSTEM_PROMPT, BASE_DIR,
    LLM_MODE, LLM_PRIMARY_PROVIDER, LLM_FALLBACK_PROVIDER,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    GROQ_API_KEY, GROQ_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL,
)
from database.db import get_all_documents, delete_document, add_document
from ingestion.parser import parse_document
from ingestion.chunker import chunk_document
from ingestion.embedder import store_chunks, delete_doc_chunks, get_collection_stats


def render_admin_page():
    """Render document management (called from app.py admin sidebar → Documents)."""

    st.markdown("### 📄 Document Management")
    st.divider()
    _render_document_management()


def _render_document_management():
    """Document upload and management section."""

    st.subheader("Upload Documents")
    st.caption(f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")

    uploaded_files = st.file_uploader(
        "Choose files to upload",
        accept_multiple_files=True,
        type=[ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS],
        key="doc_uploader",
    )

    if uploaded_files and st.button("📤 Process & Upload", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, uploaded_file in enumerate(uploaded_files):
            file_ext = Path(uploaded_file.name).suffix.lower()
            if file_ext not in SUPPORTED_EXTENSIONS:
                st.warning(f"Skipping unsupported file: {uploaded_file.name}")
                continue

            status_text.text(f"Processing {uploaded_file.name}...")

            # Save file to disk
            safe_name = f"{int(time.time())}_{uploaded_file.name}"
            file_path = UPLOAD_DIR / safe_name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Parse document
            text = parse_document(str(file_path))
            if not text:
                st.error(f"Failed to extract text from {uploaded_file.name}")
                continue

            # Chunk document
            chunks = chunk_document(text, source_name=uploaded_file.name)
            if not chunks:
                st.error(f"No chunks generated from {uploaded_file.name}")
                continue

            # Record in database
            doc_id = add_document(
                filename=safe_name,
                original_name=uploaded_file.name,
                file_type=file_ext,
                file_size=uploaded_file.size,
                chunk_count=len(chunks),
                uploaded_by=st.session_state.user_id,
            )

            # Store embeddings in ChromaDB
            stored = store_chunks(chunks, doc_id)

            st.success(f"✅ {uploaded_file.name} — {stored} chunks indexed")
            progress_bar.progress((idx + 1) / len(uploaded_files))

        status_text.text("All files processed!")
        time.sleep(1)
        st.rerun()

    # ── Existing Documents ──
    st.divider()
    st.subheader("Knowledge Base")

    # Collection stats
    stats = get_collection_stats()
    st.metric("Total Chunks in Vector DB", stats["total_chunks"])

    docs = get_all_documents()
    if not docs:
        st.info("No documents uploaded yet.")
    else:
        for doc in docs:
            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                st.markdown(f"📄 **{doc['original_name']}**")
                st.caption(f"Type: {doc['file_type']} | Chunks: {doc['chunk_count']} | Size: {doc['file_size'] / 1024:.1f} KB")
            with col2:
                st.caption(f"Uploaded: {doc['uploaded_at'][:16]}")
            with col3:
                if st.button("🗑️", key=f"del_doc_{doc['id']}", help="Delete this document"):
                    # Delete from ChromaDB
                    delete_doc_chunks(doc["id"])
                    # Delete from database
                    deleted = delete_document(doc["id"])
                    # Delete physical file
                    if deleted:
                        file_path = UPLOAD_DIR / deleted["filename"]
                        if file_path.exists():
                            os.remove(file_path)
                    st.success(f"Deleted: {doc['original_name']}")
                    st.rerun()


# ═══════════════════════════════════════════════════════
# AI SETTINGS PAGE
# ═══════════════════════════════════════════════════════

def render_ai_settings_page():
    """AI Settings — LLM provider config, parameters, system prompt."""

    st.markdown("### 🤖 AI Settings")
    st.divider()

    # ══════════════════════════════════════════
    # Section 1: LLM Mode
    # ══════════════════════════════════════════
    st.subheader("🔀 LLM Mode")
    st.caption("Choose how AstroBot generates responses.")

    mode_options = ["local_only", "cloud_only", "hybrid"]
    mode_labels = {
        "local_only": "🖥️ Local Only (Ollama)",
        "cloud_only": "☁️ Cloud Only (Groq / Gemini)",
        "hybrid": "🔄 Hybrid (Primary + Fallback)",
    }
    current_mode_idx = mode_options.index(LLM_MODE) if LLM_MODE in mode_options else 0
    selected_mode = st.radio(
        "Mode",
        mode_options,
        index=current_mode_idx,
        format_func=lambda x: mode_labels[x],
        horizontal=True,
        key="llm_mode_radio",
    )
    if selected_mode != LLM_MODE:
        _update_env_var("LLM_MODE", selected_mode)
        _reset_providers()
        st.success(f"✅ Mode changed to **{mode_labels[selected_mode]}**. Restart to apply.")

    # ══════════════════════════════════════════
    # Section 2: Provider Configuration
    # ══════════════════════════════════════════
    if selected_mode in ("cloud_only", "hybrid"):
        st.divider()
        st.subheader("🔗 Provider Priority")
        st.caption("Set which provider to try first, and which to fall back to.")

        provider_options = ["ollama", "groq", "gemini"]
        provider_labels = {"ollama": "🖥️ Ollama (Local)", "groq": "⚡ Groq", "gemini": "💎 Gemini (Google)"}

        if selected_mode == "cloud_only":
            cloud_options = ["groq", "gemini"]
            cloud_labels = {k: provider_labels[k] for k in cloud_options}
            primary_idx = cloud_options.index(LLM_PRIMARY_PROVIDER) if LLM_PRIMARY_PROVIDER in cloud_options else 0
            new_primary = st.selectbox(
                "Primary Provider", cloud_options, index=primary_idx,
                format_func=lambda x: cloud_labels[x], key="primary_provider",
            )
            fallback_options = ["none"] + [p for p in cloud_options if p != new_primary]
            fallback_labels = {"none": "❌ None", **cloud_labels}
            fallback_idx = fallback_options.index(LLM_FALLBACK_PROVIDER) if LLM_FALLBACK_PROVIDER in fallback_options else 0
            new_fallback = st.selectbox(
                "Fallback Provider", fallback_options, index=fallback_idx,
                format_func=lambda x: fallback_labels[x], key="fallback_provider",
            )
        else:  # hybrid
            primary_idx = provider_options.index(LLM_PRIMARY_PROVIDER) if LLM_PRIMARY_PROVIDER in provider_options else 0
            new_primary = st.selectbox(
                "Primary Provider", provider_options, index=primary_idx,
                format_func=lambda x: provider_labels[x], key="primary_provider",
            )
            fallback_options = ["none"] + [p for p in provider_options if p != new_primary]
            fallback_labels = {"none": "❌ None (Ollama auto-fallback)", **provider_labels}
            fallback_idx = fallback_options.index(LLM_FALLBACK_PROVIDER) if LLM_FALLBACK_PROVIDER in fallback_options else 0
            new_fallback = st.selectbox(
                "Fallback Provider", fallback_options, index=fallback_idx,
                format_func=lambda x: fallback_labels[x], key="fallback_provider",
            )

        if new_primary != LLM_PRIMARY_PROVIDER or new_fallback != LLM_FALLBACK_PROVIDER:
            if st.button("💾 Save Provider Priority", type="primary"):
                _update_env_var("LLM_PRIMARY_PROVIDER", new_primary)
                _update_env_var("LLM_FALLBACK_PROVIDER", new_fallback)
                _reset_providers()
                st.success("✅ Provider priority saved. Restart to apply.")

    # ══════════════════════════════════════════
    # Section 3: Ollama Settings
    # ══════════════════════════════════════════
    st.divider()
    st.subheader("🖥️ Ollama (Local LLM)")
    st.caption("Configure the local Ollama server connection.")

    with st.form("ollama_form"):
        new_ollama_url = st.text_input("Ollama Server URL", value=OLLAMA_BASE_URL)
        new_ollama_model = st.text_input(
            "Model Name",
            value=OLLAMA_MODEL,
            help="e.g., qwen3:0.6b, llama3.2, mistral, gemma2",
        )
        save_ollama = st.form_submit_button("💾 Save Ollama Settings", use_container_width=True)
        if save_ollama:
            _update_env_var("OLLAMA_BASE_URL", new_ollama_url)
            _update_env_var("OLLAMA_MODEL", new_ollama_model)
            _reset_providers()
            st.success("✅ Ollama settings saved. Restart to apply.")

    if st.button("🔌 Test Ollama Connection", key="test_ollama"):
        with st.spinner("Testing Ollama..."):
            from rag.providers.ollama_provider import OllamaProvider
            prov = OllamaProvider(OLLAMA_BASE_URL, OLLAMA_MODEL)
            status = prov.get_status()
            if status["status"] == "ok":
                st.success(f"✅ {status['message']}")
                models = prov.list_models()
                if models:
                    st.info(f"Available models: {', '.join(models)}")
            elif status["status"] == "warning":
                st.warning(f"⚠️ {status['message']}")
            else:
                st.error(f"❌ {status['message']}")

    # ══════════════════════════════════════════
    # Section 4: Groq Settings
    # ══════════════════════════════════════════
    st.divider()
    st.subheader("⚡ Groq")
    st.caption("Configure Groq cloud API access.")

    with st.form("groq_form"):
        new_groq_key = st.text_input(
            "Groq API Key", value=GROQ_API_KEY, type="password",
            help="Get your API key from https://console.groq.com",
        )
        new_groq_model = st.text_input(
            "Groq Model", value=GROQ_MODEL,
            help="e.g., llama-3.3-70b-versatile, llama-3.1-8b-instant",
        )
        save_groq = st.form_submit_button("💾 Save Groq Settings", use_container_width=True)
        if save_groq:
            _update_env_var("GROQ_API_KEY", new_groq_key)
            _update_env_var("GROQ_MODEL", new_groq_model)
            _reset_providers()
            st.success("✅ Groq settings saved. Restart to apply.")

    if st.button("🔌 Test Groq Connection", key="test_groq"):
        with st.spinner("Testing Groq API..."):
            from rag.providers.groq_provider import GroqProvider
            prov = GroqProvider(GROQ_API_KEY, GROQ_MODEL)
            status = prov.get_status()
            if status["status"] == "ok":
                st.success(f"✅ {status['message']}")
            else:
                st.error(f"❌ {status['message']}")

    # ══════════════════════════════════════════
    # Section 5: Gemini Settings
    # ══════════════════════════════════════════
    st.divider()
    st.subheader("💎 Gemini (Google)")
    st.caption("Configure Google Gemini cloud API access.")

    with st.form("gemini_form"):
        new_gemini_key = st.text_input(
            "Gemini API Key", value=GEMINI_API_KEY, type="password",
            help="Get your API key from https://aistudio.google.com/apikey",
        )
        new_gemini_model = st.text_input(
            "Gemini Model", value=GEMINI_MODEL,
            help="e.g., gemini-2.0-flash, gemini-1.5-pro",
        )
        save_gemini = st.form_submit_button("💾 Save Gemini Settings", use_container_width=True)
        if save_gemini:
            _update_env_var("GEMINI_API_KEY", new_gemini_key)
            _update_env_var("GEMINI_MODEL", new_gemini_model)
            _reset_providers()
            st.success("✅ Gemini settings saved. Restart to apply.")

    if st.button("🔌 Test Gemini Connection", key="test_gemini"):
        with st.spinner("Testing Gemini API..."):
            from rag.providers.gemini_provider import GeminiProvider
            prov = GeminiProvider(GEMINI_API_KEY, GEMINI_MODEL)
            status = prov.get_status()
            if status["status"] == "ok":
                st.success(f"✅ {status['message']}")
            else:
                st.error(f"❌ {status['message']}")

    # ══════════════════════════════════════════
    # Section 6: Generation Parameters
    # ══════════════════════════════════════════
    st.divider()
    st.subheader("⚙️ Generation Parameters")
    st.caption("Adjust generation parameters. Changes are saved to `.env` and take effect on restart.")

    with st.form("llm_params_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_temp = st.slider(
                "Temperature", 0.0, 2.0,
                value=float(MODEL_TEMPERATURE), step=0.05,
                help="Higher = more creative, lower = more focused",
            )
        with col2:
            new_max_tokens = st.slider(
                "Max Tokens", 64, 4096,
                value=int(MODEL_MAX_TOKENS), step=64,
                help="Maximum number of tokens in the response",
            )

        save_params = st.form_submit_button("💾 Save Parameters", use_container_width=True, type="primary")
        if save_params:
            _update_env_var("MODEL_TEMPERATURE", str(new_temp))
            _update_env_var("MODEL_MAX_TOKENS", str(new_max_tokens))
            _reset_providers()
            st.success("✅ Parameters saved to `.env`. Restart to apply changes.")

    # ══════════════════════════════════════════
    # Section 7: System Prompt
    # ══════════════════════════════════════════
    st.divider()
    st.subheader("📝 System Prompt")
    st.caption("Customize the system prompt that guides the LLM's behavior.")

    new_prompt = st.text_area(
        "System Prompt",
        value=SYSTEM_PROMPT,
        height=200,
        key="system_prompt_editor",
    )
    if st.button("💾 Save System Prompt", use_container_width=True):
        _update_env_var("SYSTEM_PROMPT", new_prompt)
        st.success("✅ System prompt saved. Restart to apply.")

    # ══════════════════════════════════════════
    # Section 8: Embedding Model
    # ══════════════════════════════════════════
    st.divider()
    st.subheader("🔢 Embedding Model")
    st.caption("Select the sentence-transformers model used for document embeddings.")

    embedding_options = [
        "all-MiniLM-L6-v2",
        "all-MiniLM-L12-v2",
        "all-mpnet-base-v2",
        "paraphrase-MiniLM-L6-v2",
        "multi-qa-MiniLM-L6-cos-v1",
    ]
    current_embed = EMBEDDING_MODEL
    if current_embed not in embedding_options:
        embedding_options.insert(0, current_embed)

    selected_embed = st.selectbox(
        "Embedding Model",
        embedding_options,
        index=embedding_options.index(current_embed),
    )
    if selected_embed != current_embed:
        if st.button("💾 Save Embedding Model", type="primary"):
            _update_env_var("EMBEDDING_MODEL", selected_embed)
            st.success(f"✅ Embedding model changed to `{selected_embed}`. Restart to apply.")
            st.warning("⚠️ Changing the embedding model will require re-indexing all documents.")


# ── Helper: update .env file ──

def _update_env_var(key: str, value: str):
    """Update or add a key=value pair in the .env file."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        env_path.write_text(f"{key}={value}\n")
        return

    lines = env_path.read_text(encoding="utf-8").splitlines()
    found = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _reset_providers():
    """Reset the provider manager singleton so it re-reads config on next use."""
    try:
        from rag.providers.manager import reset_manager
        reset_manager()
    except Exception:
        pass
    # Also clear cached health data
    st.session_state.pop("system_health", None)
    st.session_state.pop("health_check_time", None)
