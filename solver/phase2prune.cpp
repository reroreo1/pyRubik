#include "phase2prune.h"
#include <iostream>
#include <cstdio>

using namespace std;

// ============================================================================
// Static Data
// ============================================================================

struct corner_reduce {
    unsigned char m, parity;
    lookup_type c, minbits;
};

static corner_reduce corner_reduction[FACT8];
static lookup_type edgeud_remap[CUBE_SYMM][FACT8];

int phase2prune::cornermax;
unsigned int phase2prune::memsize;
unsigned int* phase2prune::mem;
const char* const phase2prune::filename = "p2p1h.dat";
int phase2prune::file_checksum;

// ============================================================================
// Helper Functions
// ============================================================================

inline int corner_coordinate(const permcube& pc) {
    return (pc.c8_4 * FACT4 + pc.ctp) * FACT4 + pc.cbp;
}

inline int edge_coordinate(const permcube& pc) {
    return (permcube::c12_8[pc.et] * FACT4 + pc.etp) * FACT4 + pc.ebp;
}

static int datahash(unsigned int* dat, int sz, int seed) {
    while (sz > 0) {
        sz -= 4;
        seed = 37 * seed + *dat++;
    }
    return seed;
}

// ============================================================================
// Lookup Functions
// ============================================================================

int phase2prune::lookup(const cubepos& cp) {
    permcube pc(cp);
    return lookup(pc);
}

int phase2prune::lookup(const permcube& pc) {
    int cc = corner_coordinate(pc);
    corner_reduce& cr = corner_reduction[cc];
    int off = cr.c * FACT8 + edgeud_remap[cr.m][edge_coordinate(pc)];
    int r = (mem[off >> 3] >> (4 * (off & 7))) & 0xf;
    if (r == 0 && pc == identity_pc)
        return 0;
    else
        return r + 1;
}

// ============================================================================
// Table Generation
// ============================================================================

void phase2prune::gen_table() {
    memset(mem, 255, memsize);
    cout << "Gen phase2" << flush;
    mem[0] &= ~14;
    int seen = 1;
    
    for (int d = 0; d < 15; d++) {
        unsigned int seek = (d ? d - 1 : 1);
        int newval = d;
        
        for (int c8_4 = 0; c8_4 < C8_4; c8_4++)
            for (int ctp = 0; ctp < FACT4; ctp++)
                for (int cbp = 0; cbp < FACT4; cbp++) {
                    permcube pc;
                    pc.c8_4 = c8_4;
                    pc.ctp = ctp;
                    pc.cbp = cbp;
                    int oc = corner_coordinate(pc);
                    corner_reduce& cr = corner_reduction[oc];
                    
                    if (cr.minbits & 1) {
                        permcube pc2, pc3, pc4;
                        cubepos cp2, cp3;
                        int off = corner_reduction[oc].c * (FACT8 / 8);
                        
                        for (int mv = 0; mv < NMOVES; mv++) {
                            if (!CubeSymmetry::in_Kociemba_group(mv))
                                continue;
                            pc2 = pc;
                            pc2.move(mv);
                            int dest_off = corner_coordinate(pc2);
                            corner_reduce& cr2 = corner_reduction[dest_off];
                            int destat = cr2.c * (FACT8 / 8);
                            
                            for (int m = cr2.m; (1 << m) <= cr2.minbits; m++)
                                if ((cr2.minbits >> m) & 1) {
                                    int at = 0;
                                    for (int e8_4 = 0; e8_4 < C8_4; e8_4++) {
                                        int et = permcube::c8_12[e8_4];
                                        int t1 = permcube::eperm_move[et][mv];
                                        int eb = CubeSymmetry::epsymm_compress[0xf0f - CubeSymmetry::epsymm_expand[et]];
                                        int t2 = permcube::eperm_move[eb][mv] & 31;
                                        int dst1 = permcube::c12_8[t1 >> 5] * 24 * 24;
                                        t1 &= 31;
                                        
                                        for (int etp = 0; etp < FACT4; etp++)
                                            for (int ebp = 0; ebp < FACT4; ebp++, at++) {
                                                if (mem[off + (at >> 3)] == 0xffffffff) {
                                                    ebp += 7;
                                                    at += 7;
                                                } else if (((mem[off + (at >> 3)] >> (4 * (at & 7))) & 0xf) == seek) {
                                                    int etp1 = permcube::s4mul[etp][t1];
                                                    int ebp1 = permcube::s4mul[ebp][t2];
                                                    int dat = edgeud_remap[m][dst1 + etp1 * 24 + ebp1];
                                                    int val = (mem[destat + (dat >> 3)] >> (4 * (dat & 7))) & 0xf;
                                                    if (val == 0xf) {
                                                        mem[destat + (dat >> 3)] -= (0xf - newval) << (4 * (dat & 7));
                                                        seen++;
                                                    }
                                                }
                                            }
                                    }
                                }
                        }
                    }
                }
        
        if (d == 0)
            mem[0] &= ~15;
        cout << " " << d << flush;
    }
    
    cout << " done." << endl << flush;
}

// ============================================================================
// Table I/O
// ============================================================================

const int CHUNKSIZE = 65536;

int phase2prune::read_table() {
    FILE* f = fopen(filename, "rb");
    if (f == 0)
        return 0;
    
    int togo = memsize;
    unsigned int* p = mem;
    int seed = 0;
    
    while (togo > 0) {
        unsigned int siz = (togo > CHUNKSIZE ? CHUNKSIZE : togo);
        if (fread(p, 1, siz, f) != siz) {
            cerr << "Out of data in " << filename << endl;
            fclose(f);
            return 0;
        }
        seed = datahash(p, siz, seed);
        togo -= siz;
        p += siz / sizeof(unsigned int);
    }
    
    if (fread(&file_checksum, sizeof(int), 1, f) != 1) {
        cerr << "Out of data in " << filename << endl;
        fclose(f);
        return 0;
    }
    fclose(f);
    
    if (file_checksum != seed) {
        cerr << "Bad checksum in " << filename << "; expected "
             << file_checksum << " but saw " << seed << endl;
        return 0;
    }
    return 1;
}

