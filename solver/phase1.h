#ifndef PHASE1_H
#define PHASE1_H

#include "cube_symmetry.h"

// Bytes per pruning table entry
const int BYTES_PER_ENTRY = 4;

// Phase 1 pruning table manager.
// Provides lookup and solving functionality for phase 1.
class phase1 {
public:
    static void init(int suppress_writing = 0);

    static int lookup(const CubeSymmetry& kc, int& mask);
    static int lookup(const CubeSymmetry& kc);
    static int lookup(const CubeSymmetry& kc, int togo, int& nextmovemask);

    static moveseq solve(CubeSymmetry kc);

    static void gen_table();
    static int read_table();
    static void write_table();
    static void check_integrity();

    static unsigned int memsize;
    static unsigned char* mem;
    static int file_checksum;
    static const char* const filename;
};

#endif
