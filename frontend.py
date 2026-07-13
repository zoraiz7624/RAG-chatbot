import streamlit as st
import requests

st.set_page_config(
    page_title="Secure AI Assistant",
    page_icon="🤖",
    layout="wide"
)

FASTAPI_URL = "http://127.0.0.1:8000"

# ==========================
# CUSTOM CSS
# ==========================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #0F172A;
    color: #F8FAFC;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header {visibility: hidden;}

h1, h2, h3 {
    font-weight: 700 !important;
    letter-spacing: -0.3px;
    color: #F8FAFC;
}

/* ---------- Hero ---------- */

.hero-title {
    font-size: 2.3rem;
    font-weight: 800;
    color: #F8FAFC;
    text-align: center;
    margin-bottom: 4px;
    animation: fadeIn 0.6s ease;
}

.hero-subtitle {
    text-align: center;
    color: #94A3B8;
    font-size: 1rem;
    margin-top: 0;
    margin-bottom: 4px;
}

.hero-tagline {
    text-align: center;
    color: #3B82F6;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 28px;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-6px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ---------- Auth card ---------- */

[data-testid="stVerticalBlockBorderWrapper"] {
    background: #1E293B;
    border: 1px solid #334155 !important;
    border-radius: 14px;
    box-shadow: 0 10px 34px rgba(0, 0, 0, 0.45);
    animation: fadeIn 0.5s ease;
}

.auth-tip {
    color: #94A3B8;
    font-size: 0.85rem;
    line-height: 1.7;
    background: #111827;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 10px;
}

.auth-caption {
    color: #94A3B8;
    font-size: 0.9rem;
    margin-bottom: 12px;
}

/* ---------- Tabs ---------- */

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    border-bottom: 1px solid #334155;
}

.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 8px 8px 0 0;
    padding: 10px 18px;
    color: #94A3B8;
    font-weight: 600;
    transition: color 0.15s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #F8FAFC;
}

.stTabs [aria-selected="true"] {
    background-color: transparent;
    color: #3B82F6 !important;
    font-weight: 700;
    border-bottom: 2px solid #3B82F6;
}

/* ---------- Inputs ---------- */

.stTextInput input {
    background-color: #111827 !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    color: #F8FAFC !important;
    padding: 10px 12px !important;
    transition: border 0.15s ease;
}

.stTextInput input:focus {
    border: 1px solid #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
}

/* ---------- Buttons ---------- */

.stButton button {
    background: #3B82F6;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 22px;
    font-weight: 600;
    transition: all 0.15s ease;
    width: 100%;
    box-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

.stButton button:hover {
    background: #2563EB;
    box-shadow: 0 6px 16px rgba(59, 130, 246, 0.35);
    transform: translateY(-1px);
}

.stButton button:active {
    transform: translateY(0);
}

/* ---------- Camera ---------- */

[data-testid="stCameraInput"] {
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 10px;
    background: #111827;
    max-width: 320px;
    margin: 0 auto;
}

[data-testid="stCameraInput"] video,
[data-testid="stCameraInput"] img {
    border-radius: 10px;
    max-height: 240px;
    width: 100%;
    object-fit: cover;
}

[data-testid="stCameraInput"] button {
    width: auto !important;
    padding: 8px 18px !important;
    background: #334155;
}

[data-testid="stCameraInput"] button:hover {
    background: #475569;
}

/* ---------- Sidebar ---------- */

section[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid #334155;
}

.sidebar-user-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 16px;
}

.sidebar-user-name {
    font-weight: 700;
    color: #F8FAFC;
    font-size: 1rem;
}

.sidebar-user-status {
    color: #22C55E;
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 2px;
}

.sidebar-section-label {
    color: #94A3B8;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    margin: 18px 0 8px 2px;
}

.session-info-box {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 0.8rem;
    color: #94A3B8;
    margin-bottom: 10px;
}

.session-info-box b {
    color: #F8FAFC;
}

section[data-testid="stSidebar"] .stButton button {
    background: #1E293B;
    color: #F8FAFC;
    text-align: left;
    font-weight: 500;
    border: 1px solid #334155;
}

section[data-testid="stSidebar"] .stButton button:hover {
    background: #334155;
    color: #3B82F6;
    border: 1px solid #3B82F6;
}

/* New Chat button gets primary treatment via key targeting handled inline */

/* ---------- Chat header ---------- */

.chat-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
}

.jwt-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(34, 197, 94, 0.12);
    border: 1px solid rgba(34, 197, 94, 0.35);
    color: #22C55E;
    padding: 6px 14px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.78rem;
    float: right;
}

/* ---------- Chat bubbles ---------- */

[data-testid="stChatMessage"] {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 6px 12px;
    margin-bottom: 10px;
    animation: fadeIn 0.35s ease;
}

