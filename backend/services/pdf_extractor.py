"""
Extract text from uploaded PDF files (Information Memorandums).

Uses pypdfium2 (bundled with pdfplumber) as primary extractor,
falls back to pdfplumber if available.
"""

import io


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF file.

    Args:
        pdf_bytes: Raw PDF file bytes

    Returns:
        Combined text from all pages
    """
    # Try pypdfium2 first (lighter dependency, no cryptography needed)
    try:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(pdf_bytes)
        pages_text = []
        for i in range(len(pdf)):
            page = pdf[i]
            textpage = page.get_textpage()
            text = textpage.get_text_range()
            if text.strip():
                pages_text.append(text)
            textpage.close()
            page.close()
        pdf.close()
        return "\n\n".join(pages_text)
    except ImportError:
        pass

    # Fallback to pdfplumber
    try:
        import pdfplumber

        pages_text = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
        return "\n\n".join(pages_text)
    except ImportError:
        raise ImportError(
            "No PDF extraction library available. "
            "Install pypdfium2 or pdfplumber."
        )
