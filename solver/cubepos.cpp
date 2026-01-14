#include <iostream>
#include "cubepos.h"

/*
===============================================================================
 CUBEPOS.CPP - CUBE STATE REPRESENTATION & MOVE LOGIC
===============================================================================

PURPOSE:
    Implements the core cube state representation and all move application logic.
    Handles parsing of Singmaster notation, move encoding, and state transitions.

KEY FUNCTIONS:
    - Static initialization of move tables and face mappings
    - move(): Applies a face rotation to the cube state
    - parse_Singmaster(): Parses input notation into internal representation
    - invert_into(), invert_sequence(): Cube state inversion operations

NOTES:
    - All move tables are initialized at startup for fast application
    - Used by TwophaseSolver and symmetry modules for all cube manipulations
*/

using namespace std;

// ============================================================================
// Static Data Initialization
// ============================================================================

const cubepos identity_cube(0, 0, 0);

unsigned char cubepos::corner_ori_inc[CUBIES],
              cubepos::corner_ori_dec[CUBIES],
              cubepos::corner_ori_neg_strip[CUBIES],
              cubepos::mod24[2 * CUBIES];

char cubepos::faces[FACES] = {'U', 'F', 'R', 'D', 'B', 'L'};

unsigned char cubepos::edge_trans[NMOVES][CUBIES],
              cubepos::corner_trans[NMOVES][CUBIES];

unsigned char cubepos::inv_move[NMOVES];

unsigned char cubepos::face_map[M][FACES], cubepos::move_map[M][NMOVES];
unsigned char cubepos::mm[M][M], cubepos::invm[M];
unsigned char cubepos::rot_edge[M][CUBIES], cubepos::rot_corner[M][CUBIES];

unsigned char cubepos::canon_seq[CANONSEQSTATES][NMOVES];
int cubepos::canon_seq_mask[CANONSEQSTATES];

static char static_buf[200];

// ============================================================================
// Edge and Corner Twist Permutations
// ============================================================================

// Which edges are affected by each face turn
static const unsigned char edge_twist_perm[FACES][4] = {
    {0, 2, 3, 1},    // U
    {3, 7, 11, 6},   // F
    {2, 5, 10, 7},   // R
    {9, 11, 10, 8},  // D
    {0, 4, 8, 5},    // B
    {1, 6, 9, 4}     // L
};

// Which corners are affected by each face turn
static const unsigned char corner_twist_perm[FACES][4] = {
    {0, 1, 3, 2},    // U
    {2, 3, 7, 6},    // F
    {3, 1, 5, 7},    // R
    {4, 6, 7, 5},    // D
    {1, 0, 4, 5},    // B
    {0, 2, 6, 4}     // L
};

// Edge orientation changes for each face (F and L flip edges)
static const unsigned char edge_change[FACES] = {0, 0, 1, 0, 0, 1};

// Corner orientation changes for each face and position
static const unsigned char corner_change[FACES][4] = {
    {0, 0, 0, 0},    // U - no orientation change
    {1, 2, 1, 2},    // F
    {1, 2, 1, 2},    // R
    {0, 0, 0, 0},    // D - no orientation change
    {1, 2, 1, 2},    // B
    {1, 2, 1, 2},    // L
};

// ============================================================================
// Singmaster Notation Lookup Tables
// ============================================================================

static const char* sing_solved = 
    "UF UR UB UL DF DR DB DL FR FL BR BL UFR URB UBL ULF DRF DFL DLB DBR";

static const char* const smedges[] = {
    "UB", "BU", "UL", "LU", "UR", "RU", "UF", "FU",
    "LB", "BL", "RB", "BR", "LF", "FL", "RF", "FR",
    "DB", "BD", "DL", "LD", "DR", "RD", "DF", "FD",
};

static const char* const smcorners[] = {
    "UBL", "URB", "ULF", "UFR", "DLB", "DBR", "DFL", "DRF",
    "LUB", "BUR", "FUL", "RUF", "BDL", "RDB", "LDF", "FDR",
    "BLU", "RBU", "LFU", "FRU", "LBD", "BRD", "FLD", "RFD",
    "ULB", "UBR", "UFL", "URF", "DBL", "DRB", "DLF", "DFR",
    "LBU", "BRU", "FLU", "RFU", "BLD", "RBD", "LFD", "FRD",
    "BUL", "RUB", "LUF", "FUR", "LDB", "BDR", "FDL", "RDF",
};

