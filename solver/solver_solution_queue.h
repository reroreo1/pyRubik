#ifndef SOLVER_SOLUTION_QUEUE_H
#define SOLVER_SOLUTION_QUEUE_H

#include "cubepos.h"
#include <vector>

// Small POD type used to keep solutions in sequence order while
// multiple worker threads finish at different times.
struct Solution {
    cubepos cube;           // Original scrambled cube position
    int sequence_id;        // Monotonic input id (1, 2, 3, ...)
    long long phase2_probes;// Number of phase 2 nodes expanded
    moveseq moves;          // Solving move sequence
};

// Report a finished solution. This function is thread‑safe: it is
// responsible for ordering solutions by sequence_id and printing the
// move sequence for each solved cube exactly once.
void report_solution(const cubepos& cp,
                     int seq,
                     long long phase2probes,
                     const moveseq& sol);

#endif // SOLVER_SOLUTION_QUEUE_H
