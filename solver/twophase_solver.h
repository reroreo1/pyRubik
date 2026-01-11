#ifndef TWOPHASE_SOLVER_H
#define TWOPHASE_SOLVER_H

#include "solver_config.h"
#include "cube_symmetry.h"
#include "phase1prune.h"
#include "phase2prune.h"
#include "solver_solution_queue.h"
#include "solver_input.h"

// High‑level two‑phase Kociemba solver.
// Each TwophaseSolver instance owns the working state used by a single
// worker thread (phase 1 + phase 2 search, buffers, orientations, ...).

class TwophaseSolver {
public:
    TwophaseSolver();

    // Solve a single cube position. "seqarg" is a monotonically
    // increasing sequence id used only for deterministic output order.
    void solve(int seqarg, cubepos& cp);

    // Process work in a loop by repeatedly reading from stdin until EOF.
    void dowork();

    // Entry point passed to pthread_create.
    static void* worker_entry(void* s);

private:
    // Phase 1: reduce the cube into the Kociemba subgroup using pruning
    // tables on the CubeSymmetry coordinate.
    void solve_phase1(const CubeSymmetry& kc,
                      const permcube& pc,
                      int togo,
                      int sofar,
                      int movemask,
                      int canon);

    // Phase 2: solve the remaining permutation problem once orientations
    // have been fixed by phase 1.
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
    CubeSymmetry kc6[6], kccanon6[6];
    cubepos cp6[6];
    permcube pc6[6];
    int mindepth[6];
    char uniq[6];
    int minmindepth;
};

// One solver instance per potential worker thread.
extern TwophaseSolver solvers[];

// Compare two cube positions up to any symmetry from the Kociemba group.
int cubes_equal_up_to_symmetry(const cubepos& cp1, const cubepos& cp2);

#endif // TWOPHASE_SOLVER_H
