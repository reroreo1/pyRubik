#ifndef CUBEPOS_H
#define CUBEPOS_H

#include <cstring>
#include <cstdlib>
#include <stddef.h>
#include <vector>
#include <algorithm>

using namespace std;

// ============================================================================
// CUBEPOS.H - CUBE POSITION REPRESENTATION
// ============================================================================
//
// This header defines the core data structure for representing a Rubik's cube
// position and all operations on it.
//
// INTERNAL REPRESENTATION:
//   - Corner cubies: Each corner encodes position (0-7) and orientation (0-2)
//   - Edge cubies: Each edge encodes position (0-11) and orientation (0-1)
//   - Encoding: corner = ori * 8 + perm, edge = perm * 2 + ori
//
// KEY CONCEPTS:
//   - Move: A face rotation (18 total: 6 faces × 3 twist types)
//   - Symmetry: Cube can be viewed in 48 different orientations
//   - Canonical sequence: Valid move sequences avoiding redundant face rotations
//
// ============================================================================

// ============================================================================
// Constants
// ============================================================================

const int NMOVES = 18;          // Total possible moves (6 faces × 3 twists)
const int TWISTS = 3;           // Twist types: 90° (1), 180° (2), 270° (3)
const int FACES = 6;            // Number of cube faces: U,F,R,D,B,L
const int M = 48;               // Number of cube symmetries (rotations + inversions)
const int CUBIES = 24;          // Total cubie encoding values (8 corners × 3 + 12 edges × 2)

// Forward declaration
extern const class cubepos identity_cube;

// Type definitions
typedef vector<int> moveseq;

// Move mask constants
const int ALLMOVEMASK = (1 << NMOVES) - 1;

// Canonical sequence states for move pruning
const int CANONSEQSTATES = FACES + 1;
const int CANONSEQSTART = 0;

// I/O chunk size for reading/writing pruning tables
const int TABLE_CHUNKSIZE = 65536;

// ============================================================================
// Utility Functions
// ============================================================================

void error(const char* s);
int datahash(unsigned int* dat, int sz, int seed);

// ============================================================================
// Cube Position Class
// ============================================================================

/**
 * Represents the state of a Rubik's cube using arrays for corner and edge cubies.
 * Each cubie encodes both its position (permutation) and orientation.
 * 
 * Corner encoding: ori * 8 + perm (ori in 0-2, perm in 0-7)
 * Edge encoding: perm * 2 + ori (perm in 0-11, ori in 0-1)
 */
class cubepos {
public:
    // ========================================================================
    // Data Members
    // ========================================================================
    
    unsigned char c[8];   // Corner cubies (permutation + orientation)
    unsigned char e[12];  // Edge cubies (permutation + orientation)

    // ========================================================================
    // Comparison Operators
    // ========================================================================
    
    inline bool operator<(const cubepos& cp) const {
        return memcmp(this, &cp, sizeof(cp)) < 0;
    }
    
    inline bool operator==(const cubepos& cp) const {
        return memcmp(this, &cp, sizeof(cp)) == 0;
    }
    
    inline bool operator!=(const cubepos& cp) const {
        return memcmp(this, &cp, sizeof(cp)) != 0;
    }

    // ========================================================================
    // Cubie Value Extraction and Construction
    // ========================================================================
    
    static inline int edge_perm(int cubieval) { return cubieval >> 1; }
    static inline int edge_ori(int cubieval) { return cubieval & 1; }
    static inline int corner_perm(int cubieval) { return cubieval & 7; }
    static inline int corner_ori(int cubieval) { return cubieval >> 3; }
    static inline int edge_flip(int cubieval) { return cubieval ^ 1; }
    static inline int edge_val(int perm, int ori) { return perm * 2 + ori; }
    static inline int corner_val(int perm, int ori) { return ori * 8 + perm; }
    static inline int edge_ori_add(int cv1, int cv2) { return cv1 ^ edge_ori(cv2); }
    static inline int corner_ori_add(int cv1, int cv2) { return mod24[cv1 + (cv2 & 0x18)]; }
    static inline int corner_ori_sub(int cv1, int cv2) { return cv1 + corner_ori_neg_strip[cv2]; }
    
    // ========================================================================
    // Initialization and Constructors
    // ========================================================================
    
    static void init();
    inline cubepos(const cubepos& cp = identity_cube) { *this = cp; }
    inline cubepos& operator=(const cubepos& cp) {
        memcpy(this, &cp, sizeof(cubepos));
        return *this;
    }
    cubepos(int, int, int);

    // ========================================================================
    // Move Operations
    // ========================================================================
    
    void move(int mov);
    void movepc(int mov);

    // ========================================================================
    // Move Inversion
    // ========================================================================
    
    static int invert_move(int mv) { return inv_move[mv]; }
    static moveseq invert_sequence(const moveseq& sequence);
    void invert_into(cubepos& dst) const;


    // ========================================================================
    // Parsing and String Conversion
    // ========================================================================
    
    static void skip_whitespace(const char*& p);
    static int parse_face(const char*& p);
    static int parse_face(char f);
    static void append_face(char*& p, int f) { *p++ = faces[f]; }
    static int parse_move(const char*& p);
    static void append_move(char*& p, int mv);
    static void append_moveseq(char*& p, const moveseq& seq);
    static char* moveseq_string(const moveseq& seq);

    // ========================================================================
    // Singmaster Notation
    // ========================================================================
    
    const char* parse_Singmaster(const char* p);

    // ========================================================================
    // Symmetry and Canonicalization
    // ========================================================================
    
    void remap_into(int m, cubepos& dst) const;

    // ========================================================================
    // Canonical Sequence Helpers
    // ========================================================================
    
    static inline int next_cs(int cs, int mv) { return canon_seq[cs][mv]; }
    static inline int cs_mask(int cs) { return canon_seq_mask[cs]; }

    // ========================================================================
    // Static Lookup Tables
    // ========================================================================
    
    static unsigned char corner_ori_inc[CUBIES], corner_ori_dec[CUBIES],
                         corner_ori_neg_strip[CUBIES], mod24[2 * CUBIES];
    static char faces[FACES];
    static unsigned char edge_trans[NMOVES][CUBIES], corner_trans[NMOVES][CUBIES];
    static unsigned char inv_move[NMOVES];
    static unsigned char face_map[M][FACES], move_map[M][NMOVES];
    static unsigned char invm[M], mm[M][M];
    static unsigned char rot_edge[M][CUBIES], rot_corner[M][CUBIES];
    static unsigned char canon_seq[CANONSEQSTATES][NMOVES];
    static int canon_seq_mask[CANONSEQSTATES];
};

// Force initialization at startup
static cubepos cubepos_initialization_hack(1, 2, 3);

#endif
