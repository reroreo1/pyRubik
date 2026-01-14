#ifndef CUBE_SYMMETRY_H
#define CUBE_SYMMETRY_H

/*
===============================================================================
 CUBE_SYMMETRY - COORDINATE AND SYMMETRY SYSTEM
===============================================================================

PURPOSE:
    Provides coordinate systems and symmetry operations for Rubik's Cube states.
    Used for efficient pruning and equivalence checking in the Kociemba algorithm.

KEY CONCEPTS:
    - CubeSymmetry: Encodes cube state using Kociemba's symmetry coordinates
        (corner orientation, edge orientation, edge permutation)
    - permcube: Encodes permutation-only state for Phase 2
    - Static lookup tables for fast move application and symmetry reduction

ALGORITHM OVERVIEW:
    - CubeSymmetry is used in Phase 1 to reduce the cube to the G1 subgroup
    - permcube is used in Phase 2 to solve the remaining permutation problem
    - Symmetry tables allow pruning of equivalent states and fast move transitions

CLASS OVERVIEW:
    CubeSymmetry:
        - csymm, eosymm, epsymm: Coordinates for corners, edge orientation, edge permutation
        - move(): Applies a move to the symmetry coordinates
        - init(): Initializes all static lookup tables
        - in_Kociemba_group(): Checks if a move is valid in G1

    permcube:
        - et, em, eb: Edge permutation coordinates
        - c8_4, ctp, cbp: Corner permutation coordinates
        - move(): Applies a move to permutation coordinates
        - init_edge_from_cp(), init_corner_from_cp(): Initialize from cubepos

STATIC TABLES:
    - cornermove, edgeomove, edgepmove: Move transitions for coordinates
    - cornersymm, edgeomap, edgepmap: Symmetry reduction tables
    - s4mul, s4compress, c8_4_compact: Permutation helpers for Phase 2

*/

#include "cubepos.h"

// ============================================================================
// Constants
// ============================================================================

const int CORNERSYMM = 2187;    // 3^7 corner orientations
const int EDGEOSYMM  = 2048;    // 2^11 edge orientations
const int EDGEPERM   = 495;     // C(12,4) edge permutation classes
const int CUBE_SYMM  = 16;      // Number of symmetries used in the tables
const int CORNERRSYMM = 168;    // Reduced corner symmetry classes

// ============================================================================
// Corner Map Info Structure
// ============================================================================

struct corner_mapinfo {
    unsigned short minbits;
    unsigned char csymm, minmap;
};

// ============================================================================
// Lookup Type
// ============================================================================

typedef unsigned short lookup_type;

// ============================================================================
// Kociemba Symmetry Class
// ============================================================================

// Represents a cube state using Kociemba's symmetry coordinates.
// These coordinates are sufficient to determine if the cube is in
// the "G1" subgroup where only half-turns of the middle layer are needed.
class CubeSymmetry {
public:
    // Coordinate values
    lookup_type csymm, eosymm, epsymm;

    // --------------------------------------------------------------------
    // Constructors
    // --------------------------------------------------------------------

    CubeSymmetry() : csymm(0), eosymm(0), epsymm(0) {}
    CubeSymmetry(int c, int eo, int ep) : csymm(c), eosymm(eo), epsymm(ep) {}
    CubeSymmetry(int) : csymm(0), eosymm(0), epsymm(0) { init(); }
    CubeSymmetry(const cubepos& cp);

    // Static initialization for all symmetry tables.
    static void init();

    // --------------------------------------------------------------------
    // Comparison Operators
    // --------------------------------------------------------------------

    inline bool operator<(const CubeSymmetry& kc) const {
        if (csymm != kc.csymm) return csymm < kc.csymm;
        if (eosymm != kc.eosymm) return eosymm < kc.eosymm;
        return epsymm < kc.epsymm;
    }

    inline bool operator==(const CubeSymmetry& kc) const {
        return kc.csymm == csymm && kc.eosymm == eosymm && kc.epsymm == epsymm;
    }

    inline bool operator!=(const CubeSymmetry& kc) const {
        return kc.csymm != csymm || kc.eosymm != eosymm || kc.epsymm != epsymm;
    }

