from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database_dialect" in data

def test_chat_text_message(client: TestClient):
    payload = {
        "message": "Hello, how are you today?",
        "modality": "text",
        "use_rag": False,
        "generate_speech": False
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "conversation_id" in data
    assert data["modality"] in ("text", "multimodal")
    assert not data["is_crisis"]

def test_chat_empty_input_rejected(client: TestClient):
    payload = {
        "message": "",
        "modality": "text"
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 422  # Pydantic validation error

def test_conversation_lifecycle(client: TestClient):
    # 1. Send first message to initialize conversation
    res = client.post("/chat", json={"message": "First test message", "modality": "text"})
    assert res.status_code == 200
    conv_id = res.json()["conversation_id"]

    # 2. Get list of conversations
    res_list = client.get("/conversations")
    assert res_list.status_code == 200
    conv_ids = [c["conversation_id"] for c in res_list.json()]
    assert conv_id in conv_ids

    # 3. Get messages for the conversation
    res_msgs = client.get(f"/conversations/{conv_id}/messages")
    assert res_msgs.status_code == 200
    msgs = res_msgs.json()
    assert len(msgs) >= 2  # user + assistant

    # 4. Delete the conversation
    del_res = client.delete(f"/conversations/{conv_id}")
    assert del_res.status_code == 200

    # 5. Verify conversation is gone
    res_msgs_after = client.get(f"/conversations/{conv_id}/messages")
    assert len(res_msgs_after.json()) == 0

def test_speech_generation(client: TestClient):
    payload = {
        "text": "Hello, this is a test audio generation.",
        "language": "en"
    }
    response = client.post("/speech/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "audio_url" in data
    assert data["audio_url"].startswith("/speech/file/")

def test_image_upload_endpoint(client: TestClient):
    import io
    from PIL import Image

    buf = io.BytesIO()
    img = Image.new("RGB", (20, 20), color="green")
    img.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("test_avatar.png", buf.getvalue(), "image/png")}
    response = client.post("/upload/image", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == "image"
    assert "test_avatar.png" in data["filename"]

def test_document_upload_and_listing(client: TestClient):
    content = b"This is a test document uploaded via API for RAG."
    files = {"file": ("test_handbook.txt", content, "text/plain")}
    response = client.post("/upload/document", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == "document"
    doc_id = data["document_id"]
    assert doc_id is not None

    # List documents
    list_res = client.get("/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert any(d["document_id"] == doc_id for d in docs)

    # Delete document
    del_res = client.delete(f"/documents/{doc_id}")
    assert del_res.status_code == 200

def test_audio_upload_endpoint(client: TestClient):
    audio_content = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00"
    files = {"file": ("sample.wav", audio_content, "audio/wav")}
    response = client.post("/upload/audio", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == "audio"

def test_unsupported_file_upload_rejected(client: TestClient):
    files = {"file": ("malicious.exe", b"fake binary executable", "application/octet-stream")}
    response = client.post("/upload/image", files=files)
    assert response.status_code == 400

def test_oversized_file_upload_rejected(client: TestClient):
    # Default limit is 10MB -> 10 * 1024 * 1024 + 1
    oversized = b"0" * (10 * 1024 * 1024 + 10)
    files = {"file": ("large_image.png", oversized, "image/png")}
    response = client.post("/upload/image", files=files)
    assert response.status_code == 413