const int INVALID = 99;
static unsigned char lookup_edge_cubie[FACES * FACES];
static unsigned char lookup_corner_cubie[FACES * FACES * FACES];
static unsigned char sm_corner_order[8];
static unsigned char sm_edge_order[12];
static unsigned char sm_edge_flipped[12];

// ============================================================================
// Symmetry Map Tables
// ============================================================================

static const char* const axis_permute_map[] = 
    {"UFR", "URF", "FRU", "FUR", "RUF", "RFU"};
static const char* const axis_negate_map[] = 
    {"UFR", "UFL", "UBL", "UBR", "DBR", "DBL", "DFL", "DFR"};

// ============================================================================
// Helper Functions
// ============================================================================

static int parse_cubie(const char*& p) {
    cubepos::skip_whitespace(p);
    int v = 1;
    int f = 0;
    while ((f = cubepos::parse_face(p)) >= 0) {
        v = v * 6 + f;
        if (v >= 2 * 6 * 6 * 6)
            return -1;
    }
    return v;
}

static int parse_edge(const char*& p) {
    int c = parse_cubie(p);
    if (c < 6 * 6 || c >= 2 * 6 * 6)
        return -1;
    c = lookup_edge_cubie[c - 6 * 6];
    if (c == INVALID)
        return -1;
    return c;
}

static int parse_corner(const char*& p) {
    int c = parse_cubie(p);
    if (c < 6 * 6 * 6 || c >= 2 * 6 * 6 * 6)
        return -1;
    c = lookup_corner_cubie[c - 6 * 6 * 6];
    if (c == INVALID || c >= CUBIES)
        return -1;
    return c;
}

static void parse_corner_to_facemap(const char* p, unsigned char* a) {
    for (int i = 0; i < 3; i++) {
        int f = cubepos::parse_face(p[i]);
        a[i] = f;
        a[i + 3] = (f + 3) % FACES;
    }
}

static void face_map_multiply(unsigned char* a, unsigned char* b, unsigned char* c) {
    for (int i = 0; i < 6; i++)
        c[i] = b[a[i]];
}

// ============================================================================
// Initialization
// ============================================================================

