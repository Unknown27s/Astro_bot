"""
IMS AstroBot — Main Streamlit Application
Entry point with sidebar-based login selection and role-based dashboards.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

# ── Page config (must be first Streamlit command) ──
st.set_page_config(
    page_title="IMS AstroBot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports ──
from auth.auth import init_session_state, login, logout, register_user
from views.chat import render_chat_page
from views.admin import render_admin_page, render_ai_settings_page
from config import CHROMA_PERSIST_DIR, UPLOAD_DIR, EMBEDDING_MODEL, LLM_MODE


# ═══════════════════════════════════════════════════════
# LIGHTWEIGHT HEALTH CHECK (admin only)
# ═══════════════════════════════════════════════════════

def _check_system_health() -> dict:
    """Lightweight health checks — no external LLM provider calls."""
    health = {}
    try:
        from database.db import get_connection
        conn = get_connection()
        conn.execute("SELECT 1")
        u = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]
        d = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()["cnt"]
        conn.close()
        health["sqlite"] = {"status": "ok", "message": f"{u} users, {d} documents"}
    except Exception as e:
        health["sqlite"] = {"status": "error", "message": str(e)}

    chroma_path = Path(CHROMA_PERSIST_DIR)
    health["chromadb"] = (
        {"status": "ok", "message": f"Ready at {chroma_path.name}/"}
        if chroma_path.exists()
        else {"status": "warning", "message": "Will create on first use"}
    )

    # LLM mode only (no provider network calls here)
    health["llm_mode"] = {"status": "ok", "message": LLM_MODE}

    try:
        import sentence_transformers
        health["embeddings"] = {"status": "ok", "message": f"{EMBEDDING_MODEL} (lazy load)"}
    except ImportError:
        health["embeddings"] = {"status": "error", "message": "Package missing"}

    if UPLOAD_DIR.exists():
        fc = len([f for f in UPLOAD_DIR.iterdir() if f.is_file()])
        health["uploads"] = {"status": "ok", "message": f"{fc} files"}
    else:
        health["uploads"] = {"status": "error", "message": "Directory missing"}
    return health


def _check_llm_providers() -> dict:
    """On-demand LLM provider health checks (can be slow / external)."""
    from rag.providers.manager import get_manager

    mgr = get_manager()
    provider_statuses = mgr.get_all_statuses()
    provider_statuses.pop("_mode", None)

    results = {}
    for key in ("ollama", "groq", "gemini"):
        if key in provider_statuses:
            results[key] = provider_statuses[key]
    return results


def render_health_sidebar():
    """Show system health in sidebar (admin only).

    Core components are always checked; LLM providers are on-demand.
    """
    if "system_health" not in st.session_state:
        st.session_state.system_health = _check_system_health()
        st.session_state.health_check_time = datetime.now().strftime("%H:%M:%S")

    health = st.session_state.system_health
    icons = {"ok": "🟢", "warning": "🟡", "error": "🔴"}
    ok_count = sum(1 for v in health.values() if v["status"] == "ok")
    total = len(health)

    st.sidebar.divider()
    if ok_count == total:
        st.sidebar.success(f"System: {ok_count}/{total} OK", icon="✅")
    else:
        err = sum(1 for v in health.values() if v["status"] == "error")
        st.sidebar.error(f"System: {err} issues", icon="❌") if err else st.sidebar.warning("Warnings", icon="⚠️")

    with st.sidebar.expander("🔍 Status Details", expanded=(ok_count < total)):
        # Core components (fast, local checks)
        core_labels = {
            "sqlite": "📦 DB",
            "chromadb": "🔮 VectorDB",
            "llm_mode": "🔀 Mode",
            "embeddings": "🔢 Embed",
            "uploads": "📂 Uploads",
        }
        for key, label in core_labels.items():
            info = health.get(key, {"status": "error", "message": "?"})
            st.markdown(f"{icons.get(info['status'], '⚪')} **{label}**: {info['message']}")

        st.caption(f"Checked {st.session_state.get('health_check_time', '')}")
        if st.button("🔄 Re-check Core", use_container_width=True, key="recheck_core"):
            st.session_state.system_health = _check_system_health()
            st.session_state.health_check_time = datetime.now().strftime("%H:%M:%S")
            st.rerun()

        # On-demand LLM provider checks (can be slow / external)
        st.markdown("---")
        st.markdown("**🤖 LLM Providers (on-demand)**")
        provider_health = st.session_state.get("llm_provider_health")
        provider_labels = {
            "ollama": "🖥️ Ollama",
            "groq": "⚡ Groq",
            "gemini": "💎 Gemini",
        }
        if provider_health:
            for key, info in provider_health.items():
                label = provider_labels.get(key, key)
                st.markdown(
                    f"{icons.get(info.get('status', 'warning'), '⚪')} "
                    f"**{label}**: {info.get('message', '')}"
                )
        else:
            st.caption("Providers not checked yet. Use the button below to run tests.")

        if st.button("⚡ Check LLM Providers", use_container_width=True, key="recheck_llm"):
            st.session_state.llm_provider_health = _check_llm_providers()
            st.session_state.health_check_time = datetime.now().strftime("%H:%M:%S")
            st.rerun()


# ═══════════════════════════════════════════════════════
# LOGIN PAGE (with sidebar role selector)
# ═══════════════════════════════════════════════════════

def render_login_page():
    """Login page with sidebar role selection."""

    # ── Sidebar: role selector ──
    with st.sidebar:
        st.markdown(
            """
            <div style='text-align: center; padding: 1.5rem 0 0.5rem;'>
                <h2>🤖 IMS AstroBot</h2>
                <p style='color: gray; font-size: 0.85rem;'>Institutional AI Assistant</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        st.markdown("#### Select Login Type")

        if "login_mode" not in st.session_state:
            st.session_state.login_mode = "student_faculty"

        if st.button("🔑 Admin Login", use_container_width=True,
                      type="primary" if st.session_state.login_mode == "admin" else "secondary"):
            st.session_state.login_mode = "admin"
            st.rerun()

        if st.button("🎓 Student / Faculty", use_container_width=True,
                      type="primary" if st.session_state.login_mode == "student_faculty" else "secondary"):
            st.session_state.login_mode = "student_faculty"
            st.rerun()

        st.divider()
        st.caption("Choose your role, then log in →")

    # ── Main area: login form ──
    st.markdown(
        """
        <div style='text-align: center; padding: 1rem 0;'>
            <h1>🤖 IMS AstroBot</h1>
            <p style='color: gray; font-size: 1.1rem;'>Institutional AI Assistant — Powered by RAG</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mode = st.session_state.login_mode

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if mode == "admin":
            _render_admin_login()
        else:
            _render_student_faculty_login()


def _render_admin_login():
    """Admin login form."""
    st.markdown("### 🔑 Administrator Login")
    st.caption("Access the full admin dashboard — documents, users, analytics, AI settings.")

    with st.form("admin_login_form"):
        username = st.text_input("Admin Username", placeholder="Enter admin username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        submitted = st.form_submit_button("Login as Admin", use_container_width=True, type="primary")

        if submitted:
            if username and password:
                if login(username, password):
                    if st.session_state.role == "admin":
                        st.success(f"Welcome, Administrator {st.session_state.username}!")
                        st.rerun()
                    else:
                        logout()
                        st.error("This account is not an administrator. Use Student/Faculty login.")
                else:
                    st.error("Invalid username or password.")
            else:
                st.warning("Please enter both username and password.")


def _render_student_faculty_login():
    """Student/Faculty login + registration."""
    tab_login, tab_register = st.tabs(["🎓 Login", "📝 Register"])

    with tab_login:
        st.markdown("### 🎓 Student / Faculty Login")
        st.caption("Access the Q&A chatbot to ask questions about institutional documents.")

        with st.form("sf_login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

            if submitted:
                if username and password:
                    if login(username, password):
                        if st.session_state.role in ("student", "faculty"):
                            st.success(f"Welcome, {st.session_state.username}!")
                            st.rerun()
                        else:
                            logout()
                            st.error("Admin accounts should use the Admin Login option in the sidebar.")
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.warning("Please enter both username and password.")

    with tab_register:
        st.markdown("### 📝 Create Account")
        with st.form("register_form"):
            reg_fullname = st.text_input("Full Name", placeholder="Enter your full name")
            reg_username = st.text_input("Username", placeholder="Choose a username", key="reg_user")
            reg_password = st.text_input("Password", type="password", placeholder="Choose a password", key="reg_pass")
            reg_password2 = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
            reg_role = st.selectbox("Role", ["student", "faculty"])
            reg_submitted = st.form_submit_button("Register", use_container_width=True)

            if reg_submitted:
                if not all([reg_fullname, reg_username, reg_password, reg_password2]):
                    st.warning("Please fill in all fields.")
                elif reg_password != reg_password2:
                    st.error("Passwords do not match.")
                elif len(reg_password) < 4:
                    st.error("Password must be at least 4 characters.")
                else:
                    if register_user(reg_username, reg_password, reg_role, reg_fullname):
                        st.success("Account created! Switch to the Login tab.")
                    else:
                        st.error("Username already taken.")


# ═══════════════════════════════════════════════════════
# ADMIN DASHBOARD FLOW
# ═══════════════════════════════════════════════════════

def run_admin_dashboard():
    """Full admin experience with sidebar navigation."""
    with st.sidebar:
        st.markdown(
            """
            <div style='text-align: center; padding: 1rem 0;'>
                <h2>🤖 IMS AstroBot</h2>
                <p style='color: gray; font-size: 0.8rem;'>Admin Dashboard</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        st.markdown(f"**🔑 {st.session_state.username}** (Admin)")
        st.divider()

        page = st.radio(
            "Navigate",
            ["📄 Documents", "📊 Analytics", "👥 Users", "🤖 AI Settings", "💬 Test Chat"],
            label_visibility="collapsed",
        )

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

    # Health dashboard in sidebar (admin only)
    render_health_sidebar()

    # Footer
    with st.sidebar:
        st.markdown(
            "<div style='padding:0.5rem;color:gray;font-size:0.75rem;text-align:center;'>"
            "IMS AstroBot v2.0<br>Powered by RAG + Ollama/Groq/Gemini</div>",
            unsafe_allow_html=True,
        )

    # ── Page routing ──
    try:
        if page == "📄 Documents":
            render_admin_page()
        elif page == "📊 Analytics":
            _render_analytics_page()
        elif page == "👥 Users":
            _render_users_page()
        elif page == "🤖 AI Settings":
            render_ai_settings_page()
        elif page == "💬 Test Chat":
            render_chat_page()
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc(), language="text")


