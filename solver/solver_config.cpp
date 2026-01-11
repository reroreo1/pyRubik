#include "solver_config.h"

// Default configuration. These values reproduce the original behaviour
// from the monolithic twophase.cpp implementation.

const int verbose      = 0;   // Minimal output for Python integration
const int numthreads   = 8;   // Default 8 threads

const int target_length = 50;                 // Target solution length
const long long phase2limit = 0xffffffffffffffLL; // Phase 2 search limit
const int skipwrite   = 0;   // Do not suppress writing pruning tables
const int axesmask    = 63;  // Search all 6 axis/inversion orientations

pthread_mutex_t my_mutex;

void get_global_lock() {
    pthread_mutex_lock(&my_mutex);
}

void release_global_lock() {
    pthread_mutex_unlock(&my_mutex);
}
