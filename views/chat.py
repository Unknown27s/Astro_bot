"""
IMS AstroBot — Chat Interface Page
Streamlit-based conversational UI with RAG pipeline.
"""

import time
import streamlit as st
from rag.retriever import retrieve_context, format_context_for_llm, get_source_citations
from rag.generator import generate_response, is_llm_available
from database.db import log_query


def render_chat_page():
    """Render the main chat interface."""

    # ── Header ──
    col_title, col_status = st.columns([4, 1])
    with col_title:
        st.markdown("### 💬 Chat with AstroBot")
        st.caption(f"Logged in as **{st.session_state.username}** ({st.session_state.role})")
    with col_status:
        if is_llm_available():
            st.success("🟢 LLM Online", icon="✅")
        else:
            st.warning("🟡 Fallback Mode", icon="⚠️")

    st.divider()

    # ── Initialize chat history ──
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "sources_history" not in st.session_state:
        st.session_state.sources_history = []

    # ── Display chat messages ──
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.info(
                "👋 Welcome! I'm **IMS AstroBot**, your institutional AI assistant.\n\n"
                "Ask me anything about uploaded institutional documents — regulations, policies, handbooks, circulars, and more.",
                icon="🤖",
            )

        for i, msg in enumerate(st.session_state.chat_history):
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])
                # Show sources for assistant messages
                if msg["role"] == "assistant" and i < len(st.session_state.sources_history):
                    sources = st.session_state.sources_history[i]
                    if sources:
                        with st.expander("📚 Sources", expanded=False):
                            st.markdown(sources)

    # ── Chat input ──
    if prompt := st.chat_input("Ask a question about institutional documents..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Searching documents and generating response..."):
                start_time = time.time()

                # Step 1: Retrieve relevant chunks
                chunks = retrieve_context(prompt)

                # Step 2: Format context for LLM
                context = format_context_for_llm(chunks)

                # Step 3: Generate response
                response = generate_response(prompt, context)

                # Step 4: Get citations
                citations = get_source_citations(chunks)

                elapsed_ms = (time.time() - start_time) * 1000

            st.markdown(response)

            if citations:
                with st.expander("📚 Sources", expanded=False):
                    st.markdown(citations)

        # Store in history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        # Pad sources_history to align with chat_history
        while len(st.session_state.sources_history) < len(st.session_state.chat_history) - 1:
            st.session_state.sources_history.append("")
        st.session_state.sources_history.append(citations)

        # Log query to database
        try:
            source_names = ", ".join([c.get("source", "") for c in chunks[:3]])
            log_query(
                user_id=st.session_state.user_id,
                username=st.session_state.username,
                query_text=prompt,
                response_text=response[:500],
                sources=source_names,
                response_time_ms=elapsed_ms,
            )
        except Exception as e:
            print(f"[Chat] Error logging query: {e}")