void cubepos::init() {
    static int initialized = 0;
    if (initialized)
        return;
    initialized = 1;

    // Initialize corner orientation lookup tables
    for (int i = 0; i < CUBIES; i++) {
        int perm = corner_perm(i);
        int ori = corner_ori(i);
        corner_ori_inc[i] = corner_val(perm, (ori + 1) % 3);
        corner_ori_dec[i] = corner_val(perm, (ori + 2) % 3);
        corner_ori_neg_strip[i] = corner_val(0, (3 - ori) % 3);
        mod24[i] = mod24[i + CUBIES] = i;
    }

    // Initialize move transition tables
    for (int m = 0; m < NMOVES; m++)
        for (int c = 0; c < CUBIES; c++) {
            edge_trans[m][c] = c;
            corner_trans[m][c] = c;
        }

    // Build move transition tables for each face/twist combination
    for (int f = 0; f < FACES; f++)
        for (int t = 0; t < 3; t++) {
            int m = f * TWISTS + t;
            int isquarter = (t == 0 || t == 2);
            int perminc = t + 1;
            if (m < 0)
                continue;
            for (int i = 0; i < 4; i++) {
                int ii = (i + perminc) % 4;
                for (int o = 0; o < 2; o++) {
                    int oo = o;
                    if (isquarter)
                        oo ^= edge_change[f];
                    edge_trans[m][edge_val(edge_twist_perm[f][i], o)] = 
                        edge_val(edge_twist_perm[f][ii], oo);
                }
                for (int o = 0; o < 3; o++) {
                    int oo = o;
                    if (isquarter)
                        oo = (corner_change[f][i] + oo) % 3;
                    corner_trans[m][corner_val(corner_twist_perm[f][i], o)] = 
                        corner_val(corner_twist_perm[f][ii], oo);
                }
            }
        }

    // Initialize inverse move table
    for (int i = 0; i < NMOVES; i++)
        inv_move[i] = TWISTS * (i / TWISTS) + (NMOVES - i - 1) % TWISTS;

    // Initialize Singmaster notation lookup tables
    memset(lookup_edge_cubie, INVALID, sizeof(lookup_edge_cubie));
    memset(lookup_corner_cubie, INVALID, sizeof(lookup_corner_cubie));
    for (int i = 0; i < CUBIES; i++) {
        const char* tmp = 0;
        lookup_corner_cubie[parse_cubie(tmp = smcorners[i]) - 6 * 6 * 6] = i;
        lookup_corner_cubie[parse_cubie(tmp = smcorners[CUBIES + i]) - 6 * 6 * 6] = CUBIES + i;
        lookup_edge_cubie[parse_cubie(tmp = smedges[i]) - 6 * 6] = i;
    }
    const char* p = sing_solved;
    for (int i = 0; i < 12; i++) {
        int cv = parse_edge(p);
        sm_edge_order[i] = edge_perm(cv);
        sm_edge_flipped[i] = edge_ori(cv);
    }
    for (int i = 0; i < 8; i++)
        sm_corner_order[i] = corner_perm(parse_corner(p));

    // Initialize face maps for symmetry operations
    unsigned char face_to_m[FACES * FACES * FACES];
    for (int i = 0; i < 6; i++)
        parse_corner_to_facemap(axis_permute_map[i], face_map[8 * i]);
    for (int i = 0; i < 8; i++)
        parse_corner_to_facemap(axis_negate_map[i], face_map[i]);
    for (int i = 1; i < 6; i++)
        for (int j = 1; j < 8; j++)
            face_map_multiply(face_map[8 * i], face_map[j], face_map[8 * i + j]);

    // Build symmetry multiplication tables
    for (int i = 0; i < M; i++) {
        int v = face_map[i][0] * 36 + face_map[i][1] * 6 + face_map[i][2];
        face_to_m[v] = i;
    }
    unsigned char tfaces[6];
    for (int i = 0; i < M; i++)
        for (int j = 0; j < M; j++) {
            face_map_multiply(face_map[i], face_map[j], tfaces);
            int v = tfaces[0] * 36 + tfaces[1] * 6 + tfaces[2];
            mm[i][j] = face_to_m[v];
            if (mm[i][j] == 0)
                invm[i] = j;
        }
    for (int m = 0; m < M; m++) {
        int is_neg = (m ^ (m >> 3)) & 1;
        for (int f = 0; f < 6; f++) {
            for (int t = 0; t < TWISTS; t++) {
                if (is_neg)
                    move_map[m][f * TWISTS + t] = face_map[m][f] * TWISTS + TWISTS - 1 - t;
                else
                    move_map[m][f * TWISTS + t] = face_map[m][f] * TWISTS + t;
            }
        }
    }

    // Build rotation tables for edges and corners
    for (int m = 0; m < M; m++)
        for (int c = 0; c < CUBIES; c++) {
            int v = 0;
            for (int i = 0; i < 2; i++)
                v = 6 * v + face_map[m][parse_face(smedges[c][i])];
            rot_edge[m][c] = lookup_edge_cubie[v];
            v = 0;
            for (int i = 0; i < 3; i++)
                v = 6 * v + face_map[m][parse_face(smcorners[c][i])];
            rot_corner[m][c] = mod24[lookup_corner_cubie[v]];
        }

    // Initialize canonical sequence tables for move pruning
    for (int s = 0; s < CANONSEQSTATES; s++) {
        int prevface = (s - 1) % FACES;
        canon_seq_mask[s] = (1 << NMOVES) - 1;
        for (int mv = 0; mv < NMOVES; mv++) {
            int f = mv / TWISTS;
            int isplus = 0;
            if (s != 0 && (prevface == f || prevface == f + 3)) {
                canon_seq[s][mv] = INVALID;
                canon_seq_mask[s] &= ~(1 << mv);
            } else {
                canon_seq[s][mv] = f + 1 + FACES * isplus;
            }
        }
    }
}