    // --------------------------------------------------------------------
    // Move Application
    // --------------------------------------------------------------------

    void move(int mv) {
        csymm = cornermove[csymm][mv];
        eosymm = edgeomove[eosymm][mv];
        epsymm = edgepmove[epsymm][mv];
    }

    // --------------------------------------------------------------------
    // Cube State Operations
    // --------------------------------------------------------------------

    void set_coset(cubepos& cp);
    void canon_into(CubeSymmetry& kc) const;

    // --------------------------------------------------------------------
    // Kociemba Group Check
    // --------------------------------------------------------------------

    static inline int in_Kociemba_group(int mv) { return edgepmove[0][mv] == 0; }

    // --------------------------------------------------------------------
    // Static Lookup Tables
    // --------------------------------------------------------------------

    static lookup_type cornermove[CORNERSYMM][NMOVES];
    static lookup_type edgeomove[EDGEOSYMM][NMOVES];
    static lookup_type edgepmove[EDGEPERM][NMOVES];
    static lookup_type epsymm_compress[1 << 12];
    static lookup_type epsymm_expand[EDGEOSYMM];
    static lookup_type cornersymm_expand[CORNERRSYMM];
    static corner_mapinfo cornersymm[CORNERSYMM];
    static lookup_type edgeomap[EDGEOSYMM][CUBE_SYMM];
    static lookup_type edgepmap[EDGEPERM][CUBE_SYMM];
    static lookup_type edgepxor[EDGEPERM][2];
};

// Identity CubeSymmetry state
static CubeSymmetry identity_kc(1);

// ============================================================================
// Permutation Cube Class (Phase 2)
// ============================================================================

const int FACT4 = 24;   // 4! permutations
const int C8_4  = 70;   // C(8,4) combinations

// Represents the permutation state for phase 2 of Kociemba's algorithm.
// In phase 2, orientations are solved and we only need to track permutations.
class permcube {
public:
    // Edge permutation coordinates (top, middle, bottom layers)
    unsigned short et, em, eb;
    unsigned char etp, emp, ebp;

    // Corner permutation coordinates
    unsigned char c8_4, ctp, cbp;

    permcube();
    permcube(const cubepos& cp);

    inline bool operator<(const permcube& pc) const {
        if (et != pc.et) return et < pc.et;
        if (em != pc.em) return em < pc.em;
        if (eb != pc.eb) return eb < pc.eb;
        if (etp != pc.etp) return etp < pc.etp;
        if (emp != pc.emp) return emp < pc.emp;
        if (ebp != pc.ebp) return ebp < pc.ebp;
        if (c8_4 != pc.c8_4) return c8_4 < pc.c8_4;
        if (ctp != pc.ctp) return ctp < pc.ctp;
        return cbp < pc.cbp;
    }

    inline bool operator==(const permcube& pc) const {
        return et == pc.et && em == pc.em && eb == pc.eb &&
               etp == pc.etp && emp == pc.emp && ebp == pc.ebp &&
               c8_4 == pc.c8_4 && ctp == pc.ctp && cbp == pc.cbp;
    }

    inline bool operator!=(const permcube& pc) const {
        return !(*this == pc);
    }

    void move(int mv);
    void init_edge_from_cp(const cubepos& cp);
    void init_corner_from_cp(const cubepos& cp);
    void set_edge_perm(cubepos& cp) const;
    void set_corner_perm(cubepos& cp) const;
    void set_perm(cubepos& cp) const;

    static void init();

    static unsigned char s4mul[FACT4][FACT4];
    static unsigned char s4compress[256];
    static unsigned char s4expand[FACT4];
    static unsigned char c8_4_compact[256];
    static unsigned char c8_4_expand[C8_4];
    static unsigned char c8_4_parity[C8_4];
    static unsigned char c12_8[EDGEPERM];
    static lookup_type c8_12[C8_4];
    static unsigned short eperm_move[EDGEPERM][NMOVES];
    static int cperm_move[C8_4][NMOVES];
};

// Identity permcube state
static permcube identity_pc;

#endif
