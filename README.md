# pyRubik

A 3D Rubik's Cube visualizer and solver using OpenGL, Pygame, and Kociemba's two-phase algorithm.

## Quick Start

```bash
make setup        # Install dependencies + build solver (one-time setup)
python3 cub3D.py  # Run the application
```

**Controls:**
- **Mouse Drag** - Rotate cube
- **F/B/U/D/L/R** - Rotate faces  
- **X** - Shuffle | **S** - Solve | **W** - Reset | **Q** - Quit

## Project Structure

```
pyRubik/
├── Makefile                      # Root build system
├── REFACTORING.md               # Solver refactoring details
├── LOADING_SCREEN.md            # Loading screen implementation
├── README.md                    # Original project info
├── requirements.txt             # Python dependencies
├── cub3D.py                     # Main Python GUI application
├── twophase_solver.py           # Python-C++ bridge
├── background.jpg               # Background texture (if available)
│
└── solver/                      # C++ Solver
    ├── cubepos.cpp/h            # Cube representation & operations
    ├── phase1.cpp/h             # Phase 1: Kociemba reduction
    ├── phase2.cpp/h             # Phase 2: Permutation solving
    ├── cube_symmetry.cpp/h      # Symmetry & coordinate mapping
    │
    ├── Solver
    ├── twophase_solver.cpp/h    # Main solver class
    ├── twophase.cpp             # Configuration (now minimal)
    ├── solver_main.cpp          # Entry point
    │
    └── Support
        ├── corner_order.h       # Corner sticker ordering
        ├── bestsol.h            # Best solution tracking
        └── *.dat                # Pruning tables (generated at runtime)
```

## Key Components

### 1. **C++ Solver** (`solver/`)
- **Algorithm:** Kociemba's two-phase algorithm
- **Target:** Solutions under 45 moves
- **Input:** Singmaster notation (stdin)
- **Output:** Move sequence (stdout)

### 2. **Python Integration** (`twophase_solver.py`)
- Bridges Python GUI to C++ solver
- Handles subprocess communication
- Simplifies move sequences
- Error handling and timeouts

### 3. **3D Visualizer** (`cub3D.py`)
- OpenGL-based 3D rendering
- Interactive cube manipulation
- Smooth animations with easing
- Minimap showing cube state
- Control guide panel

### 4. **Build System** (`Makefile`)
- Root-level Makefile for easy project management
- Install Python dependencies from `requirements.txt`
- Build C++ solver
- Clean targets for various levels

## Documentation

- **[REFACTORING.md](docs/REFACTORING.md)** - Solver optimization & cleanup
- **[LOADING_SCREEN.md](docs/LOADING_SCREEN.md)** - Background initialization  
- **[PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)** - Full technical details

## Prerequisites

- Python 3.10+
- C++11 compiler (g++)
- OpenGL drivers