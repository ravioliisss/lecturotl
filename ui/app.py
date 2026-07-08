"""
ui/app.py — Lecturotl main window
"""

import tkinter as tk
from tkinter import ttk
import sys

BG = "#0a0a0a"
PANEL = "#141414"
BORDER = "#1e1e1e"
TEXT_PRI = "#ffffff"
TEXT_SEC = "#888888"
ACCENT = "#c8d9c4"

FONT_LABEL = ("Nimbus Mono PS", 10, "bold")
FONT_BTN = ("Nimbus Mono PS", 9, "bold")
FONT_BODY = ("Comfortaa", 11)
FONT_BODY_S = ("Comfortaa", 10)
FONT_MONO = ("Nimbus Mono PS", 9)


def _apply_global_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Dark.Vertical.TScrollbar",
        gripcount=0, background=BORDER, darkcolor=BORDER,
        lightcolor=BORDER, troughcolor=BG, bordercolor=BG,
        arrowcolor=TEXT_SEC, relief="flat", width=6)
    style.map("Dark.Vertical.TScrollbar", background=[("active", BORDER)])
    style.configure("Dark.TSeparator", background=BORDER)


class LecturotlApp(tk.Tk):
    def __init__(self, reader_module, chat_module):
        super().__init__()
        self.title("Lecturotl")
        self.configure(bg=BG)
        self.geometry("1280x800")
        self.minsize(900, 600)

        _apply_global_style()

        # Top bar
        self._build_topbar()

        # Main paned area (65/35)
        self._pane = tk.Frame(self, bg=BG)
        self._pane.place(x=0, y=48, relwidth=1, relheight=1, height=-48)

        self._pane.columnconfigure(0, weight=65)
        self._pane.columnconfigure(1, weight=0)
        self._pane.columnconfigure(2, weight=35)
        self._pane.rowconfigure(0, weight=1)

        # Reader panel (65%)
        self._reader_frame = tk.Frame(self._pane, bg=PANEL,
                                      highlightbackground=BORDER, highlightthickness=1)
        self._reader_frame.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=12)

        # Divider
        tk.Frame(self._pane, bg=BORDER, width=1).grid(row=0, column=1, sticky="ns", pady=12)

        # Chat panel (35%)
        self._chat_frame = tk.Frame(self._pane, bg=PANEL,
                                    highlightbackground=BORDER, highlightthickness=1)
        self._chat_frame.grid(row=0, column=2, sticky="nsew", padx=(0, 12), pady=12)

        # Inject modules
        self._reader = reader_module.ReaderPanel(self._reader_frame, app=self)
        self._chat = chat_module.ChatPanel(self._chat_frame, app=self)

        # Close handler
        self.protocol("WM_DELETE_WINDOW", self._handle_close)

    def _handle_close(self):
        try:
            self._reader._tts.stop()
        except Exception:
            pass
        self.quit()
        self.destroy()
        sys.exit(0)

    def _build_topbar(self):
        bar = tk.Frame(self, bg=BG, height=48)
        bar.place(x=0, y=0, relwidth=1)
        bar.pack_propagate(False)

        tk.Label(bar, text="LECTUROTL", font=("Nimbus Mono PS", 12, "bold"),
                 fg=ACCENT, bg=BG).pack(side="left", padx=20, pady=12)

        self.status_var = tk.StringVar(value="idle")
        self._status_pill = StatusPill(bar, textvariable=self.status_var)
        self._status_pill.pack(side="right", padx=20, pady=12)

        tk.Frame(self, bg=BORDER, height=1).place(x=0, y=47, relwidth=1)

    def set_status(self, text: str):
        self.status_var.set(text)

    def get_reader(self):
        return self._reader

    def get_chat(self):
        return self._chat


class StatusPill(tk.Label):
    STATE_COLORS = {
        "idle": TEXT_SEC,
        "reading": ACCENT,
        "thinking": "#c8b4a0",
        "error": "#c87a7a",
    }

    def __init__(self, parent, textvariable, **kw):
        super().__init__(parent, textvariable=textvariable, font=FONT_MONO,
                         fg=BG, bg=TEXT_SEC, padx=10, pady=3, relief="flat", **kw)
        textvariable.trace_add("write", self._update_color)

    def _update_color(self, *_):
        state = self.cget("text")
        col = self.STATE_COLORS.get(state, TEXT_SEC)
        self.configure(bg=col, fg=BG if col != TEXT_SEC else BG)


def CapsuleButton(parent, text, command, accent=False, small=False, **kw):
    pad_x = 14 if not small else 10
    pad_y = 6 if not small else 4
    font = FONT_BTN

    if accent:
        btn = tk.Button(parent, text=text, command=command, font=font,
                        fg=BG, bg=ACCENT, activebackground="#b0c4b0",
                        activeforeground=BG, relief="flat", bd=0,
                        padx=pad_x, pady=pad_y, cursor="hand2", **kw)
    else:
        btn = tk.Button(parent, text=text, command=command, font=font,
                        fg=TEXT_PRI, bg=BORDER, activebackground="#2a2a2a",
                        activeforeground=TEXT_PRI, relief="flat", bd=0,
                        padx=pad_x, pady=pad_y, cursor="hand2", **kw)
    return btn


def launch(reader_module, chat_module):
    app = LecturotlApp(reader_module, chat_module)
    app.mainloop()