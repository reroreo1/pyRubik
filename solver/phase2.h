#ifndef PHASE2_H
#define PHASE2_H

#include "cube_symmetry.h"

// 8! permutations
const int FACT8 = 40320;

// Phase 2 pruning table manager.
// Provides lookup and solving functionality for phase 2.
class phase2 {
public:
    static void init(int suppress_writing = 0);

    static int lookup(const cubepos& cp);
    static int lookup(const permcube& pc);

    static moveseq solve(const permcube& pc, int maxlen = 30);
    static moveseq solve(const cubepos& cp, int maxlen = 30) {
        permcube pc(cp);
        return solve(pc, maxlen);
    }
    static int solve(const permcube& pc, int togo, int canonstate, moveseq& seq);

    static void gen_table();
    static int read_table();
    static void write_table();
    static void check_integrity();

    static int cornermax;
    static unsigned int memsize;
    static unsigned int* mem;
    static const char* const filename;
    static int file_checksum;
};

#endif
