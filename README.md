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

## Schema of data, in partquet

- 0 image Bytes of WEBP image in 1024 x 586
- 1 timestamp float
- 2 mouse_x int
- 3 mouse_y int
- 4 mouse_left bool
- 5 mouse_right bool
- 6 key_w bool
- 7 key_a bool
- 8 key_s bool
- 9 key_d bool
- 10 key_space bool
- 11 key_shift bool
- 12 key_ctrl bool
