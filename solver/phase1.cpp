#include "phase1.h"
#include <iostream>
#include <cstdio>

using namespace std;

unsigned int phase1::memsize;
unsigned char* phase1::mem;
int phase1::file_checksum;
const char* const phase1::filename = "data1.dat";

static unsigned char map_phase1_offsets[CUBE_SYMM][3];
static int map_phase1_table[2][12][256];

static int datahash(unsigned int* dat, int sz, int seed) {
    while (sz > 0) {
        sz -= 4;
        seed = 37 * seed + *dat++;
    }
    return seed;
}

void phase1::gen_table() {
    memset(mem, -1, memsize);
    mem[0] = 0;
    int seen = 1;

    cout << "Gen phase1" << flush;

    for (int d = 1; ; d++) {
        int lastiter = (seen == CORNERRSYMM * EDGEOSYMM * EDGEPERM);
        int seek = d - 1;
        int at = 0;

        for (int cs = 0; cs < CORNERRSYMM; cs++) {
            int csymm = CubeSymmetry::cornersymm_expand[cs];
            for (int eosymm = 0; eosymm < EDGEOSYMM; eosymm++)
                for (int epsymm = 0; epsymm < EDGEPERM; epsymm++, at += BYTES_PER_ENTRY)
                    if (mem[at] == seek) {
                        int deltadist[NMOVES];
                        for (int mv = 0; mv < NMOVES; mv++) {
                            int rd = 0;
                            CubeSymmetry kc(csymm, eosymm, epsymm);
                            kc.move(mv);
                            corner_mapinfo& cm = CubeSymmetry::cornersymm[kc.csymm];
                            for (int m = cm.minmap; cm.minbits >> m; m++)
                                if ((cm.minbits >> m) & 1) {
                                    int deosymm = CubeSymmetry::edgeomap[CubeSymmetry::edgepxor[kc.epsymm][m >> 3] ^ kc.eosymm][m];
                                    int depsymm = CubeSymmetry::edgepmap[kc.epsymm][m];
                                    int dat = ((cm.csymm * EDGEOSYMM + deosymm) * EDGEPERM + depsymm) * BYTES_PER_ENTRY;
                                    rd = mem[dat];
                                    if (rd == 255) {
                                        rd = d;
                                        mem[dat] = rd;
                                        seen++;
                                    }
                                }
                            deltadist[mv] = rd - seek;
                        }

                        for (int b = 0; b < 3; b++) {
                            int v = 0;
                            int clim = 1;
                            for (int c = clim; c >= 0; c--) {
                                int vv = 0;
                                int cnts[3];
                                cnts[0] = cnts[1] = cnts[2] = 0;
                                for (int t = 2; t >= 0; t--) {
                                    vv = 2 * vv + deltadist[3 * b + 9 * c + t];
                                    cnts[1 + deltadist[3 * b + 9 * c + t]]++;
                                }
                                if (cnts[0] > 0 && cnts[2] > 0)
                                    error("! bad delta distance values within one face turn set");
                                if (cnts[0])
                                    vv += 7;
                                else
                                    vv += 8;
                                v = 16 * v + vv;
                            }
                            mem[at + b + 1] = v;
                        }
                    }
        }

        cout << " " << d << flush;
        if (lastiter)
            break;
    }

    cout << " done." << endl << flush;
}

const int PHASE1_CHUNKSIZE = 65536;

int phase1::read_table() {
    FILE* f = fopen(filename, "rb");
    if (f == 0)
        return 0;

    int togo = memsize;
    unsigned char* p = mem;
    int seed = 0;

    while (togo > 0) {
        unsigned int siz = (togo > PHASE1_CHUNKSIZE ? PHASE1_CHUNKSIZE : togo);
        if (fread(p, 1, siz, f) != siz) {
            cerr << "Out of data in " << filename << endl;
            fclose(f);
            return 0;
        }
        seed = datahash((unsigned int*)p, siz, seed);
        togo -= siz;
        p += siz;
    }

    if (fread(&file_checksum, sizeof(int), 1, f) != 1) {
        cerr << "Out of data in " << filename << endl;
        fclose(f);
        return 0;
    }
    fclose(f);

    if (file_checksum != datahash((unsigned int*)mem, memsize, 0)) {
        cerr << "Bad checksum in " << filename << endl;
        return 0;
    }
    return 1;
}

void phase1::write_table() {
    FILE* f = fopen(filename, "wb");
    if (f == 0)
        error("! cannot write pruning file to current directory");
    if (fwrite(mem, 1, memsize, f) != memsize)
        error("! error writing pruning table");
    if (fwrite(&file_checksum, sizeof(int), 1, f) != 1)
        error("! error writing pruning table");
    fclose(f);
}

void phase1::check_integrity() {
    if (file_checksum != datahash((unsigned int*)mem, memsize, 0))
        error("! integrity of pruning table compromised");
    cout << "Verified integrity of phase one pruning data: "
         << file_checksum << endl;
}