def _render_analytics_page():
    """Analytics dashboard."""
    from database.db import get_analytics
    from ingestion.embedder import get_collection_stats
    import pandas as pd

    st.markdown("### 📊 Usage Analytics")
    st.divider()

    analytics = get_analytics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Queries", analytics["total_queries"])
    c2.metric("Total Documents", analytics["total_documents"])
    c3.metric("Total Users", analytics["total_users"])
    c4.metric("Avg Response Time", f"{analytics['avg_response_ms']}ms")

    st.divider()
    if analytics["daily_queries"]:
        st.subheader("Queries Per Day (Last 7 Days)")
        df = pd.DataFrame(analytics["daily_queries"])
        df.columns = ["Date", "Queries"]
        st.bar_chart(df.set_index("Date"))
    else:
        st.info("No query data yet. Use the Test Chat to generate some!")

    if analytics["top_users"]:
        st.subheader("Top Querying Users")
        df_u = pd.DataFrame(analytics["top_users"])
        df_u.columns = ["Username", "Queries"]
        st.dataframe(df_u, use_container_width=True, hide_index=True)

    st.divider()
    stats = get_collection_stats()
    st.metric("Total Chunks in Vector DB", stats["total_chunks"])

    # Query Logs
    st.divider()
    st.subheader("📋 Recent Query Logs")
    from database.db import get_query_logs
    logs = get_query_logs(limit=50)
    if not logs:
        st.info("No queries logged yet.")
    else:
        for log in logs:
            with st.expander(
                f"🔍 {log['query_text'][:80]}{'...' if len(log['query_text']) > 80 else ''} — "
                f"by {log['username']} ({log['created_at'][:16]})"
            ):
                st.markdown(f"**Query:** {log['query_text']}")
                st.markdown(f"**Response:** {log['response_text']}")
                if log["sources"]:
                    st.markdown(f"**Sources:** {log['sources']}")
                st.caption(f"Response time: {log['response_time_ms']:.0f}ms | Time: {log['created_at']}")


