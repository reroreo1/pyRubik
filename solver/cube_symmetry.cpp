#include "cube_symmetry.h"

#include <iostream>

using namespace std;

// ============================================================================
// Static Data Initialization for CubeSymmetry
// ============================================================================

lookup_type CubeSymmetry::cornermove[CORNERSYMM][NMOVES];
lookup_type CubeSymmetry::edgeomove[EDGEOSYMM][NMOVES];
lookup_type CubeSymmetry::edgepmove[EDGEPERM][NMOVES];
lookup_type CubeSymmetry::epsymm_compress[1 << 12];
lookup_type CubeSymmetry::epsymm_expand[EDGEOSYMM];
lookup_type CubeSymmetry::cornersymm_expand[CORNERRSYMM];
corner_mapinfo CubeSymmetry::cornersymm[CORNERSYMM];
lookup_type CubeSymmetry::edgeomap[EDGEOSYMM][CUBE_SYMM];
lookup_type CubeSymmetry::edgepmap[EDGEPERM][CUBE_SYMM];
lookup_type CubeSymmetry::edgepxor[EDGEPERM][2];

unsigned char permcube::s4inv[FACT4];
unsigned char permcube::s4mul[FACT4][FACT4];
unsigned char permcube::s4compress[256];
unsigned char permcube::s4expand[FACT4];
unsigned char permcube::c8_4_compact[256];
unsigned char permcube::c8_4_expand[C8_4];
unsigned char permcube::c8_4_parity[C8_4];
unsigned char permcube::c12_8[EDGEPERM];
lookup_type permcube::c8_12[C8_4];
unsigned short permcube::eperm_move[EDGEPERM][NMOVES];
int permcube::cperm_move[C8_4][NMOVES];

// ============================================================================
// Helper Functions
// ============================================================================

// Bit count (population count)
static int bc(int v) {
    int r = 0;
    while (v) {
        v &= v - 1;
        r++;
    }
    return r;
}

// Multiply two S4 permutations
static int muls4(int a, int b) {
    int r = 3 & (b >> (2 * (a & 3)));
    r += (3 & (b >> (2 * ((a >> 2) & 3)))) << 2;
    r += (3 & (b >> (2 * ((a >> 4) & 3)))) << 4;
    r += (3 & (b >> (2 * ((a >> 6) & 3)))) << 6;
    return r;
}

// ============================================================================
// CubeSymmetry Implementation
// ============================================================================

CubeSymmetry::CubeSymmetry(const cubepos& cp) {
    int c = 0, eo = 0, ep = 0;

    // Calculate corner orientation
    for (int i = 6; i >= 0; i--)
        c = 3 * c + cubepos::corner_ori(cp.c[i]);

    // Calculate edge orientation and permutation
    for (int i = 10; i >= 0; i--) {
        eo = 2 * eo + cubepos::edge_ori(cp.e[i]);
        ep = 2 * ep + (cp.e[i] & 8);
    }

    csymm = c;
    eosymm = eo;
    epsymm = epsymm_compress[ep >> 3];
}

void CubeSymmetry::set_coset(cubepos& cp) {
    int c = csymm, eo = eosymm, ep = epsymm_expand[epsymm];
    int s = 0;

    // Set corner orientations
    for (int i = 0; i < 7; i++) {
        int ori = c % 3;
        cp.c[i] = cubepos::corner_val(i, ori);
        s += ori;
        c = c / 3;
    }
    cp.c[7] = cubepos::corner_val(7, (8 * 3 - s) % 3);

    // Set edge orientations and positions
    s = 0;
    int nextmid = 4;
    int nextud = 0;
    for (int i = 0; i < 12; i++) {
        if (i == 11)
            eo = s;
        int ori = eo & 1;
        if (ep & 1)
            cp.e[i] = cubepos::edge_val(nextmid++, ori);
        else {
            cp.e[i] = cubepos::edge_val(nextud++, ori);
            if (nextud == 4)
                nextud = 8;
        }
        s ^= ori;
        eo >>= 1;
        ep >>= 1;
    }
}