// ============================================================================
// Constructor
// ============================================================================

cubepos::cubepos(int, int, int) {
    for (int i = 0; i < 8; i++)
        c[i] = corner_val(i, 0);
    for (int i = 0; i < 12; i++)
        e[i] = edge_val(i, 0);
    init();
}

// ============================================================================
// Move Application
// ============================================================================

void cubepos::move(int mov) {
    const unsigned char* p = corner_trans[mov];
    c[0] = p[c[0]]; c[1] = p[c[1]]; c[2] = p[c[2]]; c[3] = p[c[3]];
    c[4] = p[c[4]]; c[5] = p[c[5]]; c[6] = p[c[6]]; c[7] = p[c[7]];
    p = edge_trans[mov];
    e[0] = p[e[0]]; e[1] = p[e[1]]; e[2] = p[e[2]]; e[3] = p[e[3]];
    e[4] = p[e[4]]; e[5] = p[e[5]]; e[6] = p[e[6]]; e[7] = p[e[7]];
    e[8] = p[e[8]]; e[9] = p[e[9]]; e[10] = p[e[10]]; e[11] = p[e[11]];
}

// Move macros for movepc
#define ROT2(cc, a, b) { unsigned char t = cc[a]; cc[a] = cc[b]; cc[b] = t; }
#define ROT4(cc, a, b, c, d) { unsigned char t = cc[d]; cc[d] = cc[c]; cc[c] = cc[b]; cc[b] = cc[a]; cc[a] = t; }
#define ROT22(cc, a, b, c, d) ROT2(cc, a, c) ROT2(cc, b, d)
#define EDGE4FLIP(a, b, c, d) { unsigned char t = e[d]; e[d] = edge_flip(e[c]); \
    e[c] = edge_flip(e[b]); e[b] = edge_flip(e[a]); e[a] = edge_flip(t); }
#define CORNER4FLIP(a, b, cc, d) { unsigned char t = c[d]; c[d] = corner_ori_inc[c[cc]]; \
    c[cc] = corner_ori_dec[c[b]]; c[b] = corner_ori_inc[c[a]]; c[a] = corner_ori_dec[t]; }

void cubepos::movepc(int mov) {
    switch (mov) {
        case 0:  ROT4(e, 0, 2, 3, 1); ROT4(c, 0, 1, 3, 2); break;           // U
        case 1:  ROT22(e, 0, 2, 3, 1); ROT22(c, 0, 1, 3, 2); break;         // U2
        case 2:  ROT4(e, 1, 3, 2, 0); ROT4(c, 2, 3, 1, 0); break;           // U'
        case 3:  ROT4(e, 3, 7, 11, 6); CORNER4FLIP(3, 7, 6, 2); break;      // F
        case 4:  ROT22(e, 3, 7, 11, 6); ROT22(c, 2, 3, 7, 6); break;        // F2
        case 5:  ROT4(e, 6, 11, 7, 3); CORNER4FLIP(3, 2, 6, 7); break;      // F'
        case 6:  EDGE4FLIP(2, 5, 10, 7); CORNER4FLIP(1, 5, 7, 3); break;    // R
        case 7:  ROT22(e, 2, 5, 10, 7); ROT22(c, 3, 1, 5, 7); break;        // R2
        case 8:  EDGE4FLIP(7, 10, 5, 2); CORNER4FLIP(1, 3, 7, 5); break;    // R'
        case 9:  ROT4(e, 9, 11, 10, 8); ROT4(c, 4, 6, 7, 5); break;         // D
        case 10: ROT22(e, 9, 11, 10, 8); ROT22(c, 4, 6, 7, 5); break;       // D2
        case 11: ROT4(e, 8, 10, 11, 9); ROT4(c, 5, 7, 6, 4); break;         // D'
        case 12: ROT4(e, 0, 4, 8, 5); CORNER4FLIP(0, 4, 5, 1); break;       // B
        case 13: ROT22(e, 0, 4, 8, 5); ROT22(c, 1, 0, 4, 5); break;         // B2
        case 14: ROT4(e, 5, 8, 4, 0); CORNER4FLIP(0, 1, 5, 4); break;       // B'
        case 15: EDGE4FLIP(1, 6, 9, 4); CORNER4FLIP(2, 6, 4, 0); break;     // L
        case 16: ROT22(e, 1, 6, 9, 4); ROT22(c, 0, 2, 6, 4); break;         // L2
        case 17: EDGE4FLIP(4, 9, 6, 1); CORNER4FLIP(2, 0, 4, 6); break;     // L'
    }
}

