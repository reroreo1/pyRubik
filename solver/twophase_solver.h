#ifndef TWOPHASE_SOLVER_H
#define TWOPHASE_SOLVER_H

#include <pthread.h>

#include "cube_symmetry.h"
#include "phase1.h"
#include "phase2.h"

// Global configuration values for the twophase solver.
// These reproduce the original behaviour from twophase.cpp.

extern const int verbose;        // Verbosity level (kept low for Python integration)
extern const int numthreads;     // Number of worker threads

// Compile‑time limits used for static array sizes.
#define MAX_THREADS 32           // Upper bound for worker array
#define MAX_MOVES   50           // Hard upper bound on move count

extern const int target_length;       // Target maximum solution length
extern const long long phase2limit;   // Limit on phase 2 node expansions
extern const int skipwrite;           // If non‑zero, do not write pruning tables to disk
extern const int axesmask;            // Mask controlling which cube orientations are searched

// Global mutex protecting stdin reads and solution output ordering.
extern pthread_mutex_t my_mutex;

// Acquire and release the global mutex.
void get_global_lock();
void release_global_lock();

// Read a single cube position from stdin in Singmaster notation.
// Returns a positive sequence id on success, or a non‑positive value
// on EOF or error. Thread‑safe via the global mutex.
int getwork(cubepos& cp);

// Small POD type used to keep solutions in sequence order while
// multiple worker threads finish at different times.
struct Solution {
    cubepos cube;            // Original scrambled cube position
    int sequence_id;         // Monotonic input id (1, 2, 3, ...)
    long long phase2_probes; // Number of phase 2 nodes expanded
    moveseq moves;           // Solving move sequence
};

// Report a finished solution. This function is thread‑safe: it is
// responsible for ordering solutions by sequence_id and printing the
// move sequence for each solved cube exactly once.
void report_solution(const cubepos& cp,
                     int seq,
                     long long phase2probes,
                     const moveseq& sol);

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
