"""
main.py — Lecturotl entry point
Run: python main.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ui import app as app_module
from ui import reader as reader_module
from ui import chat as chat_module

if __name__ == "__main__":
    app_module.launch(reader_module, chat_module)