/* ---------- Chat input ---------- */

[data-testid="stChatInput"] {
    border-radius: 12px;
    background: #1E293B;
    border: 1px solid #334155;
}

/* ---------- Alerts ---------- */

.stAlert {
    border-radius: 10px;
}

/* ---------- Empty state ---------- */

.empty-state {
    text-align: center;
    padding: 60px 20px 30px 20px;
}

.empty-state-emoji {
    font-size: 2.6rem;
    margin-bottom: 10px;
}

.empty-state-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #F8FAFC;
    margin-bottom: 6px;
}

.empty-state-subtitle {
    color: #94A3B8;
    font-size: 0.95rem;
    margin-bottom: 24px;
}

/* Suggested prompt buttons: reuse stButton but constrain width via columns */

/* ---------- Footer ---------- */

.app-footer {
    text-align: center;
    color: #475569;
    font-size: 0.75rem;
    margin-top: 30px;
    padding-top: 14px;
    border-top: 1px solid #1E293B;
}

</style>
""", unsafe_allow_html=True)

# This variable will tell Streamlit whether the user is logged in.
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ==========================
# LOGIN / REGISTER SCREEN
# ==========================

if not st.session_state.authenticated:

    st.markdown('<div class="hero-title">🤖 Secure AI Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Enterprise-grade AI chatbot protected using facial authentication.</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-tagline">FAST &nbsp;•&nbsp; SECURE &nbsp;•&nbsp; INTELLIGENT</div>', unsafe_allow_html=True)

    left, center, right = st.columns([1, 2, 1])
    with center:

        card = st.container(border=True)

        with card:

            tab1, tab2 = st.tabs(["Register Face", "Login"])

            # ---------------- REGISTER ---------------- #

            with tab1:

                st.subheader("Create Face Login Profile")
                st.markdown('<div class="auth-caption">Set up biometric login for your account.</div>', unsafe_allow_html=True)

                reg_username = st.text_input(
                    "Enter Username",
                    key="reg_user"
                )

                reg_image = st.camera_input(
                    "Position your face inside the frame",
                    key="reg_cam"
                )

                st.markdown(
                    '<div class="auth-tip">'
                    '✔ Face clearly visible<br>'
                    '✔ Good, even lighting<br>'
                    '✔ Look directly ahead<br>'
                    '✔ Remove sunglasses or masks'
                    '</div>',
                    unsafe_allow_html=True
                )

                if reg_image is not None and reg_username:

                    if st.button("Register", key="reg_btn"):

                        files = {
                            "file": (
                                f"{reg_username}.jpg",
                                reg_image.getvalue(),
                                "image/jpeg"
                            )
                        }

                        with st.spinner("🟢 Creating face profile..."):

                            response = requests.post(
                                f"{FASTAPI_URL}/auth/register-face/{reg_username}",
                                files=files
                            )

                        if response.status_code == 200:
                            st.success(f"✅ {response.json()['message']}")
                        else:
                            st.error(f"❌ {response.json()['detail']}")

            # ---------------- LOGIN ---------------- #

            with tab2:

                st.subheader("Login")
                st.markdown('<div class="auth-caption">Authenticate using facial recognition.</div>', unsafe_allow_html=True)

                login_username = st.text_input(
                    "Username",
                    key="login_user"
                )

                login_image = st.camera_input(
                    "Position your face inside the frame",
                    key="login_cam"
                )

                st.markdown(
                    '<div class="auth-tip">'
                    '✔ Face clearly visible<br>'
                    '✔ Good, even lighting<br>'
                    '✔ Look directly at the camera'
                    '</div>',
                    unsafe_allow_html=True
                )

                if login_image is not None and login_username:

                    files = {
                        "file": (
                            f"{login_username}.jpg",
                            login_image.getvalue(),
                            "image/jpeg"
                        )
                    }

                    with st.spinner("🔍 Verifying identity..."):

                        response = requests.post(
                            f"{FASTAPI_URL}/auth/login-face/{login_username}",
                            files=files
                        )

                    if response.status_code == 200:

                        st.session_state.authenticated = True
                        st.session_state.username = login_username
                        st.session_state.token = response.json()["token"]

                        st.rerun()
                    else:
                        try:
                            error = response.json().get(
                                "detail",
                                "Authentication Failed"
                            )
                        except Exception:
                            error = response.text

                        st.error(f"❌ Face not recognized. {error}")

    st.markdown(
        '<div class="app-footer">Powered by FastAPI • MongoDB Atlas • Streamlit • InsightFace • OpenRouter</div>',
        unsafe_allow_html=True
    )


# ==========================
# CHAT SCREEN
# ==========================

else:

    header_col, badge_col = st.columns([3, 1])

    with header_col:
        st.markdown('<div class="hero-title" style="text-align:left;font-size:1.8rem;">🤖 Secure AI Assistant</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle" style="text-align:left;">AI-powered assistant secured with biometric authentication.</div>', unsafe_allow_html=True)

    with badge_col:
        st.markdown(
            '<div style="text-align:right;padding-top:18px;">'
            '<span class="jwt-badge">🔒 Secure Session · JWT Active</span>'
            '</div>',
            unsafe_allow_html=True
        )

    with st.sidebar:

        st.markdown(
            f'<div class="sidebar-user-card">'
            f'<div class="sidebar-user-name">🙂 {st.session_state.username}</div>'
            f'<div class="sidebar-user-status">🟢 Online · Verified User</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if st.button("➕ New Chat", key="new_chat_btn"):

            st.session_state.pop("session_id", None)
            st.rerun()

        # ---------------- CREATE SESSION ---------------- #

        if "session_id" not in st.session_state:

            resp = requests.post(
                f"{FASTAPI_URL}/session",
                headers={
                    "Authorization": f"Bearer {st.session_state.token}"
                }
            )

            if resp.status_code in [200, 201]:

                st.session_state.session_id = resp.json()["session_id"]

            else:

                st.error("Failed to create session.")
                st.stop()

        st.markdown(
            f'<div class="session-info-box">'
            f'<b>Current Session</b><br>ID: {st.session_state.session_id[:8]}...'
            f'</div>',
            unsafe_allow_html=True
        )

        # ---------------- SIDEBAR ---------------- #

        st.markdown('<div class="sidebar-section-label">Recent Sessions</div>', unsafe_allow_html=True)

        sessions_resp = requests.get(
            f"{FASTAPI_URL}/session",
            headers={
                "Authorization": f"Bearer {st.session_state.token}"
            }
        )

        sessions = sessions_resp.json()

        for sid in sessions:

            if st.button(f"💬 {sid[:8]}", key=sid):

                st.session_state.session_id = sid
                st.rerun()

        st.markdown('<div class="sidebar-section-label">Account</div>', unsafe_allow_html=True)

        if st.button("🚪 Logout", key="logout_btn"):

            st.session_state.authenticated = False

            st.session_state.pop("username", None)
            st.session_state.pop("token", None)
            st.session_state.pop("session_id", None)

            st.rerun()

    # ---------------- LOAD HISTORY ---------------- #

    history_resp = requests.get(
        f"{FASTAPI_URL}/history/{st.session_state.session_id}",
        headers={
            "Authorization": f"Bearer {st.session_state.token}"
        }
    )

    if history_resp.status_code == 200:

        st.session_state.messages = [
            m for m in history_resp.json()
            if m["role"] != "system"
        ]

    else:

        st.session_state.messages = []

    # ---------------- SHOW CHAT / EMPTY STATE ---------------- #

    if "queued_prompt" not in st.session_state:
        st.session_state.queued_prompt = None

    if len(st.session_state.messages) == 0:

        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-state-emoji">🤖</div>'
            f'<div class="empty-state-title">Hello {st.session_state.username}!</div>'
            '<div class="empty-state-subtitle">How can I help you today?</div>'
            '</div>',
            unsafe_allow_html=True
        )

        suggestions = [
            "📚 Explain JWT",
            "💻 Write Python Code",
            "🤖 Explain AI",
            "🧠 Summarize Text"
        ]

        s1, s2, s3, s4 = st.columns(4)
        suggestion_cols = [s1, s2, s3, s4]

        for col, suggestion in zip(suggestion_cols, suggestions):
            with col:
                if st.button(suggestion, key=f"sugg_{suggestion}"):
                    st.session_state.queued_prompt = suggestion.split(" ", 1)[1]

    else:

        for msg in st.session_state.messages:

            with st.chat_message(msg["role"]):

                st.markdown(msg["content"])

    # ---------------- CHAT INPUT ---------------- #

    prompt = st.chat_input("Ask anything...")

    if st.session_state.queued_prompt and not prompt:
        prompt = st.session_state.queued_prompt
        st.session_state.queued_prompt = None

    if prompt:

        with st.chat_message("user"):

            st.markdown(prompt)

        payload = {

            "session_id": st.session_state.session_id,

            "message": prompt

        }

        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):

                response = requests.post(

                    f"{FASTAPI_URL}/message",

                    json=payload,

                    headers={
                        "Authorization": f"Bearer {st.session_state.token}"
                    }
                )

                if response.status_code == 200:

                    bot = response.json()["e"]
                    st.markdown(bot)

                else:

                    st.error(response.text)

    st.markdown(
        '<div class="app-footer">Powered by FastAPI • MongoDB Atlas • Streamlit • InsightFace • OpenRouter</div>',
        unsafe_allow_html=True
    )