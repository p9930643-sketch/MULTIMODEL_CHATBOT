# Aura: Multimodal AI Companion

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg?style=flat&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1.svg?style=flat&logo=mysql&logoColor=white)](https://www.mysql.com/)

A modern, functional, modular, secure, and scalable **Multimodal AI Companion** powered by **FastAPI**, **Streamlit**, **MySQL**, **Google Gemini**, and a modular **Retrieval-Augmented Generation (RAG)** pipeline.

---

## 🌟 Key Features

1. **Natural Language Understanding & Empathetic Persona**:
   - Attuned, active listening persona ("Aura") providing gentle emotional validation, non-judgmental support, and healthy coping mechanisms (box breathing, grounding exercises).
   - Medical disclaimer protocols ensuring the AI never provides psychiatric diagnoses or presents itself as a licensed doctor/therapist.
2. **Emergency Crisis Intervention**:
   - Real-time pre-inference regex and semantic scanning for self-harm, suicide, or severe crisis intent.
   - Immediate bypass to safe crisis resources (988 Lifeline, Crisis Text Line 741741, International helplines).
3. **Multimodal Input & Processing**:
   - **Image Understanding**: Upload and ask questions about JPG, JPEG, and PNG images with vision analysis.
   - **Document Intelligence (RAG)**: Extract, clean, and chunk PDF and TXT documents with page-level attribution using PyMuPDF (`fitz`).
   - **Speech-to-Text (STT)**: Transcribe uploaded audio files (WAV, MP3, M4A, OGG).
4. **Modular RAG Pipeline**:
   - Recursive character chunking with configurable window overlap.
   - 768-dimensional semantic embeddings via Gemini `text-embedding-004` (with deterministic fallback).
   - Hybrid semantic + lexical retrieval with source citation cards.
   - Untrusted prompt boundaries protecting against document-embedded prompt injection.
5. **Multimodal Output**:
   - Rich interactive Streamlit UI with conversation memory.
   - Audio text-to-speech (TTS) synthesis and playback.
6. **Robust Database Layer**:
   - Normalized MySQL 8.0 schema (`conversations`, `messages`, `documents`, `document_chunks`, `knowledge_sources`) with foreign keys and FULLTEXT indexing.
   - Automatic connection pooling and SQLite development fallback when MySQL is temporarily offline.

---

## 📂 Project Architecture & Directory Layout

```
multimodal_ai_companion/
│
├── app.py                      # Streamlit frontend user interface
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment configuration
├── .env                        # Local secrets (strictly excluded from git)
├── .gitignore                  # Git ignore rules
├── README.md                   # System documentation
│
├── backend/
│   ├── main.py                 # FastAPI application, CORS, lifespan & healthcheck
│   ├── database.py             # SQLAlchemy session management & connection verification
│   ├── models.py               # Declarative ORM models (5 tables)
│   ├── schemas.py              # Pydantic v2 validation models
│   └── routes/
│       ├── chat.py             # Chat endpoint with multimodal pipeline
│       ├── upload.py           # Validated upload endpoints (image, doc, audio)
│       ├── documents.py        # RAG ingestion, listing, and deletion
│       └── speech.py           # Text-to-speech audio streaming
│
├── core/
│   ├── config.py               # Application settings loaded via Pydantic
│   ├── ai_engine.py            # Gemini API client wrapper with system instructions
│   ├── multimodal_engine.py    # Modality dispatcher & pipeline coordinator
│   ├── rag_engine.py           # Chunking, indexing, retrieval, and grounded synthesis
│   ├── embeddings.py           # 768-dim embeddings generator with fallback
│   ├── safety_guardrails.py    # Crisis filter, injection sanitizer, medical disclaimer
│   └── prompt_templates.py     # Empathetic system prompts & RAG delimiters
│
├── services/
│   ├── image_service.py        # Image validation (PIL) and vision prompts
│   ├── audio_service.py        # Audio transcription & TTS generation (gTTS)
│   ├── document_service.py     # PyMuPDF PDF parsing and recursive chunking
│   └── conversation_service.py # Session lifecycle and chronological history
│
├── database/
│   └── schema.sql              # Raw SQL DDL with MySQL 8.0 FULLTEXT indexes
│
├── tests/
│   ├── conftest.py             # Test fixtures & in-memory test database
│   ├── test_api.py             # FastAPI integration tests
│   ├── test_rag.py             # Chunking, embeddings & retrieval tests
│   ├── test_security.py        # Crisis detection, injection & file sanitizer tests
│   └── test_multimodal.py      # Format validation tests for image, doc, audio
│
└── uploads/                    # Local temporary storage for media & documents
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- MySQL Server 8.0+ (Optional for testing; SQLite fallback is supported automatically)
- A Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### 2. Environment Setup

Clone or enter the project directory and create a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure `.env`

Copy `.env.example` to `.env`:

```powershell
copy .env.example .env
```

Edit `.env` with your preferred credentials:

```ini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# MySQL Database Configuration
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=multimodal_companion
ALLOW_SQLITE_FALLBACK=True
```

### 4. Initialize MySQL Database

If running MySQL locally, create the database and tables using the provided schema:

```powershell
mysql -u root -p < database/schema.sql
```

*(Note: If MySQL is not running, the application seamlessly uses SQLite `multimodal_companion_dev.db` for development and automated testing).*

---

## 🖥️ Running the Application

### 1. Start the FastAPI Backend

```powershell
.\venv\Scripts\uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 2. Start the Streamlit Frontend

Open a second terminal window:

```powershell
.\venv\Scripts\streamlit run app.py
```
- Web Application: [http://localhost:8501](http://localhost:8501)

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:

```powershell
.\venv\Scripts\pytest -v
```

The test suite covers:
- Endpoint health and chat requests
- Empty/invalid payload rejection
- Conversation lifecycle (create, fetch, delete)
- Speech synthesis generation
- Document chunking and semantic similarity
- Crisis detection and hotline intervention
- Prompt injection indicators
- Path traversal and malicious file sanitization
- Multi-format validation for images, audio, and documents

---

## 🛡️ Security & Ethical Guardrails

- **Prompt Injection Defense**: Uploaded documents are tagged as untrusted input and wrapped in rigid boundary delimiters `<<<UNTRUSTED_DOCUMENT_CHUNK>>>`. System instructions explicitly direct the model to disregard instructions embedded inside external files.
- **Safety Interceptions**: Crisis terms (e.g. self-harm, suicide) automatically trigger an immediate, compassionate response with 24/7 hotline numbers (988), bypassing LLM generation.
- **Input Sanitization**: File uploads are restricted by size (10MB limit), verified by MIME types and file signatures, and filenames are sanitized against path traversal (`../`).
- **No Hardcoded Secrets**: Secrets are loaded strictly through Pydantic settings from environment variables.
- **MVP Scope**: This application is intended for controlled local development and demonstration. Authentication is intentionally omitted from this MVP.