void phase2prune::write_table() {
    FILE* f = fopen(filename, "wb");
    if (f == 0)
        error("! cannot write pruning file to current directory");
    if (fwrite(mem, 1, memsize, f) != memsize)
        error("! error writing pruning table");
    if (fwrite(&file_checksum, sizeof(int), 1, f) != 1)
        error("! error writing pruning table");
    fclose(f);
}

void phase2prune::check_integrity() {
    if (file_checksum != datahash(mem, memsize, 0))
        error("! integrity of pruning table compromised");
    cout << "Verified integrity of phase two pruning data: "
         << file_checksum << endl;
}

// ============================================================================
// Solving
// ============================================================================

int phase2prune::solve(const permcube& pc, int togo, int canonstate, moveseq& seq) {
    int d = lookup(pc);
    if (d > togo + 1)
        return -1;
    if (pc == identity_pc)
        return 0;
    if (togo < 1)
        return -1;
    
    togo--;
    permcube pc2;
    int mask = cubepos::cs_mask(canonstate);
    
    for (int mv = 0; mv < NMOVES; mv++) {
        if (!CubeSymmetry::in_Kociemba_group(mv))
            continue;
        if (0 == ((mask >> mv) & 1))
            continue;
        pc2 = pc;
        pc2.move(mv);
        if (solve(pc2, togo, cubepos::next_cs(canonstate, mv), seq) >= 0) {
            seq.push_back(mv);
            return 1;
        }
    }
    return -1;
}

moveseq phase2prune::solve(const permcube& pc, int maxlen) {
    moveseq r;
    for (int d = lookup(pc); d <= maxlen; d++)
        if (solve(pc, d, CANONSEQSTART, r) >= 0)
            break;
    reverse(r.begin(), r.end());
    return r;
}

// ============================================================================
// Initialization
// ============================================================================

void phase2prune::init(int suppress_writing) {
    static int initialized = 0;
    if (initialized)
        return;
    initialized = 1;
    
    CubeSymmetry::init();
    
    // Initialize corner reduction table
    cubepos cp, cp2;
    int cornercount = 0;
    
    for (int c8_4 = 0; c8_4 < C8_4; c8_4++)
        for (int ctp = 0; ctp < FACT4; ctp++)
            for (int cbp = 0; cbp < FACT4; cbp++) {
                permcube pc;
                pc.c8_4 = c8_4;
                pc.ctp = ctp;
                pc.cbp = cbp;
                pc.set_perm(cp);
                int minm = 0;
                cubepos mincp = cp;
                int minbits = 1;
                
                for (int m = 1; m < CUBE_SYMM; m++) {
                    cp.remap_into(m, cp2);
                    if (cp2 < mincp) {
                        mincp = cp2;
                        minm = m;
                        minbits = 1 << m;
                    } else if (cp2 == mincp) {
                        minbits |= 1 << m;
                    }
                }
                
                int off = corner_coordinate(pc);
                corner_reduction[off].m = minm;
                corner_reduction[off].parity = permcube::c8_4_parity[c8_4] ^
                                               (permcube::s4mul[ctp][cbp] & 1);
                corner_reduction[off].minbits = minbits;
                
                if (minm == 0) {
                    corner_reduction[off].c = cornercount;
                    cornercount++;
                }
            }
    
    // Set corner indices for non-minimal positions
    for (int c8_4 = 0; c8_4 < C8_4; c8_4++)
        for (int ctp = 0; ctp < FACT4; ctp++)
            for (int cbp = 0; cbp < FACT4; cbp++) {
                permcube pc;
                pc.c8_4 = c8_4;
                pc.ctp = ctp;
                pc.cbp = cbp;
                int off = corner_coordinate(pc);
                corner_reduce& cr = corner_reduction[off];
                if (cr.m != 0) {
                    pc.set_perm(cp);
                    cp.remap_into(cr.m, cp2);
                    permcube pc2(cp2);
                    cr.c = corner_reduction[corner_coordinate(pc2)].c;
                }
            }
    
    cornermax = cornercount;
    
    // Initialize edge remapping table
    for (int m = 0; m < CUBE_SYMM; m++) {
        for (int e8_4 = 0; e8_4 < C8_4; e8_4++)
            for (int etp = 0; etp < FACT4; etp++)
                for (int ebp = 0; ebp < FACT4; ebp++) {
                    permcube pc;
                    pc.et = permcube::c8_12[e8_4];
                    pc.eb = CubeSymmetry::epsymm_compress[0xf0f - CubeSymmetry::epsymm_expand[pc.et]];
                    pc.etp = etp;
                    pc.ebp = ebp;
                    pc.set_perm(cp);
                    cp.remap_into(m, cp2);
                    permcube pc2(cp2);
                    int dat = permcube::c12_8[pc2.et] * FACT4 * FACT4 +
                              pc2.etp * FACT4 + pc2.ebp;
                    edgeud_remap[m][e8_4 * FACT4 * FACT4 + etp * FACT4 + ebp] = dat;
                }
    }
    
    // Allocate and load/generate pruning table
    memsize = cornermax * FACT8 / 2;
    mem = new unsigned int[(memsize + 3) / 4];
    
    if (!read_table()) {
        gen_table();
        file_checksum = datahash(mem, memsize, 0);
        if (!suppress_writing)
            write_table();
    }
}
