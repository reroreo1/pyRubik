#ifndef SOLVER_CONFIG_H
#define SOLVER_CONFIG_H

#include <pthread.h>

// Global configuration values for the twophase solver.
// These are kept in a single place so it is easy to see and
// adjust high-level limits and threading parameters.

extern const int verbose;        // Verbosity level (kept low for Python integration)
extern const int numthreads;     // Number of worker threads

// These symbolic constants are used for static array sizes and therefore
// must be compile-time constants visible to every translation unit.
// They are defined as macros instead of variables for that reason.
#define MAX_THREADS 32           // Upper bound for worker array
#define MAX_MOVES   50           // Hard upper bound on move count

extern const int target_length;  // Target maximum solution length
extern const long long phase2limit; // Limit on phase 2 node expansions
extern const int skipwrite;      // If non‑zero, do not write pruning tables to disk
extern const int axesmask;       // Mask controlling which cube orientations are searched

// Global mutex protecting stdin reads and solution output ordering.
extern pthread_mutex_t my_mutex;

// Acquire and release the global mutex.
void get_global_lock();
void release_global_lock();

#endif // SOLVER_CONFIG_H
