"""
Summarise tool plugin.

``handle`` receives the Task ORM instance.  Read any parameters you need
from ``task.input_data`` (a JSON string) and return a plain dict.  The
dispatcher serialises the dict to JSON and stores it in ``task.output_data``.

Example input_data: '{"text": "Long article text goes here...", "max_words": 100}'
"""
import json


def handle(task) -> dict:
    """
    Stub: produce a short summary of a body of text.

    Replace the body with a real summarisation call (e.g. Claude API,
    OpenAI, sumy, or a local model).
    """
    params = {}
    if task.input_data:
        try:
            params = json.loads(task.input_data)
        except json.JSONDecodeError:
            pass

    source_text = params.get("text", "")
    max_words = params.get("max_words", 100)

    # --- replace below with real summarisation logic ---
    summary = ""
    word_count = 0
    # ---------------------------------------------------

    return {
        "tool": "summarise_tool",
        "max_words": max_words,
        "word_count": word_count,
        "summary": summary,
    }
