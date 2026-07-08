"""
ui/reader.py — Lecturotl reader panel
"""

import tkinter as tk
from tkinter import filedialog, ttk
from .app import (
    BG, PANEL, BORDER, TEXT_PRI, TEXT_SEC, ACCENT,
    FONT_LABEL, FONT_BTN, FONT_BODY, FONT_BODY_S, FONT_MONO,
    CapsuleButton,
)
from core import file_loader
from core.tts_engine import TTSEngine


class ReaderPanel:
    def __init__(self, parent, app):
        self._app    = app
        self._parent = parent
        self._tts    = TTSEngine()
        self._current_file = ""

        # State
        self._chunks          = []
        self._current_idx     = 0
        self._tts_active      = False
        self._resume_idx      = None
        self._read_all_active = False

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        self._build_toolbar(parent)
        self._build_text_area(parent)
        self._build_bottom_bar(parent)

    # ── Toolbar ───────────────────────────────────────────────────────────
    def _build_toolbar(self, parent):
        bar = tk.Frame(parent, bg=PANEL, pady=10, padx=12)
        bar.grid(row=0, column=0, sticky="ew")

        self._btn_open = CapsuleButton(
            bar, text="▸  open file",
            command=self._open_file, accent=True
        )
        self._btn_open.pack(side="left", padx=(0, 8))

        self._file_label = tk.Label(
            bar, text="no file loaded",
            font=FONT_MONO, fg=TEXT_SEC, bg=PANEL, anchor="w"
        )
        self._file_label.pack(side="left", fill="x", expand=True)

        self._chunk_counter = tk.Label(
            bar, text="—", font=FONT_MONO, fg=TEXT_SEC, bg=PANEL
        )
        self._chunk_counter.pack(side="right")

        tk.Frame(parent, bg=BORDER, height=1).grid(
            row=0, column=0, sticky="ew", pady=(44, 0)
        )

    # ── Scrollable text area ──────────────────────────────────────────────
    def _build_text_area(self, parent):
        container = tk.Frame(parent, bg=PANEL)
        container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self._text = tk.Text(
            container,
            font=FONT_BODY,
            fg=TEXT_PRI,
            bg=PANEL,
            insertbackground=ACCENT,
            selectbackground=ACCENT,
            selectforeground=BG,
            relief="flat",
            bd=0,
            wrap="word",
            padx=32,
            pady=24,
            spacing1=4,
            spacing3=6,
            state="disabled",
            cursor="arrow",
            highlightthickness=0,
        )
        self._text.grid(row=0, column=0, sticky="nsew")

        self._text.tag_configure("highlight", background="#1e2e1e", foreground=ACCENT)
        self._text.tag_configure("secondary", foreground=TEXT_SEC, font=FONT_BODY_S)
        self._text.tag_configure("heading", foreground=TEXT_PRI,
                                  font=("Nimbus Mono PS", 13, "bold"))

        sb = ttk.Scrollbar(container, orient="vertical",
                           command=self._text.yview,
                           style="Dark.Vertical.TScrollbar")
        sb.grid(row=0, column=1, sticky="ns")
        self._text.configure(yscrollcommand=sb.set)

    # ── Bottom bar ────────────────────────────────────────────────────────
    def _build_bottom_bar(self, parent):
        bar = tk.Frame(parent, bg=PANEL, padx=12, pady=10)
        bar.grid(row=2, column=0, sticky="ew")

        tk.Frame(parent, bg=BORDER, height=1).grid(row=2, column=0, sticky="ew")
        bar.grid(row=3, column=0, sticky="ew")

        self._btn_prev = CapsuleButton(
            bar, text="← prev", command=self._prev_chunk, small=True
        )
        self._btn_prev.pack(side="left", padx=(0, 6))

        self._tts_var = tk.StringVar(value="▶  read")
        self._btn_tts = CapsuleButton(
            bar, text=self._tts_var.get(),
            command=self._toggle_tts, accent=True
        )
        self._btn_tts.pack(side="left", padx=(0, 6))

        self._btn_next = CapsuleButton(
            bar, text="next →", command=self._next_chunk, small=True
        )
        self._btn_next.pack(side="left")

        # Read all (resumes from last position)
        self._btn_all = CapsuleButton(
            bar, text="read all", command=self._read_all, small=True
        )
        self._btn_all.pack(side="left", padx=(12, 0))

        # Restart from beginning
        self._btn_restart = CapsuleButton(
            bar, text="↺", command=self._read_all_from_start, small=True
        )
        self._btn_restart.pack(side="left", padx=(4, 0))

        self._progress_label = tk.Label(
            bar, text="chunk  —  /  —",
            font=FONT_MONO, fg=TEXT_SEC, bg=PANEL
        )
        self._progress_label.pack(side="right")

    # ── File loading ──────────────────────────────────────────────────────
    def _open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Text files",    "*.txt"),
                ("PDF files",     "*.pdf"),
                ("Markdown",      "*.md"),
                ("All files",     "*.*"),
            ]
        )
        if not path:
            return

        self._app.set_status("loading")
        short_name = path.split("/")[-1]
        self._file_label.configure(text=short_name)
        self.current_file = short_name

        try:
            text = file_loader.load_file(path)
        except Exception as e:
            self._show_error(f"Could not load file: {e}")
            self._app.set_status("error")
            return

        self._load_text(text)
        self._app.set_status("idle")

    def _load_text(self, raw_text: str):
        words = raw_text.split()
        chunk_size = 500
        self._chunks = [
            " ".join(words[i:i+chunk_size])
            for i in range(0, len(words), chunk_size)
        ]
        self._current_idx = 0
        self._render_chunk()

    def _render_chunk(self):
        if not self._chunks:
            return
        chunk = self._chunks[self._current_idx]
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("end", chunk)
        self._text.configure(state="disabled")
        self._text.yview_moveto(0)
        self._update_chunk_counter()
    
    def _push_reading_state(self):
        try:
            self._app.get_chat().update_reading_state(
                file=self._current_file or "unknown",
                chunk=self._current_idx + 1,
                total_chunks=len(self._chunks),
                page_text=self._chunks[self._current_idx],
            )
        except Exception:
            pass

    def _update_chunk_counter(self):
        total = len(self._chunks)
        cur   = self._current_idx + 1 if self._chunks else 0
        self._chunk_counter.configure(text=f"{cur} / {total}")
        self._progress_label.configure(text=f"chunk  {cur}  /  {total}")

    # ── Chunk navigation ──────────────────────────────────────────────────
    def _prev_chunk(self):
        if self._current_idx > 0:
            self._current_idx -= 1
            self._render_chunk()

    def _next_chunk(self):
        if self._current_idx < len(self._chunks) - 1:
            self._current_idx += 1
            self._render_chunk()

    # ── TTS controls ──────────────────────────────────────────────────────
    def _safe_callback(self, fn):
        """Wrap a callback so it always runs on tkinter's main thread."""
        return lambda *a, **kw: self._parent.after(0, lambda: fn(*a, **kw))

    def _toggle_tts(self):
        if self._tts_active:
            self._stop_tts()
        else:
            self._start_tts()

    def _start_tts(self):
        if not self._chunks:
            return
        self._tts_active = True
        self._btn_tts.configure(text="■  stop", bg=BORDER)
        self._app.set_status("reading")
        chunk = self._chunks[self._current_idx]

        try:
            self._tts.speak(chunk, on_done=self._safe_callback(self._tts_done))
        except Exception as e:
            self._show_error(f"TTS error: {e}")
            self._stop_tts()

    def _stop_tts(self):
        self._tts_active = False
        self._btn_tts.configure(text="▶  read", bg=ACCENT)
        self._app.set_status("idle")
        
        if self._read_all_active:
            self._resume_idx = self._current_idx + 1
        self._read_all_active = False
        
        try:
            self._tts.stop()
        except Exception:
            pass

    def _tts_done(self):
        """Called when a chunk finishes playing."""
        self._tts_active = False
        self._btn_tts.configure(text="▶  read", bg=ACCENT)
        self._app.set_status("idle")

    def _read_all(self, from_start=False):
        """Read from current chunk to end. Resumes if stopped mid-session."""
        if not self._chunks:
            return
        
        if from_start:
            start_idx = 0
            self._resume_idx = None
        else:
            start_idx = self._resume_idx if self._resume_idx is not None else self._current_idx
        
        self._tts_active = True
        self._read_all_active = True
        self._btn_tts.configure(text="■  stop", bg=BORDER)
        self._app.set_status("reading")
        self._read_all_from(start_idx)

    def _read_all_from_start(self):
        """Force 'read all' to start from chunk 0."""
        self._stop_tts()
        self._read_all(from_start=True)

    def _read_all_from(self, idx):
        if not self._tts_active or idx >= len(self._chunks):
            self._tts_done()
            self._resume_idx = None
            self._read_all_active = False
            return
        
        self._current_idx = idx
        self._render_chunk()
        chunk = self._chunks[idx]

        try:
            self._tts.speak(
                chunk,
                on_done=self._safe_callback(lambda: self._read_all_from(idx + 1))
            )
        except Exception as e:
            self._show_error(f"TTS error: {e}")
            self._stop_tts()

    # ── Helpers ───────────────────────────────────────────────────────────
    def _show_error(self, msg: str):
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("end", f"[error]\n{msg}", "secondary")
        self._text.configure(state="disabled")

    def highlight_sentence(self, sentence: str):
        self._text.configure(state="normal")
        self._text.tag_remove("highlight", "1.0", "end")
        start = "1.0"
        while True:
            pos = self._text.search(sentence[:40], start, stopindex="end")
            if not pos:
                break
            end = f"{pos}+{len(sentence)}c"
            self._text.tag_add("highlight", pos, end)
            start = end
        self._text.configure(state="disabled")

    def get_current_text(self) -> str:
        if not self._chunks:
            return ""
        return self._chunks[self._current_idx]
         
    

