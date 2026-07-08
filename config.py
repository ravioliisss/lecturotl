"""
config.py — Lecturotl configuration
Copy .env.example to .env and fill in your values.
"""

import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ── Paths ─────────────────────────────────────────────────────────────────────
PIPER_BINARY = os.getenv("PIPER_BINARY", "piper")
VOICE_MODEL  = os.getenv("VOICE_MODEL", os.path.join(BASE_DIR, "voices", "en_US-kristin-medium.onnx"))

# ── API ───────────────────────────────────────────────────────────────────────
API_KEY = os.getenv("API_KEY")
MODEL   = os.getenv("MODEL", "llama-3.3-70b-versatile")
API_URL = os.getenv("API_URL", "https://api.groq.com/openai/v1/chat/completions")

# ── Window ────────────────────────────────────────────────────────────────────
WINDOW_TITLE = "Lecturotl"
WINDOW_SIZE  = "1280x600"
MIN_SIZE     = (900, 600)

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_BODY    = ("Comfortaa", 13)
FONT_HEADING = ("Comfortaa", 15, "bold")
FONT_UI      = ("Nimbus Mono PS", 11, "bold")
FONT_SMALL   = ("Nimbus Mono PS", 9, "bold")