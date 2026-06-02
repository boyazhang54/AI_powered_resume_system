from fastapi import HTTPException


def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="PyMuPDF is not installed.") from exc

    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as document:
            pages = []
            for page_index, page in enumerate(document, start=1):
                text = page.get_text("text")
                if text.strip():
                    pages.append(f"--- Page {page_index} ---\n{text}")
            return "\n\n".join(pages).strip()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {exc}") from exc
