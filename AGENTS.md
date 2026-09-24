# AI Development Agent Guidelines: Screen & Input Recorder

## 🎯 Project Overview
A lightweight Python-based background logging tool designed to capture desktop interactions (screenshots, keyboard events, mouse movements, and clicks) synchronized via timestamps. The primary goal is to collect raw multimodal data for training machine learning models (Behavioral Cloning / UI Automation agents).

---

## 🛠️ Tech Stack & Dependencies
* **Language:** Python 3.10+
* **Screen Capture:** `mss` (fast cross-platform screenshot utility)
* **Input Hooking:** `pynput` (global listeners for keyboard & mouse)
* **Data Format:** 
  * Parquet format, like Shema 
  * Images will be in small format 1024 x 576

---

## 📂 Project Structure
```text
ui-recorder/
├── data/
│   ├── events-000000-000010.partquet
│   ├── events-000010-000100.partquet
```

---

## Schema 
and one json with screen width and height

- image
- timestamp
- mouse_x
- mouse_y
- mouse_dx
- mouse_dy
- mouse_left
- mouse_right
- key_w
- key_a
- key_s
- key_d
- key_space
- key_shift
- key_ctrl

