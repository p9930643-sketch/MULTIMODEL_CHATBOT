import os
import streamlit as st
import requests
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Aura - Multimodal AI Companion",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #64748b;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .chat-bubble-user {
        background-color: #3b82f6;
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin-bottom: 10px;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .chat-bubble-assistant {
        background-color: #f1f5f9;
        color: #1e293b;
        padding: 14px 18px;
        border-radius: 18px 18px 18px 4px;
        margin-bottom: 10px;
        max-width: 85%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .citation-card {
        background-color: #f8fafc;
        border-left: 4px solid #6366f1;
        padding: 8px 12px;
        margin-top: 8px;
        border-radius: 4px;
        font-size: 0.88rem;
    }
    .crisis-banner {
        background-color: #fef2f2;
        border: 1px solid #f87171;
        color: #991b1b;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 12px;
        font-size: 0.95rem;
    }
    .tag-rag {
        background-color: #e0e7ff;
        color: #4338ca;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_file_path" not in st.session_state:
    st.session_state.uploaded_file_path = None
if "active_modality" not in st.session_state:
    st.session_state.active_modality = "text"

# Helper API functions
def check_api_health():
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return r.status_code == 200, r.json() if r.status_code == 200 else {}
    except Exception:
        return False, {}

def fetch_conversations():
    try:
        r = requests.get(f"{API_BASE_URL}/conversations", timeout=3)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def fetch_messages(conv_id: str):
    try:
        r = requests.get(f"{API_BASE_URL}/conversations/{conv_id}/messages", timeout=3)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def delete_conversation(conv_id: str):
    try:
        requests.delete(f"{API_BASE_URL}/conversations/{conv_id}", timeout=3)
    except Exception:
        pass

# Sidebar
with st.sidebar:
    st.title("✨ Aura Companion")
    
    # API Health indicator
    is_healthy, health_info = check_api_health()
    if is_healthy:
        dialect = health_info.get("database_dialect", "active")
        st.caption(f"🟢 Backend Online (DB: `{dialect}`)")
    else:
        st.warning("⚠️ Backend API offline. Please ensure FastAPI server is running.")

    if st.button("➕ New Conversation", use_container_width=True):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.session_state.uploaded_file_path = None
        st.session_state.active_modality = "text"
        st.rerun()

    st.markdown("---")
    st.subheader("💬 Recent Chats")
    conversations = fetch_conversations()
    if conversations:
        for conv in conversations:
            col_a, col_b = st.columns([4, 1])
            is_active = conv["conversation_id"] == st.session_state.conversation_id
            label = ("▶ " if is_active else "") + conv["title"]
            if col_a.button(label, key=f"conv_{conv['conversation_id']}", use_container_width=True):
                st.session_state.conversation_id = conv["conversation_id"]
                st.session_state.messages = fetch_messages(conv["conversation_id"])
                st.session_state.uploaded_file_path = None
                st.rerun()
            if col_b.button("🗑️", key=f"del_{conv['conversation_id']}"):
                delete_conversation(conv["conversation_id"])
                if is_active:
                    st.session_state.conversation_id = None
                    st.session_state.messages = []
                st.rerun()
    else:
        st.caption("No past conversations yet.")

    st.markdown("---")
    st.subheader("📚 Knowledge Base (RAG)")
    try:
        docs_resp = requests.get(f"{API_BASE_URL}/documents", timeout=2)
        if docs_resp.status_code == 200:
            docs = docs_resp.json()
            if docs:
                for d in docs:
                    st.caption(f"📄 **{d['filename']}** ({d['chunk_count']} chunks) - `{d['processing_status']}`")
            else:
                st.caption("No documents ingested yet.")
    except Exception:
        st.caption("Could not load knowledge sources.")

# Main Chat View
st.markdown('<div class="main-title">Aura: Multimodal AI Companion</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Empathetic companionship, visual analysis, speech understanding, and grounded knowledge retrieval.</div>', unsafe_allow_html=True)

# Display message history
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        sender = msg.get("sender")
        content = msg.get("message_content", "")
        metadata = msg.get("metadata_json") or {}

        if sender == "user":
            st.markdown(f'<div class="chat-bubble-user">{content}</div>', unsafe_allow_html=True)
        else:
            # Check for safety flags
            if metadata.get("safety") == "crisis_intercepted":
                st.markdown(f'<div class="crisis-banner">🚨 <strong>Priority Support Intercept:</strong><br>{content}</div>', unsafe_allow_html=True)
            else:
                # Normal or grounded response
                tag_html = '<span class="tag-rag">RAG Grounded</span>' if metadata.get("citations") else ""
                st.markdown(f'<div class="chat-bubble-assistant">{content}<br>{tag_html}</div>', unsafe_allow_html=True)

                # Citations
                citations = metadata.get("citations", [])
                if citations:
                    with st.expander(f"📑 Sources & Citations ({len(citations)})"):
                        for idx, c in enumerate(citations, 1):
                            st.markdown(
                                f'<div class="citation-card">'
                                f'<strong>Source [{idx}]: {c.get("document_name")}</strong> (Relevance: {c.get("relevance_score")})<br>'
                                f'<em>"{c.get("snippet")}"</em>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

                # Audio playback if present
                audio_url = metadata.get("audio_url")
                if audio_url:
                    full_audio_url = f"{API_BASE_URL}{audio_url}"
                    st.audio(full_audio_url)

# Input and Multimodal Tools Area
st.markdown("---")

col_upload1, col_upload2, col_upload3, col_toggle = st.columns([1.5, 1.5, 1.5, 1.5])

with col_upload1:
    img_file = st.file_uploader("🖼️ Upload Image", type=["jpg", "jpeg", "png"], key="img_uploader")
with col_upload2:
    doc_file = st.file_uploader("📄 Upload Document", type=["pdf", "txt"], key="doc_uploader")
with col_upload3:
    aud_file = st.file_uploader("🎙️ Upload Audio", type=["wav", "mp3", "ogg", "m4a"], key="aud_uploader")
with col_toggle:
    generate_speech = st.checkbox("🔊 Voice Response (TTS)", value=False)
    use_rag_toggle = st.checkbox("🔍 Ground in Knowledge Base", value=True)

# Handle file uploads dynamically
if img_file and st.session_state.uploaded_file_path != img_file.name:
    with st.spinner("Uploading image..."):
        try:
            files = {"file": (img_file.name, img_file.getvalue(), img_file.type)}
            res = requests.post(f"{API_BASE_URL}/upload/image", files=files, timeout=10)
            if res.status_code == 200:
                data = res.json()
                st.session_state.uploaded_file_path = data["file_path"]
                st.session_state.active_modality = "image"
                st.success(f"Attached image: {img_file.name}")
            else:
                st.error(res.json().get("detail", "Image upload failed"))
        except Exception as e:
            st.error(f"Image upload connection error: {e}")

if doc_file and st.session_state.uploaded_file_path != doc_file.name:
    with st.spinner("Uploading and indexing document..."):
        try:
            files = {"file": (doc_file.name, doc_file.getvalue(), doc_file.type)}
            res = requests.post(f"{API_BASE_URL}/upload/document", files=files, timeout=10)
            if res.status_code == 200:
                data = res.json()
                doc_id = data.get("document_id")
                st.session_state.uploaded_file_path = data["file_path"]
                st.session_state.active_modality = "document"
                # Auto-trigger ingestion for RAG
                if doc_id:
                    ingest_res = requests.post(f"{API_BASE_URL}/knowledge/ingest/{doc_id}", timeout=20)
                    if ingest_res.status_code == 200:
                        st.success(f"Ingested '{doc_file.name}' into RAG knowledge base!")
                    else:
                        st.warning("Uploaded, but ingestion index had an issue.")
            else:
                st.error(res.json().get("detail", "Document upload failed"))
        except Exception as e:
            st.error(f"Document upload connection error: {e}")

if aud_file and st.session_state.uploaded_file_path != aud_file.name:
    with st.spinner("Uploading audio..."):
        try:
            files = {"file": (aud_file.name, aud_file.getvalue(), aud_file.type)}
            res = requests.post(f"{API_BASE_URL}/upload/audio", files=files, timeout=10)
            if res.status_code == 200:
                data = res.json()
                st.session_state.uploaded_file_path = data["file_path"]
                st.session_state.active_modality = "audio"
                st.success(f"Attached audio: {aud_file.name}")
            else:
                st.error(res.json().get("detail", "Audio upload failed"))
        except Exception as e:
            st.error(f"Audio upload connection error: {e}")

# Chat input form
with st.form("chat_form", clear_on_submit=True):
    col_input, col_submit = st.columns([5, 1])
    user_input = col_input.text_input(
        "Your message:",
        placeholder="Type your message, ask a question, share how you're feeling, or ask about an uploaded file...",
        label_visibility="collapsed"
    )
    submitted = col_submit.form_submit_button("Send ➔", use_container_width=True)

if submitted and user_input.strip():
    # Append user message optimistically
    user_msg_entry = {
        "sender": "user",
        "message_content": user_input,
        "metadata_json": {}
    }
    st.session_state.messages.append(user_msg_entry)

    # Prepare chat request payload
    payload = {
        "conversation_id": st.session_state.conversation_id,
        "message": user_input,
        "modality": st.session_state.active_modality,
        "media_url": st.session_state.uploaded_file_path,
        "use_rag": use_rag_toggle,
        "generate_speech": generate_speech
    }

    with st.spinner("Aura is thinking..."):
        try:
            res = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=30)
            if res.status_code == 200:
                resp_data = res.json()
                st.session_state.conversation_id = resp_data["conversation_id"]

                # Append assistant reply
                assistant_msg_entry = {
                    "sender": "assistant",
                    "message_content": resp_data["reply"],
                    "metadata_json": {
                        "citations": [c for c in resp_data.get("citations", [])],
                        "audio_url": resp_data.get("audio_url"),
                        "safety": "crisis_intercepted" if resp_data.get("is_crisis") else None
                    }
                }
                st.session_state.messages.append(assistant_msg_entry)

                # Reset upload path after submission if image/audio was analyzed
                if st.session_state.active_modality in ("image", "audio"):
                    st.session_state.uploaded_file_path = None
                    st.session_state.active_modality = "text"

                st.rerun()
            else:
                err_detail = res.json().get("detail", res.text)
                st.error(f"Error from assistant server: {err_detail}")
        except Exception as e:
            st.error(f"Failed to connect to backend server: {str(e)}")
