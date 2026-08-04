import io
import json
import tarfile
import time
import threading
from pathlib import Path
from datetime import datetime

from PIL import Image

import mss
from pynput import mouse, keyboard


SCREENSHOT_WIDTH = 1024
SCREENSHOT_HEIGHT = 576


class Recorder:
    def __init__(self, data_dir: str = "data", tick_interval: float = 1.0):
        self.data_dir = Path(data_dir)
        self.tick_interval = tick_interval
        self._running = False
        self._session_dir: Path | None = None
        self._events_file: Path | None = None
        self._screenshots_tar: Path | None = None
        self._tar: tarfile.TarFile | None = None
        self._tick_thread: threading.Thread | None = None
        self._sct = mss.mss()
        self._lock = threading.Lock()
        self._events: list[dict] = []
        self._mouse_listener: mouse.Listener | None = None
        self._keyboard_listener: keyboard.Listener | None = None

    @property
    def session_dir(self) -> Path | None:
        return self._session_dir

    def start(self) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._session_dir = self.data_dir / "sessions" / f"session_{ts}"
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._events_file = self._session_dir / "events.jsonl"
        self._screenshots_tar = self._session_dir / "screenshots.tar"
        self._tar = tarfile.open(self._screenshots_tar, "a:")

        self._running = True

        self._mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
        )
        self._mouse_listener.start()

        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._keyboard_listener.start()

        self._tick_thread = threading.Thread(target=self._tick_loop, daemon=True)
        self._tick_thread.start()

        return self._session_dir

    def stop(self) -> None:
        self._running = False
        if self._tick_thread is not None:
            self._tick_thread.join()
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
        if self._tar is not None:
            self._tar.close()
            self._tar = None
        self._flush_events()
        self._sct.close()

    def _tick_loop(self) -> None:
        while self._running:
            self._tick()
            time.sleep(self.tick_interval)

    def _tick(self) -> None:
        ts = time.time()
        screenshot_path = self._capture_screenshot(ts)
        event = {
            "timestamp": ts,
            "event_type": "tick",
            "mouse": None,
            "keyboard": None,
            "screenshot_path": screenshot_path,
        }
        self._write_event(event)

    def _capture_screenshot(self, ts: float) -> str:
        monitor = self._sct.monitors[1]
        sct_img = self._sct.grab(monitor)
        filename = f"{int(ts * 1000)}.webp"
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        img = img.resize(
            (SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT), Image.Resampling.LANCZOS
        )
        buf = io.BytesIO()
        img.save(buf, format="WEBP",quality=75, method=6, )
        buf.seek(0)
        info = tarfile.TarInfo(f"screenshots/{filename}")
        info.size = buf.getbuffer().nbytes
        self._tar.addfile(info, buf)
        return f"screenshots/{filename}"

    def _on_mouse_move(self, x: int, y: int) -> None:
        event = {
            "timestamp": time.time(),
            "event_type": "mouse_move",
            "mouse": {"x": x, "y": y, "button": None, "pressed": False},
            "keyboard": None,
            "screenshot_path": None,
        }
        self._write_event(event)

    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        event = {
            "timestamp": time.time(),
            "event_type": "mouse_click",
            "mouse": {
                "x": x,
                "y": y,
                "button": button.name,
                "pressed": pressed,
            },
            "keyboard": None,
            "screenshot_path": None,
        }
        self._write_event(event)

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        event = {
            "timestamp": time.time(),
            "event_type": "key_press",
            "mouse": None,
            "keyboard": {"key": self._format_key(key)},
            "screenshot_path": None,
        }
        self._write_event(event)

    def _on_key_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        event = {
            "timestamp": time.time(),
            "event_type": "key_release",
            "mouse": None,
            "keyboard": {"key": self._format_key(key)},
            "screenshot_path": None,
        }
        self._write_event(event)

    @staticmethod
    def _format_key(key: keyboard.Key | keyboard.KeyCode | None) -> str | None:
        if key is None:
            return None
        if isinstance(key, keyboard.Key):
            return str(key)
        if isinstance(key, keyboard.KeyCode):
            return key.char if key.char else str(key)
        return str(key)

    def _write_event(self, event: dict) -> None:
        with self._lock:
            self._events.append(event)

    def _flush_events(self) -> None:
        if not self._events_file or not self._events:
            return
        with self._lock:
            events = self._events
            self._events = []
        with open(self._events_file, "a", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")
