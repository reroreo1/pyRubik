#include "twophase_solver.h"
#include "phase1.h"
#include "phase2.h"

#include <pthread.h>

// Entry point for the twophase binary.
// Responsibilities:
//   * Initialise pruning tables
//   * Set up the global mutex
//   * Start worker threads and join them on exit

int main() {
    // Build or load pruning tables for both phases.
    phase1::init(skipwrite);
    phase2::init(skipwrite);

    // Global mutex used around stdin and solution output.
    pthread_mutex_init(&my_mutex, NULL);

    // Launch worker threads. Thread 0 runs on the main thread so that
    // the process can still make progress even if thread creation fails.
    pthread_t p_thread[MAX_THREADS];

    for (int ti = 1; ti < numthreads; ++ti) {
        pthread_create(&p_thread[ti], NULL, TwophaseSolver::worker_entry, solvers + ti);
    }

    solvers[0].dowork();

    for (int ti = 1; ti < numthreads; ++ti) {
        pthread_join(p_thread[ti], 0);
    }

    return 0;
}