// ============================================================================
// Inversion
// ============================================================================

void cubepos::invert_into(cubepos& dst) const {
    for (int i = 0; i < 8; i++) {
        int cval = c[i];
        dst.c[corner_perm(cval)] = corner_ori_sub(i, cval);
    }
    for (int i = 0; i < 12; i++) {
        int cval = e[i];
        dst.e[edge_perm(cval)] = edge_val(i, edge_ori(cval));
    }
}

moveseq cubepos::invert_sequence(const moveseq& seq) {
    unsigned int len = seq.size();
    moveseq r(len);
    for (unsigned int i = 0; i < len; i++)
        r[len - i - 1] = invert_move(seq[i]);
    return r;
}


// ============================================================================
// Parsing Functions
// ============================================================================

void cubepos::skip_whitespace(const char*& p) {
    while (*p && *p <= ' ')
        p++;
}

int cubepos::parse_face(const char*& p) {
    int f = parse_face(*p);
    if (f >= 0)
        p++;
    return f;
}

int cubepos::parse_face(char f) {
    switch (f) {
        case 'u': case 'U': return 0;
        case 'f': case 'F': return 1;
        case 'r': case 'R': return 2;
        case 'd': case 'D': return 3;
        case 'b': case 'B': return 4;
        case 'l': case 'L': return 5;
        default: return -1;
    }
}


void cubepos::append_move(char*& p, int mv) {
    append_face(p, mv / TWISTS);
    *p++ = "123"[mv % TWISTS];
    *p = 0;
}

void cubepos::append_moveseq(char*& p, const moveseq& seq) {
    *p = 0;
    for (unsigned int i = 0; i < seq.size(); i++)
        append_move(p, seq[i]);
}

char* cubepos::moveseq_string(const moveseq& seq) {
    if (seq.size() > 65)
        error("! can't print a move sequence that long");
    char* p = static_buf;
    append_moveseq(p, seq);
    return static_buf;
}

// ============================================================================
// Singmaster Notation
// ============================================================================

const char* cubepos::parse_Singmaster(const char* p) {
    int m = 0;
    for (int i = 0; i < 12; i++) {
        int c = parse_edge(p) ^ sm_edge_flipped[i];
        if (c < 0)
            return "No such edge";
        e[edge_perm(c)] = edge_val(sm_edge_order[i], edge_ori(c));
        m |= 1 << i;
    }
    for (int i = 0; i < 8; i++) {
        int cval = parse_corner(p);
        if (cval < 0)
            return "No such corner";
        c[corner_perm(cval)] = corner_ori_sub(sm_corner_order[i], cval);
        m |= 1 << (i + 12);
    }
    skip_whitespace(p);
    if (*p)
        return "Extra stuff after Singmaster representation";
    if (m != ((1 << 20) - 1))
        return "Missing at least one cubie";
    return 0;
}


// ============================================================================
// Symmetry Operations
// ============================================================================

void cubepos::remap_into(int m, cubepos& dst) const {
    int mprime = invm[m];
    for (int i = 0; i < 8; i++) {
        int c1 = rot_corner[mprime][i];
        int c2 = corner_ori_add(c[corner_perm(c1)], c1);
        dst.c[i] = rot_corner[m][c2];
    }
    for (int i = 0; i < 12; i++) {
        int c1 = rot_edge[mprime][i * 2];
        int c2 = edge_ori_add(e[edge_perm(c1)], c1);
        dst.e[i] = rot_edge[m][c2];
    }
}

// ============================================================================
// Utility Functions
// ============================================================================

void error(const char* s) {
    cerr << s << endl;
    if (*s == '!')
        exit(10);
}

int datahash(unsigned int* dat, int sz, int seed) {
    while (sz > 0) {
        sz -= 4;
        seed = 37 * seed + *dat++;
    }
    return seed;
}
