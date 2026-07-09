# Snake Link

Snake Link is a Windows-first single-player Snake game written in C11 with raylib. The snake body is implemented as a doubly circular linked list so the game can be used both as a small PC game and as a learning project for linked-list operations.

## Features

- Classic high-score Snake rules: wall collision and body collision end the run.
- 32x24 grid in a fixed 960x720 desktop window.
- Snake body stored as a doubly circular linked list.
- The board keeps a random 5 to 10 food items active; active foods use non-repeating display colors.
- Food shapes/types:
  - Apple: +10, grow 1 segment.
  - Star: +50, grow 1 segment.
  - Ice: +20, grow 1 segment, slow the snake for 5 seconds.
- Every 5 normal apples spawns the next special food; star and ice alternate.
- Gradual speed-up from 180ms/step to 90ms/step.
- Local high score saved to `snake_high_score.txt` beside the executable.
- Generated lightweight sound effects, hover feedback, food glow, and simple eat animations.
- The snake changes to the exact display color of the last food it ate.
- F1 debug overlay showing linked-list node order, Head/Tail, length, and coordinates.

## Controls

- `Enter`: start or restart.
- Mouse click: start, resume, or restart using the visible buttons.
- `WASD` or arrow keys: move.
- `Space`: pause or resume.
- `Esc`: return to the start screen.
- `F1`: toggle linked-list debug overlay.

## Build

The project uses CMake FetchContent to download raylib and GoogleTest.

```powershell
cmake --preset mingw-debug
cmake --build --preset mingw-debug
```

If `cmake` is not installed, install CMake or use a Python CMake wheel:

```powershell
python -m pip install cmake
```

## Test

```powershell
ctest --preset mingw-debug
```

The tests cover linked-list initialization, circular links, movement, growth, collision rules, food and speed rules, high-score persistence, and UI hitbox helpers.

## Run

```powershell
.\build\debug\bin\snake_client.exe
```

## Linked-List Learning Notes

The core snake structure lives in `include/snake_game/snake_list.h` and `src/snake_list.c`.

- `head` is the current snake head.
- `tail` is the final body segment.
- `head->prev == tail` and `tail->next == head`, forming a circular list.
- Every movement inserts a new head node.
- If no food was eaten, the tail node is removed.
- If food was eaten, the tail remains, so the snake grows.
- Moving into the current tail cell is safe when the tail will leave in the same step.
