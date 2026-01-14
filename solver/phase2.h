#ifndef PHASE2_H
#define PHASE2_H

#include "cube_symmetry.h"

// ============================================================================
// PHASE 2 PRUNING TABLE - PERMUTATION SOLVER
// ============================================================================
//
// PURPOSE:
//   Phase 2 solves the cube from G1 (correctly oriented) to solved state.
//   It focuses on edge and corner permutations using a separate pruning table.
//
// ALGORITHM:
//   - Uses permcube coordinates (reduced permutation representation)
//   - Pruning table stores minimum distance to solved for each G1 state
//   - Typical depth: 0-10 moves
//   - Only allows moves in Kociemba group to maintain correctness
//
// COORDINATES:
//   - Top/middle/bottom edge layers: separate permutation coords
//   - Corner permutations: compressed to 8! / 24 = 1680 states
//   - Symmetry reduction: uses CubeSymmetry for space efficiency
//
// FILE I/O:
//   - Filename: data2.dat (generated on first run, ~20MB)
//   - Uses 65KB chunks for efficient reading
//   - Includes checksum for corruption detection
//
// ============================================================================

const int FACT8 = 40320;    // 8! - Maximum corner permutations

// Phase 2 pruning table manager - singleton pattern with static methods
class phase2 {
public:
    static void init(int suppress_writing = 0);

    // Lookup functions
    static int lookup(const cubepos& cp);                    // From cubepos
    static int lookup(const permcube& pc);                  // From permcube

    // Solving functions using IDA* with pruning table
    // Returns move sequence or empty if unsolvable within maxlen
    static moveseq solve(const permcube& pc, int maxlen = 30);
    static moveseq solve(const cubepos& cp, int maxlen = 30) {
        permcube pc(cp);
        return solve(pc, maxlen);
    }
    // Core IDA* solver: recurses with depth limit, building solution backwards
    static int solve(const permcube& pc, int togo, int canonstate, moveseq& seq);

    // Table generation and I/O
    static void gen_table();   // Builds table from scratch using iterative deepening
    static int read_table();   // Loads from disk with checksum verification
    static void write_table(); // Saves table and checksum to disk

    // Static data
    static int cornermax;                         // Number of reduced corner states
    static unsigned int memsize;                  // Total bytes allocated
    static unsigned int* mem;                     // Pruning table data
    static const char* const filename;            // "data2.dat"
    static int file_checksum;                     // Checksum for verification
};
};

#endif
