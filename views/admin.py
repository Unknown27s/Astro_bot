"""
IMS AstroBot — Admin Views
Document management + AI Settings page.
"""

import os
import time
import shutil
import streamlit as st
from pathlib import Path
from datetime import datetime

from config import (
    UPLOAD_DIR, SUPPORTED_EXTENSIONS, MODEL_DIR, MODEL_PATH,
    MODEL_N_CTX, MODEL_N_THREADS, MODEL_MAX_TOKENS, MODEL_TEMPERATURE,
    EMBEDDING_MODEL, SYSTEM_PROMPT, BASE_DIR,
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
    """AI Settings — model upload/swap, parameters, system prompt."""

    st.markdown("### 🤖 AI Settings")
    st.divider()

    # ── Section 1: Current Model Info ──
    st.subheader("📁 Current Model")
    model_path = Path(MODEL_PATH)
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        st.success(f"**{model_path.name}**  —  {size_mb:.0f} MB", icon="✅")
    else:
        st.warning(f"No model found at `{model_path}`", icon="⚠️")

    # List all .gguf files in models/ directory
    gguf_files = sorted(MODEL_DIR.glob("*.gguf"))
    if gguf_files:
        with st.expander("📂 Available GGUF models in `models/` directory"):
            for f in gguf_files:
                sz = f.stat().st_size / (1024 * 1024)
                active = "✅" if f == model_path else "⬛"
                st.markdown(f"{active} **{f.name}** — {sz:.0f} MB")
    else:
        st.info("No `.gguf` files found in the `models/` directory.")

    # ── Section 2: Upload New GGUF Model ──
    st.divider()
    st.subheader("📤 Upload / Swap Model")
    st.caption("Upload a `.gguf` model file. It will be saved to the `models/` directory.")

    uploaded_model = st.file_uploader(
        "Choose a GGUF model file",
        type=["gguf"],
        key="model_uploader",
        help="Upload a quantized GGUF model (e.g., phi-3-mini-4k-instruct-q4.gguf)",
    )

    if uploaded_model:
        st.info(f"File: **{uploaded_model.name}** ({uploaded_model.size / (1024 * 1024):.0f} MB)")

        dest_path = MODEL_DIR / uploaded_model.name
        overwrite = dest_path.exists()
        if overwrite:
            st.warning(f"⚠️ This will overwrite the existing file: `{uploaded_model.name}`")

        if st.button(
            "💾 Save & Activate Model" if not overwrite else "💾 Overwrite & Activate Model",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Saving model file... This may take a while for large files."):
                try:
                    with open(dest_path, "wb") as f:
                        f.write(uploaded_model.getbuffer())

                    # Update .env to point to the new model
                    _update_env_var("MODEL_PATH", f"models\\{uploaded_model.name}")

                    st.success(f"✅ Model saved: `{dest_path.name}` ({dest_path.stat().st_size / (1024*1024):.0f} MB)")
                    st.warning(
                        "⚠️ **Restart required** — The model path in `.env` has been updated. "
                        "Please restart the application to load the new model."
                    )

                    # Force LLM singleton to re-check on next load
                    _reset_llm_singleton()

                except Exception as e:
                    st.error(f"Failed to save model: {e}")

    # ── Section 3: Select Active Model (from existing files) ──
    if len(gguf_files) > 1:
        st.divider()
        st.subheader("🔄 Switch Active Model")
        current_name = model_path.name if model_path.exists() else "(none)"
        model_names = [f.name for f in gguf_files]
        default_idx = model_names.index(current_name) if current_name in model_names else 0

        selected = st.selectbox("Select model", model_names, index=default_idx)
        if selected != current_name:
            if st.button("✅ Activate Selected Model", type="primary"):
                _update_env_var("MODEL_PATH", f"models\\{selected}")
                _reset_llm_singleton()
                st.success(f"Switched to `{selected}`. **Restart required to load.**")
                st.rerun()

    # ── Section 4: LLM Parameters ──
    st.divider()
    st.subheader("⚙️ LLM Parameters")
    st.caption("Adjust generation parameters. Changes are saved to `.env` and take effect on restart.")

    with st.form("llm_params_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_temp = st.slider(
                "Temperature", 0.0, 2.0,
                value=float(MODEL_TEMPERATURE), step=0.05,
                help="Higher = more creative, lower = more focused",
            )
            new_max_tokens = st.slider(
                "Max Tokens", 64, 4096,
                value=int(MODEL_MAX_TOKENS), step=64,
                help="Maximum number of tokens in the response",
            )
        with col2:
            new_n_ctx = st.slider(
                "Context Size (n_ctx)", 512, 16384,
                value=int(MODEL_N_CTX), step=512,
                help="Context window size in tokens",
            )
            new_n_threads = st.slider(
                "CPU Threads", 1, 16,
                value=int(MODEL_N_THREADS), step=1,
                help="Number of CPU threads for inference",
            )

        save_params = st.form_submit_button("💾 Save Parameters", use_container_width=True, type="primary")
        if save_params:
            _update_env_var("MODEL_TEMPERATURE", str(new_temp))
            _update_env_var("MODEL_MAX_TOKENS", str(new_max_tokens))
            _update_env_var("MODEL_N_CTX", str(new_n_ctx))
            _update_env_var("MODEL_N_THREADS", str(new_n_threads))
            _reset_llm_singleton()
            st.success("✅ Parameters saved to `.env`. Restart to apply changes.")

    # ── Section 5: System Prompt ──
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

    # ── Section 6: Embedding Model ──
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


def _reset_llm_singleton():
    """Reset the LLM singleton so it reloads on next use."""
    try:
        from rag import generator
        generator._llm_instance = None
        generator._llm_checked = False
        generator._llm_load_error = None
    except Exception:
        pass
    # Also clear cached health data
    st.session_state.pop("system_health", None)
    st.session_state.pop("health_check_time", None)
