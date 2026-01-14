#ifndef PHASE1_H
#define PHASE1_H

#include "cube_symmetry.h"

// ============================================================================
// PHASE 1 PRUNING TABLE - KOCIEMBA SUBGROUP REDUCTION
// ============================================================================
//
// PURPOSE:
//   Phase 1 reduces the cube into the Kociemba subgroup (G1) where corners
//   and edges can only be oriented correctly (not flipped/twisted).
//   This is done using IDA* search with a precomputed pruning table.
//
// ALGORITHM:
//   - Uses CubeSymmetry coordinates to represent cube state
//   - Pruning table stores minimum distance to G1 for each state
//   - Typical depth: 0-11 moves
//
// FILE I/O:
//   - Filename: data1.dat (generated on first run, ~10MB)
//   - Includes checksum for integrity verification
//   - Uses 65KB chunks for efficient I/O
//
// ============================================================================

const int BYTES_PER_ENTRY = 4;      // 4 bytes per pruning table entry

// Phase 1 pruning table manager - singleton pattern with static methods
class phase1 {
public:
    // Initialize pruning table (loads from disk or generates if missing)
    static void init(int suppress_writing = 0);

    // Lookup functions to query pruning table
    // - lookup(CubeSymmetry): Returns minimum distance to G1
    // - lookup(CubeSymmetry, int&): Returns distance + valid next moves
    // - lookup(CubeSymmetry, int, int&): Returns distance with depth limit
    static int lookup(const CubeSymmetry& kc, int& mask);
    static int lookup(const CubeSymmetry& kc);
    static int lookup(const CubeSymmetry& kc, int togo, int& nextmovemask);

    // Greedy solver (rarely used, kept for reference)
    static moveseq solve(CubeSymmetry kc);

    // Table generation and I/O
    static void gen_table();   // Builds table from scratch using BFS
    static int read_table();   // Loads from disk, returns 1 if successful
    static void write_table(); // Saves table to disk

    // Static data (shared across all calls)
    static unsigned int memsize;              // Total bytes allocated
    static unsigned char* mem;                // Pruning table data
    static int file_checksum;                 // For integrity verification
    static const char* const filename;        // "data1.dat"
};
public:
    static void init(int suppress_writing = 0);

    static int lookup(const CubeSymmetry& kc, int& mask);
    static int lookup(const CubeSymmetry& kc);
    static int lookup(const CubeSymmetry& kc, int togo, int& nextmovemask);

    static moveseq solve(CubeSymmetry kc);

    static void gen_table();
    static int read_table();
    static void write_table();

    static unsigned int memsize;
    static unsigned char* mem;
    static int file_checksum;
    static const char* const filename;
};

#endif
