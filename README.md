# 🤖 Robot Command Simulator
### Compiler Design Course Project

---

## Overview

A full **compiler pipeline** for a custom robot command language, built with:

| Layer | Technology | File |
|---|---|---|
| Lexer (tokeniser) | **Flex** | `compiler/robot_lexer.l` |
| Parser (grammar) | **Bison** | `compiler/robot_parser.y` |
| Compiler glue | **C** | `compiler/main.c` |
| Frontend / GUI | **Python + Tkinter** | `frontend/app.py` |
| Animation | **Python** | `frontend/robot_canvas.py` |
| Compiler bridge | **Python** | `frontend/command_runner.py` |

---

## Project Structure

```
E:\RobotCommandSimulator\
│
├── compiler\
│   ├── robot_lexer.l       ← Flex lexer definition
│   ├── robot_parser.y      ← Bison parser + JSON output
│   ├── main.c              ← C entry point
│   ├── Makefile            ← Build automation
│   └── robot_compiler.exe  ← (built output)
│
├── frontend\
│   ├── app.py              ← Main GUI window
│   ├── robot_canvas.py     ← Animated robot renderer
│   └── command_runner.py   ← Calls binary or Python fallback
│
├── run.bat                 ← Double-click to launch
└── README.md
```

---

## How to Run

### Quick Start (no build needed)
```bat
double-click  run.bat
```
or
```
python frontend\app.py
```
The Python fallback lexer+parser activates automatically if the C binary is not built yet. All features work identically.

---

### Build the Flex/Bison Compiler (optional — for full pipeline)

**Requirements:** MinGW (GCC), Flex, Bison

```bat
cd compiler
make
```

Once built, the app automatically detects `robot_compiler.exe` and switches to the true C pipeline.

---

## Robot Command Language (RCL)

### Syntax

```
# This is a comment

speed <1-10>

move forward  <N> [steps]
move backward <N> [steps]
move left     <N> [steps]
move right    <N> [steps]

turn left  <N> [degrees]
turn right <N> [degrees]

ability "shield"
ability "laser"
ability "boost"

stop
```

### Examples

```
speed 8
move forward 5 steps
turn left 90 degrees
ability "shield"
move forward 3 steps
stop
```

### Aliases

| Alias | Resolves to |
|---|---|
| `go` | `move` |
| `rotate` | `turn` |
| `halt` | `stop` |
| `skill` | `ability` |
| `back` | `backward` |
| `deg` | `degrees` |

---

## Compiler Pipeline

```
Source code (RCL)
       │
       ▼
  ┌─────────────┐
  │  Flex Lexer │  robot_lexer.l
  │  (tokenise) │  → MOVE, FORWARD, NUMBER, …
  └──────┬──────┘
         │ token stream
         ▼
  ┌──────────────┐
  │ Bison Parser │  robot_parser.y
  │  (grammar)   │  → validates syntax, emits JSON
  └──────┬───────┘
         │ JSON array
         ▼
  ┌──────────────┐
  │ Python GUI   │  app.py + robot_canvas.py
  │ (animation)  │  → animates the robot
  └──────────────┘
```

---

## Commands Reference

| Command | Effect |
|---|---|
| `speed N` | Set animation speed (1=slow, 10=fast) |
| `move forward N` | Move robot forward N grid steps |
| `move backward N` | Move robot backward N steps |
| `move left N` | Strafe left N steps |
| `move right N` | Strafe right N steps |
| `turn left N` | Rotate left N degrees |
| `turn right N` | Rotate right N degrees |
| `ability "shield"` | Expanding green shield ring effect |
| `ability "laser"` | Forward laser beam effect |
| `ability "boost"` | Speed-line boost effect |
| `stop` | Flash-halt animation |

---

## Developer

**Abu Sayed Ruman**  
Compiler Design — Academic Project  
Technologies: Flex · Bison · C · Python · Tkinter
