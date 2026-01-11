#include "solver_solution_queue.h"
#include "solver_config.h"

#include <iostream>
#include <map>

using namespace std;

// Global bookkeeping for solutions. All access is serialized via
// the global mutex declared in solver_config.

static map<int, Solution> g_queue;   // Out‑of‑order solutions from worker threads
static int g_next_sequence = 1;      // Next sequence id expected on output
static int g_missed_target = 0;      // Number of solutions longer than target_length
static int g_solved = 0;             // Total number of solved positions
static long long g_phase2total = 0;  // Cumulative phase 2 node count

// Print a single solution. Only the move sequence is printed to keep
// the interface simple for the Python caller.
static void display_solution(const cubepos& cp,
                             int seq,
                             long long phase2probes,
                             const moveseq& sol) {
    (void)cp;   // The cube itself is not printed, only its solution
    (void)seq;  // Sequence id is used only for ordering

    g_phase2total += phase2probes;
    cout << cubepos::moveseq_string(sol) << endl;
}

void report_solution(const cubepos& cp,
                     int seq,
                     long long phase2probes,
                     const moveseq& sol) {
    get_global_lock();

    g_solved++;
    if (!sol.empty() && static_cast<int>(sol.size()) > target_length && target_length) {
        g_missed_target++;
    }

    // If this solution is the next one in sequence, print it immediately
    // and flush any queued later solutions that can now be emitted.
    if (seq == g_next_sequence) {
        display_solution(cp, seq, phase2probes, sol);
        ++g_next_sequence;

        while (true) {
            map<int, Solution>::iterator it = g_queue.find(g_next_sequence);
            if (it == g_queue.end()) {
                break;
            }
            Solution& s = it->second;
            display_solution(s.cube, s.sequence_id, s.phase2_probes, s.moves);
            g_queue.erase(it);
            ++g_next_sequence;
        }
    } else {
        // Otherwise, remember this solution until all earlier ones finish.
        Solution stored;
        stored.cube = cp;
        stored.sequence_id = seq;
        stored.phase2_probes = phase2probes;
        stored.moves = sol;
        g_queue[seq] = stored;
    }

    release_global_lock();
}
