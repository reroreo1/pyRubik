<h1 align="center"> Rubik Cube </h1>

<video src="https://www.youtube.com/watch?v=6fbnkRhYae0" alt="bob" title="gif" width="900" />
A 3D Rubik's Cube visualizer and solver using OpenGL, Pygame, and Kociemba's two-phase algorithm.

## Quick Start

```bash
make setup        # Install dependencies + build solver (one-time setup)
make run  # Run the application
```

**Controls:**
- **Mouse Drag** - Rotate cube
- **F/B/U/D/L/R** - Rotate faces  
- **X** - Shuffle | **S** - Solve | **W** - Reset | **Q** - Quit

## Project Structure

```
pyRubik/
├── Makefile                      # Root build system
├── README.md                    # Original project info
├── requirements.txt             # Python dependencies
├── cub3D.py                     # Main Python GUI application
├── cubie.py                     
├── rubiks_cube 
├── twophase_solver.py           # Python-C++ bridge
│
└── solver/                      # C++ Solver
    ├── cubepos.cpp/h            # Cube representation & operations
    ├── phase1.cpp/h             # Phase 1: Kociemba reduction
    ├── phase2.cpp/h             # Phase 2: Permutation solving
    ├── cube_symmetry.cpp/h      # Symmetry & coordinate mapping
    ├── twophase_solver.cpp/h    # Main solver class
    ├── solver_main.cpp          # Entry point
│
└── images/               
    ├── background.jpg               # Background texture (if available)
    ├── loading.jpg               # Background texture (if available)

└── docs/
    ├── twophase       # reademe
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

- **[twophase.md](docs/twophase.md)** - Full technical details

## Prerequisites

- Python 3.10+
- C++11 compiler (g++)
- OpenGL drivers
