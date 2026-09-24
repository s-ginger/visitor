# Visitor for Robox Rivals data

**A utility for collecting Roblox Rivals data while you play, created with Vibecode.**

## How to use

**Create a virtual envirement**
```cmd
python -m venv .venv
```

**Install requirements**
```cmd
pip install -r requirements.txt
```

**Start a game Roblox or what you like**

**Start a Visitor**
```cmd
python ./main.py
```

Press `Ctrl+C` to stop recording.

## Data structure

Each parquet file contains up to 1000 events, named `events-{start_timestamp}-{end_timestamp}.parquet`. File `screen.json` stores the monitor resolution.

## Schema of data, in partquet

- 0 image bytes of WEBP image in 1024 x 576
- 1 timestamp float
- 2 mouse_x int
- 3 mouse_y int
- 4 mouse_dx int
- 5 mouse_dy int
- 6 mouse_left bool
- 7 mouse_right bool
- 8 key_w bool
- 9 key_a bool
- 10 key_s bool
- 11 key_d bool
- 12 key_space bool
- 13 key_shift bool
- 14 key_ctrl bool

## screen.json

```json
{
  "width": 2560,
  "height": 1440
}
```