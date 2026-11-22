import pytest
from pathlib import Path
from services.image_service import image_service
from services.audio_service import audio_service
from services.document_service import document_service

def test_image_format_validation(tmp_path):
    # 1. Non-existent file
    valid, msg = image_service.validate_image_file("non_existent.png")
    assert not valid

    # 2. Invalid extension
    fake_exe = tmp_path / "danger.exe"
    fake_exe.write_text("not an image")
    valid_ext, msg_ext = image_service.validate_image_file(str(fake_exe))
    assert not valid_ext
    assert "Unsupported image format" in msg_ext

def test_document_format_validation(tmp_path):
    # 1. TXT format allowed
    valid_txt = tmp_path / "notes.txt"
    valid_txt.write_text("These are sample notes for testing.", encoding="utf-8")
    valid, _ = document_service.validate_document_file(str(valid_txt))
    assert valid is True

    # 2. Extract text from TXT
    pages = document_service.extract_text(str(valid_txt))
    assert len(pages) == 1
    assert "sample notes" in pages[0]["text"]

    # 3. Invalid extension
    invalid_doc = tmp_path / "script.py"
    invalid_doc.write_text("print('hello')")
    valid_inv, msg_inv = document_service.validate_document_file(str(invalid_doc))
    assert valid_inv is False
    assert "Unsupported document format" in msg_inv

def test_audio_format_validation(tmp_path):
    fake_audio = tmp_path / "test.wav"
    fake_audio.write_bytes(b"RIFF....WAVEfmt ")
    valid, _ = audio_service.validate_audio_file(str(fake_audio))
    assert valid is True

    bad_audio = tmp_path / "track.flac"
    bad_audio.write_bytes(b"bad audio")
    valid_bad, msg = audio_service.validate_audio_file(str(bad_audio))
    assert valid_bad is False
    assert "Unsupported audio format" in msg

def test_pdf_document_extraction(tmp_path):
    try:
        import fitz
    except ImportError:
        import pymupdf as fitz

    # Create a small valid PDF in tmp_path
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello world from PyMuPDF document extraction test.")
    doc.save(str(pdf_path))
    doc.close()

    # Verify extraction
    valid, msg = document_service.validate_document_file(str(pdf_path))
    assert valid is True

    pages = document_service.extract_text(str(pdf_path))
    assert len(pages) == 1
    assert "PyMuPDF document extraction" in pages[0]["text"]
