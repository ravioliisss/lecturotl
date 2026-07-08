"""
core/ai_layer.py — Groq API wrapper
"""

import requests
import config

_SYSTEM_PROMPT = (
    "You are a study assistant embedded directly inside a lecture note reader. "
    "You always know what the student is currently reading — the file name, "
    "which chunk they are on, and the text on that page. "
    "Use this reading context naturally in your answers. "
    "If a question relates to the current page, answer from it. "
    "If it relates to something earlier or later, mention it briefly. "
    "If the question is unrelated to the document, just answer it normally "
    "as a helpful assistant would — don't mention the document at all. "
    "Keep explanations clear, concise, and academic. "
    "When summarizing, preserve key terms and definitions. "
    "Do not use markdown symbols like **, ##, or backticks. "
    "But do use clear structure in your responses — newlines between points, "
    "indentation for steps or formulas, and blank lines between sections. "
    "Write formulas on their own line with clear notation. "
    "For example: E = mc^2, or F = ma, each on a separate line."
    "Use short paragraphs with a blank line between them. "
    "Write one idea per paragraph, maximum 3 sentences. "
    "Put formulas on their own line. "
    "Do not use markdown symbols like **, ##, or backticks."
)


def ask_ai(prompt: str, reading_state: dict = None, history: list = None) -> str:
    """
    Args:
        prompt:        The user's question.
        reading_state: Dict with keys: file, chunk, total_chunks, page_text.
        history:       Prior {"role": ..., "content": ...} messages.
    """
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]

    if history:
        messages.extend(history)

    # Build context block from reading state
    if reading_state and reading_state.get("page_text"):
        pct  = int((reading_state["chunk"] / reading_state["total_chunks"]) * 100)
        ctx  = (
            f"[Reading state]\n"
            f"File: {reading_state['file']}\n"
            f"Position: chunk {reading_state['chunk']} of {reading_state['total_chunks']} ({pct}% through)\n\n"
            f"[Current page]\n"
            f"{reading_state['page_text'][:1500]}\n\n"
            f"[Student question]\n"
        )
        user_content = ctx + prompt
    else:
        user_content = prompt

    messages.append({"role": "user", "content": user_content})

    payload = {
        "model":       config.MODEL,
        "messages":    messages,
        "temperature": 0.4,
        "max_tokens":  1024,
    }
    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type":  "application/json",
    }

    try:
        response = requests.post(config.API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        return f"Connection error: {e}"
    except (KeyError, IndexError):
        return "Unexpected response from AI service."