"""
OCR tool plugin.

``handle`` receives the Task ORM instance.  Read any parameters you need
from ``task.input_data`` (a JSON string) and return a plain dict.  The
dispatcher serialises the dict to JSON and stores it in ``task.output_data``.

Example input_data: '{"file_url": "https://example.com/doc.pdf"}'
"""
import json


def handle(task) -> dict:
    """
    Stub: extract text from a document.

    Replace the body with a real OCR call (e.g. pytesseract, AWS Textract).
    """
    params = {}
    if task.input_data:
        try:
            params = json.loads(task.input_data)
        except json.JSONDecodeError:
            pass

    file_url = params.get("file_url", "")

    # --- replace below with real OCR logic ---
    extracted_text = ""
    page_count = 0
    # -----------------------------------------

    return {
        "tool": "ocr_tool",
        "file_url": file_url,
        "page_count": page_count,
        "text": extracted_text,
    }
