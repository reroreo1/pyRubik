#ifndef PHASE1PRUNE_H
#define PHASE1PRUNE_H

#include "kocsymm.h"

// Bytes per pruning table entry
const int BYTES_PER_ENTRY = 4;

/**
 * Phase 1 pruning table manager.
 * Provides lookup and solving functionality for phase 1.
 */
class phase1prune {
public:
    // ========================================================================
    // Initialization
    // ========================================================================
    
    static void init(int suppress_writing = 0);

    // ========================================================================
    // Lookup Functions
    // ========================================================================
    
    static int lookup(const kocsymm& kc, int& mask);
    static int lookup(const kocsymm& kc);
    static int lookup(const kocsymm& kc, int togo, int& nextmovemask);

    // ========================================================================
    // Solving
    // ========================================================================
    
    static moveseq solve(kocsymm kc);

    // ========================================================================
    // Table Management
    // ========================================================================
    
    static void gen_table();
    static int read_table();
    static void write_table();
    static void check_integrity();

    // ========================================================================
    // Static Data
    // ========================================================================
    
    static unsigned int memsize;
    static unsigned char* mem;
    static int file_checksum;
    static const char* const filename;
};

#endif
