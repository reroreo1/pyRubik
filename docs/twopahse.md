# Two-Phase Kociemba Rubik's Cube Solver

## Overview
This solver implements the Kociemba two-phase algorithm, a state-of-the-art method for finding near-optimal solutions to the Rubik's Cube. The algorithm guarantees solutions in under 30 moves for any valid cube position and is widely used in speedcubing and robotics.

## Algorithm Workflow

### Phase 1: Subgroup Reduction
- **Goal:** Reduce the cube to the Kociemba subgroup (G1), where only half-turns of the middle layer are needed to solve the cube.
- **Method:**
  - The cube is represented using symmetry coordinates (corner orientation, edge orientation, edge permutation).
  - A large pruning table is generated (or loaded from disk) to quickly determine the minimum number of moves to reach G1 from any state.
  - Iterative Deepening A* (IDA*) search is used to find a sequence of moves that brings the cube into G1.

### Phase 2: Permutation Solving
- **Goal:** Solve the remaining permutation problem once the cube is in G1.
- **Method:**
  - The cube is now represented using permutation-only coordinates (permcube).
  - A second pruning table is used to determine the minimum moves to the solved state.
  - Another IDA* search finds the optimal sequence to solve the cube completely.

### Symmetry Optimization
- The solver considers up to 6 distinct cube orientations (3 axes × 2 inversions) to avoid redundant searches and exploit cube symmetries.
- Equivalent states are pruned using canonical coordinates and symmetry checks.

## Input/Output
- **Input:** Singmaster notation (e.g., "UF UR UB UL DF DR DB DL FR FL BR BL UFR URB UBL ULF DRF DFL DLB DBR")
- **Output:** Move sequence (e.g., "R1U1R3F2")

## Data Files
- `data1.dat`: Phase 1 pruning table (~10MB)
- `data2.dat`: Phase 2 pruning table (~20MB)
- These are generated on first run and loaded for subsequent solves.

## Code Structure
- `cubepos`: Cube state representation and move logic
- `cube_symmetry`: Symmetry operations and coordinate conversions
- `phase1`: Phase 1 pruning table generation and lookup
- `phase2`: Phase 2 pruning table and IDA* solver
- `twophase_solver`: Main algorithm orchestrator
- `solver_main.cpp`: Entry point, handles I/O and invokes solver

## References
- Kociemba, Herbert. "Two-Phase Algorithm for Rubik's Cube." [kociemba.org](https://kociemba.org/)
- Rubik's Cube Wiki: [https://ruwix.com/the-rubiks-cube/notation/](https://ruwix.com/the-rubiks-cube/notation/)

---
For further details, see the code comments in each module and the documentation in the `docs/` folder.
