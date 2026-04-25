"""
document_parser.py
Handles parsing of PDF, DOCX, and TXT files.
Returns clean extracted text from each document.
"""

import os
from pathlib import Path


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
    except Exception as e:
        raise ValueError(f"Failed to parse PDF '{file_path}': {e}")


def parse_docx(file_path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs).strip()
    except ImportError:
        raise ImportError("python-docx not installed. Run: pip install python-docx")
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX '{file_path}': {e}")


def parse_txt(file_path: str) -> str:
    """Extract text from a plain TXT file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception as e:
        raise ValueError(f"Failed to parse TXT '{file_path}': {e}")


def parse_document(file_path: str) -> dict:
    """
    Auto-detect file type and parse accordingly.
    Returns a dict with 'filename', 'text', 'word_count'.
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    filename = path.name

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if ext == ".pdf":
        text = parse_pdf(file_path)
    elif ext in (".docx", ".doc"):
        text = parse_docx(file_path)
    elif ext == ".txt":
        text = parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: '{ext}'. Supported: PDF, DOCX, TXT")

    word_count = len(text.split())

    if word_count < 50:
        raise ValueError(
            f"Document '{filename}' is too thin ({word_count} words). "
            "Please upload a more detailed document."
        )

    return {
        "filename": filename,
        "text": text,
        "word_count": word_count,
    }


def parse_multiple_documents(file_paths: list) -> dict:
    """
    Parse multiple documents and combine results.
    Returns:
        {
            "documents": [{"filename": ..., "text": ..., "word_count": ...}],
            "combined_text": "...",
            "total_words": int,
            "errors": ["filename: error message", ...]
        }
    """
    documents = []
    errors = []

    for fp in file_paths:
        try:
            doc = parse_document(fp)
            documents.append(doc)
        except Exception as e:
            errors.append(f"{Path(fp).name}: {str(e)}")

    if not documents and errors:
        raise ValueError(
            "No documents could be parsed successfully.\n" + "\n".join(errors)
        )

    combined_text = "\n\n---\n\n".join(
        [f"[From: {d['filename']}]\n{d['text']}" for d in documents]
    )
    total_words = sum(d["word_count"] for d in documents)

    return {
        "documents": documents,
        "combined_text": combined_text,
        "total_words": total_words,
        "errors": errors,
    }


def save_uploaded_file(uploaded_file, save_dir: str = "/tmp/podcast_uploads") -> str:
    """
    Save a Streamlit UploadedFile to disk and return the saved path.
    Creates the directory if it doesn't exist.
    """
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return save_path
