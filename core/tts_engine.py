import asyncio
import subprocess
import threading
import shutil
import os
import config


class TTSEngine:
    def __init__(self):
        self._piper_proc = None
        self._player_proc = None
        self._thread = None
        self._stop_flag = False

    def _validate(self):
        """Check that required binaries exist BEFORE starting TTS."""
        piper_path = os.path.expanduser(config.PIPER_BINARY)
        aplay_path = shutil.which("aplay") or "/usr/bin/aplay"

        if not os.path.exists(piper_path):
            raise FileNotFoundError(
                f"Piper not found: {piper_path}\n"
                f"Install: sudo apt install piper-tts\n"
                f"Or fix PIPER_BINARY in .env"
            )
        if not os.path.exists(config.VOICE_MODEL):
            raise FileNotFoundError(
                f"Voice model not found: {config.VOICE_MODEL}\n"
                f"Download from: https://github.com/rhasspy/piper/releases"
            )
        if not shutil.which("aplay") and not os.path.exists("/usr/bin/aplay"):
            raise FileNotFoundError(
                f"aplay not found. Install: sudo apt install alsa-utils"
            )

    def speak(self, text, on_done=None):
        """Sync entry point. Validates first, then starts thread."""
        self._validate()  # ← runs on main thread, shows error in UI
        self._start_thread(text, on_done)

    def stop(self):
        self._stop_flag = True
        for proc in (self._piper_proc, self._player_proc):
            if proc:
                try:
                    proc.terminate()
                except Exception:
                    pass
        self._piper_proc = None
        self._player_proc = None

    def is_speaking(self):
        return self._thread is not None and self._thread.is_alive()

    def _start_thread(self, text, on_done):
        self.stop()
        self._stop_flag = False
        self._thread = threading.Thread(
            target=self._run, args=(text, on_done), daemon=True
        )
        self._thread.start()

    def _chunk_text(self, text, max_chars=500):
        sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
        chunks, current = [], ""
        for s in sentences:
            piece = s if s.endswith((".", "!", "?")) else s + "."
            if len(current) + len(piece) + 1 <= max_chars:
                current += (" " if current else "") + piece
            else:
                if current:
                    chunks.append(current)
                current = piece
        if current:
            chunks.append(current)
        return chunks

    def _run(self, text, on_done):
        try:
            piper_path = os.path.expanduser(config.PIPER_BINARY)
            aplay_path = shutil.which("aplay") or "/usr/bin/aplay"

            self._piper_proc = subprocess.Popen(
                [piper_path, "--model", config.VOICE_MODEL, "--output-raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self._player_proc = subprocess.Popen(
                [aplay_path, "-q", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
                stdin=self._piper_proc.stdout,
                stderr=subprocess.DEVNULL,
            )
            self._piper_proc.stdout.close()

            for chunk in self._chunk_text(text):
                if self._stop_flag:
                    break
                self._piper_proc.stdin.write((chunk + "\n").encode("utf-8"))
                self._piper_proc.stdin.flush()

            self._piper_proc.stdin.close()

            if self._stop_flag:
                return

            self._player_proc.wait()
        except Exception as e:
            print(f"TTS error: {e}")
        finally:
            if on_done and not self._stop_flag:
                on_done()
