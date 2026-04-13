"""
IMS AstroBot — Chat Interface Page
Streamlit-based conversational UI with RAG pipeline.
"""

import time
import streamlit as st
from rag.retriever import retrieve_context, format_context_for_llm, get_source_citations
from rag.generator import generate_response, is_llm_available
from rag.pipeline_trace import PipelineTrace
from database.db import log_query
from config import CONV_ENABLED


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
                trace = PipelineTrace(query=prompt, username=st.session_state.username)

                # Step 1: Retrieve relevant chunks
                from rag.conversation_history import get_history
                history = get_history(st.session_state.user_id)
                search_query = prompt
                if history:
                    previous_queries = " ".join([q for q, r in history])
                    search_query = f"{previous_queries} {prompt}"
                
                chunks = retrieve_context(search_query, trace=trace)

                # Step 2: Format context for LLM
                context = format_context_for_llm(chunks)

                # Step 3: Generate response (with memory pre-check and post-store)
                gen_result = generate_response(
                    prompt, 
                    context,
                    user_id=st.session_state.user_id,
                    sources=[c.get("source", "") for c in chunks],
                    trace=trace,
                )
                
                # Extract response from dict (handles both old string format and new dict format)
                if isinstance(gen_result, dict):
                    response = gen_result.get("response", "")
                    from_memory = gen_result.get("from_memory", False)
                else:
                    response = gen_result  # Fallback for backward compatibility
                    from_memory = False

                # Step 4: Get citations
                citations = get_source_citations(chunks)

                elapsed_ms = (time.time() - start_time) * 1000
                unique_sources = len(set(c.get("source", "") for c in chunks))
                trace.record_response(
                    response_length=len(response) if response else 0,
                    unique_sources=unique_sources,
                    from_memory=from_memory,
                )
                trace.print_summary()

            # Display memory cache indicator if from memory
            if from_memory and CONV_ENABLED:
                st.success("⚡ **Instant Response** (from memory cache)", icon="✨")
            
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