def _render_users_page():
    """User management — pulled from admin.py's existing logic."""
    from database.db import get_all_users, create_user, delete_user, toggle_user_active

    st.markdown("### 👥 User Management")
    st.divider()

    st.subheader("Create New User")
    with st.form("create_user_form"):
        c1, c2 = st.columns(2)
        with c1:
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
        with c2:
            new_fullname = st.text_input("Full Name")
            new_role = st.selectbox("Role", ["student", "faculty", "admin"])
        if st.form_submit_button("➕ Create User", use_container_width=True):
            if new_username and new_password:
                if create_user(new_username, new_password, new_role, new_fullname):
                    st.success(f"User '{new_username}' created as {new_role}.")
                    st.rerun()
                else:
                    st.error("Username already exists.")
            else:
                st.warning("Username and password are required.")

    st.divider()
    st.subheader("Existing Users")
    users = get_all_users()
    if users:
        for user in users:
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            with c1:
                icon = "🟢" if user["is_active"] else "🔴"
                st.markdown(f"{icon} **{user['username']}** ({user['full_name']})")
            with c2:
                badges = {"admin": "🔑 Admin", "faculty": "🎓 Faculty", "student": "📚 Student"}
                st.markdown(badges.get(user["role"], user["role"]))
            with c3:
                active = bool(user["is_active"])
                if st.button("Disable" if active else "Enable", key=f"toggle_{user['id']}"):
                    toggle_user_active(user["id"], not active)
                    st.rerun()
            with c4:
                if user["username"] != st.session_state.username:
                    if st.button("🗑️", key=f"del_user_{user['id']}"):
                        delete_user(user["id"])
                        st.rerun()
    else:
        st.info("No users found.")


