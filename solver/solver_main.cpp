#include "twophase_solver.h"
#include "phase1.h"
#include "phase2.h"

#include <iostream>
#include <string>

using namespace std;

// ============================================================================
// RUBIK'S CUBE SOLVER - TWO-PHASE KOCIEMBA ALGORITHM
// ============================================================================
//
// ENTRY POINT: solver_main.cpp
// 
// PURPOSE:
//   This is the main executable that solves a single Rubik's cube position
//   using the Two-Phase Kociemba algorithm. It reads a cube state in 
//   Singmaster notation from stdin and outputs the optimal or near-optimal
//   solution move sequence.
//
// ALGORITHM OVERVIEW:
//   The Two-Phase algorithm solves the cube in two phases:
//   - Phase 1: Reduce the cube to the Kociemba subgroup (G1) using BFS/IDA*
//     with a pruning table. This takes ~11 moves on average.
//   - Phase 2: Solve the remaining permutation problem using IDA* with
//     another pruning table. This takes ~10 moves on average.
//   - Total: ~21 moves (guaranteed under 30 moves for any cube state)
//
// SINGMASTER NOTATION:
//   Input format: 12 edge positions + 8 corner positions
//   Example: "UF UR UB UL DF DR DB DL FR FL BR BL UFR URB UBL ULF DRF DFL DLB DBR"
//   - Edges: UF (up-front), UR (up-right), etc.
//   - Corners: UFR (up-front-right), URB (up-right-back), etc.
//
// WORKFLOW:
//   1. Initialize pruning tables (Phase 1 and Phase 2)
//   2. Read cube state from stdin in Singmaster notation
//   3. Parse Singmaster into internal cubepos representation
//   4. Create solver and call solve()
//   5. Output the move sequence to stdout
//
// ============================================================================

int main() {
    // Optimization: Disable C++ stdio synchronization with C stdio for faster I/O
    // Since we use only C++ streams, this avoids unnecessary flushing overhead
    ios::sync_with_stdio(false);
    cout.setf(ios::unitbuf);  // Enable unbuffered output for immediate results
    
    // STEP 1: Initialize all pruning tables
    // phase1::init() builds or loads the Phase 1 pruning table (data1.dat)
    // This table stores minimum distances for G1 (Kociemba subgroup) positions
    // Takes ~30 seconds first time, then loads from disk in <1 second
    phase1::init(skipwrite);
    
    // phase2::init() builds or loads the Phase 2 pruning table (data2.dat)
    // This table stores minimum distances for G0 (permutation) coordinates
    // Takes ~60 seconds first time, then loads from disk in ~2 seconds
    phase2::init(skipwrite);

    // STEP 2: Read the cube state from standard input
    // Expected format: Singmaster notation with 20 cubie positions
    string input_line;
    if (!getline(cin, input_line)) {
        cerr << "Error: No input provided" << endl;
        return 1;
    }

    // STEP 3: Parse Singmaster notation into internal representation
    // Creates a cubepos object with corner and edge orientation/permutation data
    cubepos cube_state;
    const char* parse_result = cube_state.parse_Singmaster(input_line.c_str());
    if (parse_result != 0) {
        cerr << "Error: " << parse_result << endl;
        return 1;
    }

    // Create a solver instance and solve the cube
    TwophaseSolver solver;
    solver.solve(1, cube_state);

    return 0;
}
