import os
import re
import pdfplumber

def load_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".txt":
        return _load_txt(filepath)
    elif ext == ".md":
        return _load_md(filepath)
    elif ext == ".pdf":
        return _load_pdf(filepath)
    else:
        raise ValueError(f"Unsupported format: {ext}")

def _load_pdf(filepath):
    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted.strip() + "\n\n"
    return text.strip()

def _load_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()

def _load_md(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    return _clean_md(text).strip()

def _clean_md(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    return text