#ifndef TWOPHASE_SOLVER_H
#define TWOPHASE_SOLVER_H

#include "cube_symmetry.h"
#include "phase1.h"
#include "phase2.h"
/*
===============================================================================
 TWO-PHASE SOLVER - MAIN ALGORITHM ORCHESTRATOR
===============================================================================

PURPOSE:
    Implements the high-level Kociemba two-phase algorithm for Rubik's Cube.
    Coordinates search across multiple cube orientations and symmetries.

ALGORITHM OVERVIEW:
    1. Generate 6 distinct cube orientations (3 axes × 2 inversions)
    2. For each orientation, perform Phase 1 IDA* to reach Kociemba subgroup
    3. Once in G1, use Phase 2 to solve remaining permutations
    4. Prune equivalent orientations to avoid redundant work
    5. Return optimal solution (typically 20-23 moves)

CONFIGURATION:
    - MAX_MOVES: Hard limit on solution length (50 moves)
    - target_length: Target solution (45 moves typical)
    - phase2limit: Node expansion limit to prevent infinite search
    - axesmask: Which orientations to search (default: all 6)

CLASS OVERVIEW:
    TwophaseSolver orchestrates the two-phase search:
        - solve(): Entry point, tries all orientations
        - solve_phase1(): IDA* search for Phase 1
        - solve_phase2(): Phase 2 permutation solver
        - Internal state tracks best solution, move sequences, and symmetry info

FUNCTIONS:
    display_solution(): Outputs the final move sequence to stdout
    cubes_equal_up_to_symmetry(): Checks for duplicate states under symmetry

*/

// Global configuration values for the twophase solver.

// Compile‑time limits used for static array sizes.
#define MAX_MOVES   50           // Hard upper bound on move count

extern const int target_length;       // Target maximum solution length
extern const long long phase2limit;   // Limit on phase 2 node expansions
extern const int skipwrite;           // If non‑zero, do not write pruning tables to disk
extern const int axesmask;            // Mask controlling which cube orientations are searched


// Output the final solution move sequence to stdout
//   sol: move sequence found by solver
void display_solution(const moveseq& sol);

// High‑level two‑phase Kociemba solver.
// Solves a single cube state without threading.

// High-level two-phase Kociemba solver.
// Orchestrates Phase 1 and Phase 2 searches across multiple cube orientations.
class TwophaseSolver {
public:
    TwophaseSolver();

    // Main entry point: Solve a single cube position.
    //   seqarg: sequence type (move encoding)
    //   cp: cube position to solve
    void solve(int seqarg, cubepos& cp);

private:
    // Phase 1: Reduce the cube into the Kociemba subgroup using pruning tables.
    //   kc: CubeSymmetry coordinate
    //   pc: Permcube representation
    //   togo: moves left to reach subgroup
    //   sofar: moves used so far
    //   movemask: valid moves mask
    //   canon: canonical orientation index
    void solve_phase1(const CubeSymmetry& kc, const permcube& pc, int togo, int sofar, int movemask, int canon);

    // Phase 2: Solve the remaining permutation problem once orientations are fixed by phase 1.
    //   pc: Permcube representation
    //   sofar: moves used so far
    void solve_phase2(const permcube& pc, int sofar);

    // Working state for a single solve.
    cubepos pos;
    long long phase2probes;
    int bestsol;
    int finished;
    int curm;
    int solmap;
    int seq;

    unsigned char moves[MAX_MOVES];
    unsigned char bestmoves[MAX_MOVES];

    // Up to six distinct cube orientations (3 axes × 2 inversions).
    CubeSymmetry kc6[6], kccanon6[6]; // Symmetry coordinates for each orientation
    cubepos cp6[6];                   // Cube positions for each orientation
    permcube pc6[6];                  // Permcube representations for each orientation
    int mindepth[6];                  // Minimum depth to subgroup for each orientation
    char uniq[6];                     // Uniqueness flags for pruning
    int minmindepth;                  // Minimum depth found across all orientations
};

// Compare two cube positions up to any symmetry from the Kociemba group.
// Compare two cube positions up to any symmetry from the Kociemba group.
// Returns true if cp1 and cp2 are equivalent under symmetry.
int cubes_equal_up_to_symmetry(const cubepos& cp1, const cubepos& cp2);

#endif // TWOPHASE_SOLVER_H