# ═══════════════════════════════════════════════════════
# STUDENT / FACULTY FLOW
# ═══════════════════════════════════════════════════════

def run_student_faculty():
    """Simple chat-only interface for students and faculty."""
    with st.sidebar:
        st.markdown(
            """
            <div style='text-align: center; padding: 1rem 0;'>
                <h2>🤖 IMS AstroBot</h2>
                <p style='color: gray; font-size: 0.8rem;'>Ask Questions</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        role_icons = {"faculty": "🎓", "student": "📚"}
        icon = role_icons.get(st.session_state.role, "👤")
        st.markdown(f"**{icon} {st.session_state.username}**")
        st.caption(f"Role: {st.session_state.role.title()}")
        st.divider()

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.sources_history = []
            st.rerun()

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

        st.markdown(
            "<div style='padding:0.5rem;color:gray;font-size:0.75rem;text-align:center;'>"
            "IMS AstroBot v1.0</div>",
            unsafe_allow_html=True,
        )

    # Render the chat page (no sidebar controls — we handle them above)
    try:
        render_chat_page()
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc(), language="text")

# ═══════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════

def main():
    """Main application controller."""
    init_session_state()

    # Not authenticated → login page with sidebar role selector
    if not st.session_state.get("authenticated", False):
        render_login_page()
        return

    # Authenticated → route by role
    if st.session_state.role == "admin":
        run_admin_dashboard()
    else:
        run_student_faculty()


if __name__ == "__main__":
    main()
