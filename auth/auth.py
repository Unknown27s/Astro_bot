"""
IMS AstroBot — Authentication Module
Session-based auth using Streamlit session state.
"""

import streamlit as st
from database.db import authenticate_user, create_user


def init_session_state():
    """Initialize authentication-related session state."""
    defaults = {
        "authenticated": False,
        "user": None,
        "user_id": None,
        "username": None,
        "role": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login(username: str, password: str) -> bool:
    """Attempt login. Returns True on success and populates session state."""
    user = authenticate_user(username, password)
    if user:
        st.session_state.authenticated = True
        st.session_state.user = user
        st.session_state.user_id = user["id"]
        st.session_state.username = user["username"]
        st.session_state.role = user["role"]
        return True
    return False


def logout():
    """Clear session state for logout."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = None


def require_auth():
    """Check if user is authenticated. Returns True if yes."""
    return st.session_state.get("authenticated", False)


def require_role(allowed_roles: list[str]) -> bool:
    """Check if current user has one of the allowed roles."""
    return st.session_state.get("role") in allowed_roles


def register_user(username: str, password: str, role: str, full_name: str = "") -> bool:
    """Register a new user account."""
    return create_user(username, password, role, full_name)


def render_login_page():
    """Render the login form."""
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0;'>
            <h1>🤖 IMS AstroBot</h1>
            <p style='color: gray; font-size: 1.1rem;'>Institutional AI Assistant — Powered by RAG</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

                if submitted:
                    if username and password:
                        if login(username, password):
                            st.success(f"Welcome back, {st.session_state.username}!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
                    else:
                        st.warning("Please enter both username and password.")

        with tab_register:
            with st.form("register_form"):
                reg_fullname = st.text_input("Full Name", placeholder="Enter your full name")
                reg_username = st.text_input("Username", placeholder="Choose a username", key="reg_user")
                reg_password = st.text_input("Password", type="password", placeholder="Choose a password", key="reg_pass")
                reg_password2 = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
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
                            st.success("Account created! You can now log in.")
                        else:
                            st.error("Username already taken.")