int phase1::lookup(const CubeSymmetry& kc) {
    corner_mapinfo& cm = CubeSymmetry::cornersymm[kc.csymm];
    int m = cm.minmap;
    int r = mem[BYTES_PER_ENTRY * (((cm.csymm * EDGEOSYMM) +
            CubeSymmetry::edgeomap[CubeSymmetry::edgepxor[kc.epsymm][m >> 3] ^ kc.eosymm][m]) * 495 +
            CubeSymmetry::edgepmap[kc.epsymm][m])];
    return r;
}

int phase1::lookup(const CubeSymmetry& kc, int togo, int& nextmovemask) {
    corner_mapinfo& cm = CubeSymmetry::cornersymm[kc.csymm];
    int m = cm.minmap;
    int off = BYTES_PER_ENTRY * (((cm.csymm * EDGEOSYMM) +
              CubeSymmetry::edgeomap[CubeSymmetry::edgepxor[kc.epsymm][m >> 3] ^ kc.eosymm][m]) * EDGEPERM +
              CubeSymmetry::edgepmap[kc.epsymm][m]);
    int r = mem[off];

    if (togo > 0) {
        nextmovemask = 0;
        for (int b = 0; b < 3; b++) {
            int v = mem[off + 1 + b];
            for (int c = 0; c < 2; c++) {
                int vv = v & 15;
                v >>= 4;
                int inc = vv >= 8;
                vv = (vv - 8) & 7;
                for (int t = 0; t < 3; t++) {
                    int thisv = (inc ? 1 : -1) * (vv & 1);
                    vv >>= 1;
                    if (r + thisv <= togo)
                        nextmovemask |= 1 << (3 * b + 9 * c + t);
                }
            }
        }
    }
    return r;
}

int phase1::lookup(const CubeSymmetry& kc, int& mask) {
    corner_mapinfo& cm = CubeSymmetry::cornersymm[kc.csymm];
    int m = cm.minmap;
    int off = BYTES_PER_ENTRY * (((cm.csymm * EDGEOSYMM) +
              CubeSymmetry::edgeomap[CubeSymmetry::edgepxor[kc.epsymm][m >> 3] ^ kc.eosymm][m]) * EDGEPERM +
              CubeSymmetry::edgepmap[kc.epsymm][m]);

    mask = 0;
    for (int b = 0; b < 3; b++) {
        int v = mem[off + 1 + b];
        for (int c = 0; c < 2; c++) {
            int vv = v & 15;
            v >>= 4;
            int inc = vv >= 8;
            vv = (vv - 8) & 7;
            for (int t = 0; t < 3; t++) {
                int thisv = (inc ? 1 : -1) * (vv & 1);
                vv >>= 1;
                if (thisv <= 0)
                    mask |= 1 << (3 * b + 9 * c + t);
            }
        }
    }
    return mem[off];
}

moveseq phase1::solve(CubeSymmetry kc) {
    moveseq r;
    int mask;
    int d = lookup(kc, mask);

    while (d > 0) {
        for (int mv = 0; mv < NMOVES; mv++) {
            if ((mask >> mv) & 1) {
                CubeSymmetry kc2 = kc;
                kc2.move(mv);
                int nd = lookup(kc2, mask);
                if (nd < d) {
                    r.push_back(mv);
                    kc = kc2;
                    d = nd;
                    break;
                }
            }
        }
    }
    return r;
}

void phase1::init(int suppress_writing) {
    static int initialized = 0;
    if (initialized)
        return;
    initialized = 1;

    CubeSymmetry::init();

    memsize = BYTES_PER_ENTRY * CORNERRSYMM * EDGEOSYMM * EDGEPERM;
    mem = new unsigned char[memsize];

    if (!read_table()) {
        gen_table();
        file_checksum = datahash((unsigned int*)mem, memsize, 0);
        if (!suppress_writing)
            write_table();
    }

    for (int m = 0; m < CUBE_SYMM; m++) {
        for (int b = 0; b < 3; b++) {
            int mv = 3 * b;
            CubeSymmetry kc(0, 0, 0);
            kc.move(mv);
            corner_mapinfo& cm = CubeSymmetry::cornersymm[kc.csymm];
            int mz = cm.minmap ^ m;
            map_phase1_offsets[m][b] = mz;
        }
    }

    for (int inv = 0; inv < 2; inv++)
        for (int b = 0; b < 6; b++)
            for (int v = 0; v < 256; v++) {
                int r = 0;
                for (int c = 0; c < 2; c++) {
                    int vv = (v >> (4 * c)) & 15;
                    int inc = vv >= 8;
                    vv = (vv - 8) & 7;
                    for (int t = 0; t < 3; t++) {
                        int thisv = (inc ? 1 : -1) * (vv & 1);
                        vv >>= 1;
                        if ((inv == 0 && thisv <= 0) || (inv && thisv >= 0))
                            r |= 1 << (3 * (b % 3) + 9 * c + t);
                    }
                }
                map_phase1_table[inv][b][v] = r;
            }
}
