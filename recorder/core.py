import io
import json
import time
import threading
from pathlib import Path
from datetime import datetime

import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image

import mss
from pynput import mouse, keyboard


SCREENSHOT_WIDTH = 1024
SCREENSHOT_HEIGHT = 576
CHUNK_SIZE = 1000


class Recorder:
    def __init__(self, data_dir: str = "data", tick_interval: float = 1.0):
        self.data_dir = Path(data_dir)
        self.tick_interval = tick_interval
        self._running = False
        self._sct = mss.MSS()
        self._lock = threading.Lock()
        self._events: list[dict] = []
        self._mouse_listener: mouse.Listener | None = None
        self._keyboard_listener: keyboard.Listener | None = None
        self._tick_thread: threading.Thread | None = None
        self._mouse_x: int = 0
        self._mouse_y: int = 0
        self._prev_mouse_x: int | None = None
        self._prev_mouse_y: int | None = None
        self._mouse_left: bool = False
        self._mouse_right: bool = False
        self._keys: dict[str, bool] = {}

    def start(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._write_screen_json()
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

        return self.data_dir

    def stop(self) -> None:
        self._running = False
        if self._tick_thread is not None:
            self._tick_thread.join()
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
        self._flush_events(final=True)
        self._sct.close()

    def _tick_loop(self) -> None:
        while self._running:
            self._tick()
            time.sleep(self.tick_interval)

    def _tick(self) -> None:
        ts = time.time()
        img_bytes = self._capture_screenshot()
        if self._prev_mouse_x is None or self._prev_mouse_y is None:
            dx = 0
            dy = 0
        else:
            dx = self._mouse_x - self._prev_mouse_x
            dy = self._mouse_y - self._prev_mouse_y
        self._prev_mouse_x = self._mouse_x
        self._prev_mouse_y = self._mouse_y
        event = {
            "image": img_bytes,
            "timestamp": ts,
            "mouse_x": self._mouse_x,
            "mouse_y": self._mouse_y,
            "mouse_dx": dx,
            "mouse_dy": dy,
            "mouse_left": self._mouse_left,
            "mouse_right": self._mouse_right,
            "key_w": self._keys.get("w", False),
            "key_a": self._keys.get("a", False),
            "key_s": self._keys.get("s", False),
            "key_d": self._keys.get("d", False),
            "key_space": self._keys.get("Key.space", False),
            "key_shift": self._keys.get("Key.shift", False),
            "key_ctrl": self._keys.get("Key.ctrl", False),
        }
        with self._lock:
            self._events.append(event)
        if len(self._events) >= CHUNK_SIZE:
            self._flush_events()

    def _capture_screenshot(self) -> bytes:
        monitor = self._sct.monitors[1]
        sct_img = self._sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        img = img.resize(
            (SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT), Image.Resampling.LANCZOS
        )
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=85)
        return buf.getvalue()

    def _write_screen_json(self) -> None:
        monitor = self._sct.monitors[1]
        payload = {
            "width": monitor["width"],
            "height": monitor["height"],
        }
        with open(self.data_dir / "screen.json", "w", encoding="utf-8") as f:
            json.dump(payload, f)

    def _on_mouse_move(self, x: int, y: int) -> None:
        self._mouse_x = x
        self._mouse_y = y

    def _on_mouse_click(
        self, x: int, y: int, button: mouse.Button, pressed: bool
    ) -> None:
        self._mouse_x = x
        self._mouse_y = y
        if button == mouse.Button.left:
            self._mouse_left = pressed
        elif button == mouse.Button.right:
            self._mouse_right = pressed

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        name = self._key_name(key)
        if name:
            self._keys[name] = True

    def _on_key_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        name = self._key_name(key)
        if name:
            self._keys[name] = False

    @staticmethod
    def _key_name(key: keyboard.Key | keyboard.KeyCode | None) -> str | None:
        if key is None:
            return None
        if isinstance(key, keyboard.Key):
            return str(key)
        if isinstance(key, keyboard.KeyCode):
            return key.char if key.char else str(key)
        return str(key)

    def _flush_events(self, final: bool = False) -> None:
        with self._lock:
            if not self._events:
                return
            events = self._events
            self._events = []

        for i in range(0, len(events), CHUNK_SIZE):
            chunk = events[i : i + CHUNK_SIZE]
            start_ts = chunk[0]["timestamp"]
            end_ts = chunk[-1]["timestamp"]

            table = pa.table(
                {
                    "image": pa.array([e["image"] for e in chunk], type=pa.binary()),
                    "timestamp": pa.array(
                        [e["timestamp"] for e in chunk], type=pa.float64()
                    ),
                    "mouse_x": pa.array(
                        [e["mouse_x"] for e in chunk], type=pa.int32()
                    ),
                    "mouse_y": pa.array(
                        [e["mouse_y"] for e in chunk], type=pa.int32()
                    ),
                    "mouse_dx": pa.array(
                        [e["mouse_dx"] for e in chunk], type=pa.int32()
                    ),
                    "mouse_dy": pa.array(
                        [e["mouse_dy"] for e in chunk], type=pa.int32()
                    ),
                    "mouse_left": pa.array(
                        [e["mouse_left"] for e in chunk], type=pa.bool_()
                    ),
                    "mouse_right": pa.array(
                        [e["mouse_right"] for e in chunk], type=pa.bool_()
                    ),
                    "key_w": pa.array(
                        [e["key_w"] for e in chunk], type=pa.bool_()
                    ),
                    "key_a": pa.array(
                        [e["key_a"] for e in chunk], type=pa.bool_()
                    ),
                    "key_s": pa.array(
                        [e["key_s"] for e in chunk], type=pa.bool_()
                    ),
                    "key_d": pa.array(
                        [e["key_d"] for e in chunk], type=pa.bool_()
                    ),
                    "key_space": pa.array(
                        [e["key_space"] for e in chunk], type=pa.bool_()
                    ),
                    "key_shift": pa.array(
                        [e["key_shift"] for e in chunk], type=pa.bool_()
                    ),
                    "key_ctrl": pa.array(
                        [e["key_ctrl"] for e in chunk], type=pa.bool_()
                    ),
                }
            )

            name = f"events-{start_ts:.6f}-{end_ts:.6f}.parquet"
            pq.write_table(table, self.data_dir / name)