void CubeSymmetry::canon_into(CubeSymmetry& kc) const {
    corner_mapinfo& cm = cornersymm[csymm];
    kc.csymm = cornersymm_expand[cm.csymm];
    kc.eosymm = edgeomap[edgepxor[epsymm][cm.minmap >> 3] ^ eosymm][cm.minmap];
    kc.epsymm = edgepmap[epsymm][cm.minmap];

    for (int m = cm.minmap + 1; cm.minbits >> m; m++)
        if ((cm.minbits >> m) & 1) {
            int neo = edgeomap[edgepxor[epsymm][m >> 3] ^ eosymm][m];
            if (neo > kc.eosymm)
                continue;
            int nep = edgepmap[epsymm][m];
            if (neo < kc.eosymm || nep < kc.epsymm) {
                kc.eosymm = neo;
                kc.epsymm = nep;
            }
        }
}

int CubeSymmetry::calc_symm() const {
    int r = 1;
    corner_mapinfo& cm = cornersymm[csymm];
    int teosymm = edgeomap[edgepxor[epsymm][cm.minmap >> 3] ^ eosymm][cm.minmap];
    int tepsymm = edgepmap[epsymm][cm.minmap];

    for (int m = cm.minmap + 1; cm.minbits >> m; m++)
        if (((cm.minbits >> m) & 1) &&
            edgeomap[edgepxor[epsymm][m >> 3] ^ eosymm][m] == teosymm &&
            edgepmap[epsymm][m] == tepsymm)
            r++;
    return r;
}

// ============================================================================
// CubeSymmetry Initialization
// ============================================================================

void CubeSymmetry::init() {
    static int initialized = 0;
    if (initialized)
        return;
    initialized = 1;

    // Initialize edge permutation compression table
    int c = 0;
    for (int i = 0; i < (1 << 12); i++)
        if (bc(i) == 4) {
            int rotval = ((i << 4) + (i >> 8)) & 0xfff;
            epsymm_compress[rotval] = c;
            epsymm_compress[rotval & 0x7ff] = c;
            epsymm_expand[c] = rotval;
            c++;
        }

    // Initialize move tables
    cubepos cp, cp2;
    for (int i = 0; i < CORNERSYMM; i++) {
        CubeSymmetry kc(i, i % EDGEOSYMM, i % EDGEPERM);
        kc.set_coset(cp);
        for (int mv = 0; mv < NMOVES; mv++) {
            cp2 = cp;
            cp2.movepc(mv);
            CubeSymmetry kc2(cp2);
            cornermove[i][mv] = kc2.csymm;
            if (i < EDGEOSYMM)
                edgeomove[i][mv] = kc2.eosymm;
            if (i < EDGEPERM)
                edgepmove[i][mv] = kc2.epsymm;
        }
    }

    // Initialize corner symmetry tables
    c = 0;
    for (int cs = 0; cs < CORNERSYMM; cs++) {
        int minval = cs;
        int lowm = 0;
        int lowbits = 1;
        CubeSymmetry kc(cs, 0, 0);
        for (int m = 1; m < CUBE_SYMM; m++) {
            kc.set_coset(cp);
            cp.remap_into(m, cp2);
            CubeSymmetry kc2(cp2);
            if (kc2.csymm < minval) {
                minval = kc2.csymm;
                lowbits = 1 << m;
                lowm = m;
            } else if (kc2.csymm == minval) {
                lowbits |= 1 << m;
            }
        }
        if (minval == cs) {
            cornersymm_expand[c] = minval;
            cornersymm[cs].csymm = c++;
        }
        cornersymm[cs].minbits = lowbits;
        cornersymm[cs].minmap = lowm;
        cornersymm[cs].csymm = cornersymm[minval].csymm;
    }
    if (c != CORNERRSYMM)
        error("! bad cornersym result");

    // Initialize edge mapping tables
    for (int ep = 0; ep < EDGEPERM; ep++) {
        CubeSymmetry kc(0, 0, ep);
        for (int m = 0; m < CUBE_SYMM; m++) {
            kc.set_coset(cp);
            cp.remap_into(m, cp2);
            CubeSymmetry kc2(cp2);
            edgepmap[ep][m] = kc2.epsymm;
            if (m == 8) {
                edgepxor[kc2.epsymm][0] = 0;
                edgepxor[kc2.epsymm][1] = kc2.eosymm;
            }
        }
    }
    for (int eo = 0; eo < EDGEOSYMM; eo++) {
        CubeSymmetry kc(0, eo, 0);
        for (int m = 0; m < CUBE_SYMM; m++) {
            kc.set_coset(cp);
            cp.remap_into(m, cp2);
            CubeSymmetry kc2(cp2);
            edgeomap[eo][m] = kc2.eosymm;
        }
    }

    permcube::init();
}

