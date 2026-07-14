import streamlit as st
import requests

FASTAPI_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Chatbot", page_icon="🤖")

# ----------------------------
# Session State
# ----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []


# ==========================
# LOGIN / REGISTER
# ==========================

if not st.session_state.logged_in:

    st.title("🤖 AI Chatbot")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:

        username = st.text_input("Username", key="login_user")
        password = st.text_input(
            "Password",
            type="password",
            key="login_pass"
        )

        if st.button("Login"):

            res = requests.post(
                f"{FASTAPI_URL}/auth/login",
                json={
                    "username": username,
                    "password": password
                }
            )

            data = res.json()

            if data.get("success"):

                st.session_state.logged_in = True
                st.session_state.username = username

                # Create session
                s = requests.post(
                    f"{FASTAPI_URL}/session",
                    params={"username": username}
                )

                st.session_state.session_id = s.json()["session_id"]

                st.rerun()

            else:
                st.error(data["error"])

    with tab2:

        username = st.text_input("Username", key="reg_user")
        password = st.text_input(
            "Password",
            type="password",
            key="reg_pass"
        )

        if st.button("Register"):

            res = requests.post(
                f"{FASTAPI_URL}/auth/register",
                json={
                    "username": username,
                    "password": password
                }
            )

            st.success(res.json()["status"])

    st.stop()

# ==========================
# CHAT PAGE
# ==========================

st.title("💬 AI Chatbot")

st.write(f"Logged in as **{st.session_state.username}**")

# ---------------- Sidebar ----------------

with st.sidebar:

    st.header("Sessions")

    if st.button("New Chat"):

        s = requests.post(
            f"{FASTAPI_URL}/session",
            params={
                "username": st.session_state.username
            }
        )

        st.session_state.session_id = s.json()["session_id"]
        st.session_state.messages = []

        st.rerun()

    st.divider()

    # Load sessions
    sessions = requests.get(
        f"{FASTAPI_URL}/session",
        params={
            "username": st.session_state.username
        }
    ).json()

    for sid in sessions:

        if st.button(sid[:8], key=sid):

            st.session_state.session_id = sid

            history = requests.get(
                f"{FASTAPI_URL}/history/{sid}",
                params={
                    "username": st.session_state.username
                }
            ).json()

            st.session_state.messages = [
                x for x in history
                if x["role"] != "system"
            ]

            st.rerun()

    st.divider()

    st.subheader("Upload PDF")

    pdf = st.file_uploader(
        "Upload",
        type=["pdf"]
    )

    if pdf:

        files = {
            "f": (
                pdf.name,
                pdf,
                "application/pdf"
            )
        }

        r = requests.post(
            f"{FASTAPI_URL}/upload",
            files=files
        )

        st.success(r.json())

# ---------------- Chat ----------------

st.caption(f"Session: {st.session_state.session_id}")

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- Input ----------------

prompt = st.chat_input("Type your message...")

if prompt:

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            payload = {
                "session_id": st.session_state.session_id,
                "message": prompt
            }

            r = requests.post(
                f"{FASTAPI_URL}/message",
                json=payload
            )

            if r.status_code == 200:

                bot = r.json()["e"]

                st.markdown(bot)

                st.caption(
                    f"Route: {r.json()['debug_route']}"
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": bot
                    }
                )

            else:
                st.error(r.text)