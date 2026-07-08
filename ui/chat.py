"""
ui/chat.py — Lecturotl AI chat panel
"""

import tkinter as tk
from tkinter import ttk
import threading
from .app import (
    BG, PANEL, BORDER, TEXT_PRI, TEXT_SEC, ACCENT,
    FONT_LABEL, FONT_BTN, FONT_BODY, FONT_BODY_S, FONT_MONO,
    CapsuleButton,
)
from core import ai_layer


BUBBLE_USER = "#333333"
BUBBLE_AI   = "#282828"
INPUT_BG    = "#111111"


class ChatPanel:
    def __init__(self, parent, app):
        self._app          = app
        self._parent       = parent
        self._history      = []
        self._thinking     = False
        self._reading_state = {}   # pushed by ReaderPanel on every chunk change

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        self._build_header(parent)
        self._build_message_area(parent)
        self._build_input_bar(parent)

    # ── Reading state (called by ReaderPanel) ─────────────────────────────
    def update_reading_state(self, file: str, chunk: int, total_chunks: int, page_text: str):
        """ReaderPanel calls this every time the displayed chunk changes."""
        self._reading_state = {
            "file":         file,
            "chunk":        chunk,
            "total_chunks": total_chunks,
            "page_text":    page_text,
        }
        self._update_position_label()

    def _update_position_label(self):
        if not self._reading_state:
            return
        s = self._reading_state
        pct = int((s["chunk"] / s["total_chunks"]) * 100)
        self._position_lbl.configure(
            text=f"{s['file']}  ·  {s['chunk']}/{s['total_chunks']}  ({pct}%)"
        )

    # ── Header ────────────────────────────────────────────────────────────
    def _build_header(self, parent):
        hdr = tk.Frame(parent, bg=PANEL, pady=10, padx=12)
        hdr.grid(row=0, column=0, sticky="ew")

        tk.Label(hdr, text="AI CHAT", font=FONT_LABEL,
                 fg=ACCENT, bg=PANEL).pack(side="left")

        self._btn_clear = CapsuleButton(
            hdr, text="clear", command=self._clear_chat, small=True
        )
        self._btn_clear.pack(side="right")

        tk.Frame(parent, bg=BORDER, height=1).grid(
            row=0, column=0, sticky="ew", pady=(40, 0)
        )

        # Position label — shows current file + chunk below the header border
        self._position_lbl = tk.Label(
            parent, text="no file loaded",
            font=FONT_MONO, fg=TEXT_SEC, bg=PANEL,
            anchor="w", padx=12, pady=4,
        )
        self._position_lbl.grid(row=0, column=0, sticky="ew", pady=(48, 0))

    # ── Scrollable message area ───────────────────────────────────────────
    def _build_message_area(self, parent):
        container = tk.Frame(parent, bg=PANEL)
        container.grid(row=1, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(
            container, bg=PANEL, highlightthickness=0, bd=0
        )
        self._canvas.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(container, orient="vertical",
                           command=self._canvas.yview,
                           style="Dark.Vertical.TScrollbar")
        sb.grid(row=0, column=1, sticky="ns")
        self._canvas.configure(yscrollcommand=sb.set)

        self._msg_frame = tk.Frame(self._canvas, bg=PANEL)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._msg_frame, anchor="nw"
        )

        self._msg_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>",    self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>",   self._on_mousewheel)
        self._canvas.bind_all("<Button-5>",   self._on_mousewheel)

        self._add_system_msg("Ask anything about your lecture.")

    def _on_frame_configure(self, _event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Input bar ─────────────────────────────────────────────────────────
    def _build_input_bar(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).grid(row=2, column=0, sticky="ew")

        bar = tk.Frame(parent, bg=PANEL, padx=10, pady=10)
        bar.grid(row=3, column=0, sticky="ew")
        bar.columnconfigure(0, weight=1)

        self._input = tk.Text(
            bar,
            font=FONT_BODY_S,
            fg=TEXT_PRI, bg=INPUT_BG,
            insertbackground=ACCENT,
            relief="flat", bd=0,
            height=2, wrap="word",
            padx=10, pady=8,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )
        self._input.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._input.bind("<Return>",       self._on_enter)
        self._input.bind("<Shift-Return>", self._on_shift_enter)

        self._btn_send = CapsuleButton(
            bar, text="send", command=self._send_message, accent=True
        )
        self._btn_send.grid(row=0, column=1)

    # ── Message rendering ─────────────────────────────────────────────────
    def _add_message(self, role: str, text: str):
                    is_user = (role == "user")
                    outer = tk.Frame(self._msg_frame, bg=PANEL)
                    outer.pack(fill="x", padx=10, pady=(4, 2))

                    tk.Label(
                        outer,
                        text="you" if is_user else "ai",
                        font=FONT_MONO,
                        fg=ACCENT if is_user else TEXT_SEC,
                        bg=PANEL,
                        anchor="e" if is_user else "w",
                    ).pack(fill="x", padx=4)

                    bubble = tk.Frame(
                        outer,
                        bg=BUBBLE_USER if is_user else BUBBLE_AI,
                        padx=12, pady=8,
                    )
                    bubble.pack(anchor="e" if is_user else "w",
                                padx=(60, 0) if is_user else (0, 60))

                    tk.Label(
                        bubble,
                        text=text,
                        font=FONT_BODY_S,
                        fg=TEXT_PRI,
                        bg=BUBBLE_USER if is_user else BUBBLE_AI,
                        wraplength=380,
                        justify="left",
                        anchor="w",
                    ).pack(fill="x")

                    self._scroll_to_bottom()

    def _add_system_msg(self, text: str):
        tk.Label(
            self._msg_frame,
            text=text,
            font=FONT_MONO,
            fg=TEXT_SEC,
            bg=PANEL,
            justify="center",
            wraplength=260,
        ).pack(pady=(12, 4))

    def _add_thinking_indicator(self):
        self._thinking_frame = tk.Frame(self._msg_frame, bg=PANEL)
        self._thinking_frame.pack(anchor="w", padx=10, pady=4)
        self._thinking_lbl = tk.Label(
            self._thinking_frame, text="·",
            font=("Nimbus Mono PS", 14, "bold"),
            fg=ACCENT, bg=PANEL,
        )
        self._thinking_lbl.pack(side="left")
        self._scroll_to_bottom()
        self._animate_thinking(0)

    def _animate_thinking(self, tick):
        if not self._thinking:
            return
        self._thinking_lbl.configure(text=["·", "· ·", "· · ·"][tick % 3])
        self._msg_frame.after(400, lambda: self._animate_thinking(tick + 1))

    def _remove_thinking_indicator(self):
        if hasattr(self, "_thinking_frame"):
            self._thinking_frame.destroy()

    def _scroll_to_bottom(self):
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(1.0)

    # ── Sending messages ──────────────────────────────────────────────────
    def _on_enter(self, event):
        self._send_message()
        return "break"

    def _on_shift_enter(self, event):
        return None

    def _send_message(self):
        if self._thinking:
            return
        raw = self._input.get("1.0", "end").strip()
        if not raw:
            return

        self._input.delete("1.0", "end")
        self._add_message("user", raw)
        self._history.append({"role": "user", "content": raw})

        if len(self._history) > 20:
            self._history = self._history[-20:]

        self._thinking = True
        self._app.set_status("thinking")
        self._add_thinking_indicator()

        threading.Thread(
            target=self._call_ai,
            args=(raw,),
            daemon=True,
        ).start()

    def _call_ai(self, prompt: str):
        try:
            reply = ai_layer.ask_ai(
                prompt,
                reading_state=self._reading_state or None,
                history=self._history[:-1],
            )
        except Exception as e:
            reply = f"[error] {e}"

        self._msg_frame.after(0, lambda: self._on_ai_reply(reply))

    def _on_ai_reply(self, reply: str):
        self._thinking = False
        self._remove_thinking_indicator()
        self._app.set_status("idle")
        self._add_message("assistant", reply)
        self._history.append({"role": "assistant", "content": reply})

    # ── Clear ─────────────────────────────────────────────────────────────
    def _clear_chat(self):
        for widget in self._msg_frame.winfo_children():
            widget.destroy()
        self._history.clear()
        self._add_system_msg("Chat cleared. Ask anything about your lecture.")