// ============================================================================
// permcube Implementation
// ============================================================================

permcube::permcube() {
    c8_4 = 0;
    ctp = cbp = 0;
    et = CubeSymmetry::epsymm_compress[0xf];
    em = 0;
    eb = CubeSymmetry::epsymm_compress[0xf00];
    etp = emp = ebp = 0;
}

permcube::permcube(const cubepos& cp) {
    init_edge_from_cp(cp);
    init_corner_from_cp(cp);
}

void permcube::init_edge_from_cp(const cubepos& cp) {
    et = em = eb = 0;
    etp = emp = ebp = 0;

    for (int i = 11; i >= 0; i--) {
        int perm = cubepos::edge_perm(cp.e[i]);
        if (perm & 4) {
            em |= 1 << i;
            emp = 4 * emp + (perm & 3);
        } else if (perm & 8) {
            eb |= 1 << i;
            ebp = 4 * ebp + (perm & 3);
        } else {
            et |= 1 << i;
            etp = 4 * etp + (perm & 3);
        }
    }

    et = CubeSymmetry::epsymm_compress[et];
    em = CubeSymmetry::epsymm_compress[em];
    eb = CubeSymmetry::epsymm_compress[eb];
    etp = s4compress[etp];
    emp = s4compress[emp];
    ebp = s4compress[ebp];
}

void permcube::init_corner_from_cp(const cubepos& cp) {
    c8_4 = 0;
    ctp = cbp = 0;

    for (int i = 7; i >= 0; i--) {
        int perm = cubepos::corner_perm(cp.c[i]);
        if (perm & 4) {
            cbp = 4 * cbp + (perm & 3);
        } else {
            c8_4 |= 1 << i;
            ctp = 4 * ctp + (perm & 3);
        }
    }

    c8_4 = c8_4_compact[c8_4];
    ctp = s4compress[ctp];
    cbp = s4compress[cbp];
}

void permcube::move(int mv) {
    int t = eperm_move[et][mv];
    et = t >> 5;
    etp = s4mul[etp][t & 31];
    t = eperm_move[em][mv];
    em = t >> 5;
    emp = s4mul[emp][t & 31];
    t = eperm_move[eb][mv];
    eb = t >> 5;
    ebp = s4mul[ebp][t & 31];
    t = cperm_move[c8_4][mv];
    c8_4 = t >> 10;
    ctp = s4mul[ctp][(t >> 5) & 31];
    cbp = s4mul[cbp][t & 31];
}

void permcube::set_edge_perm(cubepos& cp) const {
    int et_bits = CubeSymmetry::epsymm_expand[et];
    int em_bits = CubeSymmetry::epsymm_expand[em];
    int et_perm = s4expand[etp];
    int em_perm = s4expand[emp];
    int eb_perm = s4expand[ebp];

    for (int i = 0; i < 12; i++)
        if ((et_bits >> i) & 1) {
            cp.e[i] = cubepos::edge_val((3 & et_perm), cubepos::edge_ori(cp.e[i]));
            et_perm >>= 2;
        } else if ((em_bits >> i) & 1) {
            cp.e[i] = cubepos::edge_val((3 & em_perm) + 4, cubepos::edge_ori(cp.e[i]));
            em_perm >>= 2;
        } else {
            cp.e[i] = cubepos::edge_val((3 & eb_perm) + 8, cubepos::edge_ori(cp.e[i]));
            eb_perm >>= 2;
        }
}

void permcube::set_corner_perm(cubepos& cp) const {
    int c8_4_bits = c8_4_expand[c8_4];
    int ct_perm = s4expand[ctp];
    int cb_perm = s4expand[cbp];

    for (int i = 0; i < 8; i++)
        if ((c8_4_bits >> i) & 1) {
            cp.c[i] = cubepos::corner_val((3 & ct_perm), cubepos::corner_ori(cp.c[i]));
            ct_perm >>= 2;
        } else {
            cp.c[i] = cubepos::corner_val((3 & cb_perm) + 4, cubepos::corner_ori(cp.c[i]));
            cb_perm >>= 2;
        }
}

void permcube::set_perm(cubepos& cp) const {
    set_edge_perm(cp);
    set_corner_perm(cp);
}

// ============================================================================
// permcube Initialization
// ============================================================================

void permcube::init() {
    // Initialize S4 (symmetric group of 4 elements) tables
    int cc = 0;
    for (int a = 0; a < 4; a++)
        for (int b = 0; b < 4; b++) if (a != b)
            for (int c = 0; c < 4; c++) if (a != c && b != c) {
                int d = 0 + 1 + 2 + 3 - a - b - c;
                int coor = cc ^ ((cc >> 1) & 1);
                int expanded = (1 << (2 * b)) + (2 << (2 * c)) + (3 << (2 * d));
                s4compress[expanded] = coor;
                s4expand[coor] = expanded;
                cc++;
            }

    for (int i = 0; i < FACT4; i++)
        for (int j = 0; j < FACT4; j++) {
            int k = s4compress[muls4(s4expand[i], s4expand[j])];
            s4mul[j][i] = k;
            if (k == 0)
                s4inv[i] = j;
        }

    // Initialize C(8,4) combination tables
    int c = 0;
    for (int i = 0; i < 256; i++)
        if (bc(i) == 4) {
            int parity = 0;
            for (int j = 0; j < 8; j++)
                if (1 & (i >> j))
                    for (int k = 0; k < j; k++)
                        if (0 == (1 & (i >> k)))
                            parity++;
            c8_4_parity[c] = parity & 1;
            c8_4_compact[i] = c;
            c8_4_expand[c] = i;
            c++;
        }

    // Initialize c12_8 table
    for (int i = 0; i < EDGEPERM; i++) {
        int expbits = CubeSymmetry::epsymm_expand[i];
        if (expbits & 0x0f0)
            c12_8[i] = 255;
        else {
            int ii = c8_4_compact[(expbits >> 4) + (expbits & 15)];
            c12_8[i] = ii;
            c8_12[ii] = i;
        }
    }

    // Initialize edge permutation move table
    cubepos cp, cp2;
    for (int i = 0; i < EDGEPERM; i++) {
        permcube pc;
        pc.em = i;
        int remaining_edges = 0xfff - CubeSymmetry::epsymm_expand[i];
        int mask = 0;
        int bitsseen = 0;
        while (bitsseen < 4) {
            if (remaining_edges & (mask + 1))
                bitsseen++;
            mask = 2 * mask + 1;
        }
        pc.et = CubeSymmetry::epsymm_compress[remaining_edges & mask];
        pc.eb = CubeSymmetry::epsymm_compress[remaining_edges & ~mask];
        pc.set_perm(cp);
        for (int mv = 0; mv < NMOVES; mv++) {
            cp2 = cp;
            cp2.movepc(mv);
            permcube pc2(cp2);
            eperm_move[i][mv] = (pc2.em << 5) + pc2.emp;
        }
    }

    // Initialize corner permutation move table
    for (int i = 0; i < C8_4; i++) {
        permcube pc;
        pc.c8_4 = i;
        pc.set_perm(cp);
        for (int mv = 0; mv < NMOVES; mv++) {
            cp2 = cp;
            cp2.movepc(mv);
            permcube pc2(cp2);
            cperm_move[i][mv] = (pc2.c8_4 << 10) + (pc2.ctp << 5) + pc2.cbp;
        }
    }
}
