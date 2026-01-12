#include "phase1.h"
#include "phase2.h"
#include <pthread.h>
#include <iostream>
#include <map>
#include <cstdio>

using namespace std;

// ============================================================================
// Global Configuration
// ============================================================================

const int verbose = 0;  // Minimal output for Python integration
const int numthreads = 8;  // Default 8 threads
const int MAX_THREADS = 32;
const int MAX_MOVES = 50;  // Default 50 moves max

const int target_length = 50;  // Default target length
const long long phase2limit = 0xffffffffffffffLL;
long long phase2total = 0LL;
const int skipwrite = 0;
const int axesmask = 63;

pthread_mutex_t my_mutex;

// ============================================================================
// Thread Synchronization
// ============================================================================

void get_global_lock() {
    pthread_mutex_lock(&my_mutex);
}

void release_global_lock() {
    pthread_mutex_unlock(&my_mutex);
}

// ============================================================================
// Solution Queue
// ============================================================================

class solution {
public:
    solution(const cubepos& cparg, int seqarg, long long p2parg, moveseq& solarg) {
        cp = cparg;
        seq = seqarg;
        phase2probes = p2parg;
        moves = solarg;
    }
    solution() {}
    
    cubepos cp;
    int seq;
    long long phase2probes;
    moveseq moves;
};

map<int, solution> queue;
int next_sequence = 1;
int missed_target = 0;
int solved = 0;

// ============================================================================
// Output Functions
// ============================================================================

void display(const cubepos& cp, int seq, long long phase2probes, moveseq sol) {
    phase2total += phase2probes;
    // Only output the solution moves for Python to parse
    cout << cubepos::moveseq_string(sol) << endl;
}

void report(const cubepos& cp, int seq, long long phase2probes, moveseq sol) {
    get_global_lock();
    solved++;
    if ((int)sol.size() > target_length && target_length)
        missed_target++;
    if (seq == next_sequence) {
        display(cp, seq, phase2probes, sol);
        next_sequence++;
        while (queue.find(next_sequence) != queue.end()) {
            solution& s = queue[next_sequence];
            display(s.cp, s.seq, s.phase2probes, s.moves);
            queue.erase(next_sequence);
            next_sequence++;
        }
    } else {
        queue[seq] = solution(cp, seq, phase2probes, sol);
    }
    release_global_lock();
}

// ============================================================================
// Cube State Comparison
// ============================================================================

int sloweq(const cubepos& cp1, const cubepos& cp2) {
    cubepos cp3;
    for (int m = 0; m < KOCSYMM; m++) {
        cp2.remap_into(m, cp3);
        if (cp1 == cp3)
            return 1;
    }
    return 0;
}

// ============================================================================
// Two-Phase Solver Class
// ============================================================================

class twophasesolver {
public:
    twophasesolver() {}
    
    cubepos pos;
    long long phase2probes;
    int bestsol;
    int finished;
    int curm;
    int solmap;
    int seq;
    
    unsigned char moves[MAX_MOVES];
    unsigned char bestmoves[MAX_MOVES];
    
    kocsymm kc6[6], kccanon6[6];
    cubepos cp6[6];
    permcube pc6[6];
    int mindepth[6];
    char uniq[6];
    int minmindepth;

    // ========================================================================
    // Main Solve Entry Point
    // ========================================================================
    
    void solve(int seqarg, cubepos& cp) {
        pos = cp;
        phase2probes = 0;
        bestsol = MAX_MOVES;
        finished = 0;
        seq = seqarg;

        // Initialize 6 orientations (3 axes × 2 inversions)
        minmindepth = MAX_MOVES;
        cubepos cpi, cp2;
        pos.invert_into(cpi);
        int ind = 0;
        
        for (int inv = 0; inv < 2; inv++)
            for (int mm = 0; mm < 3; mm++, ind++) {
                int m = KOCSYMM * mm;
                if (inv)
                    cpi.remap_into(m, cp2);
                else
                    pos.remap_into(m, cp2);
                cp6[ind] = cp2;
                kc6[ind] = kocsymm(cp2);
                pc6[ind] = permcube(cp2);
                kc6[ind].canon_into(kccanon6[ind]);
                mindepth[ind] = phase1::lookup(kc6[ind]);
                if (mindepth[ind] < minmindepth)
                    minmindepth = mindepth[ind];
                uniq[ind] = 1 & (axesmask >> ind);
                
                // Check for equivalent positions
                for (int i = 0; i < ind; i++)
                    if (uniq[i] && kccanon6[ind] == kccanon6[i] &&
                        sloweq(cp6[ind], cp6[i])) {
                        uniq[ind] = 0;
                        break;
                    }
            }

        // Iterative deepening search
        for (int d = minmindepth; d < bestsol && !finished; d++) {
            for (curm = 0; curm < 6; curm++)
                if (uniq[curm] && d < bestsol && !finished && d >= mindepth[curm]) {
                    solvep1(kc6[curm], pc6[curm], d, 0, ALLMOVEMASK, CANONSEQSTART);
                }
        }

        // Build and report solution
        moveseq sol;
        int m = cubepos::invm[(solmap % 3) * KOCSYMM];
        for (int i = 0; i < bestsol; i++)
            sol.push_back(cubepos::move_map[m][bestmoves[i]]);
        if (solmap >= 3)
            sol = cubepos::invert_sequence(sol);
        
        // Verify solution
        cubepos cpt;
        for (unsigned int i = 0; i < sol.size(); i++)
            cpt.move(sol[i]);
        if (cpt != pos)
            error("! move sequence doesn't work");
        
        report(pos, seq, phase2probes, sol);
    }

    // ========================================================================
    // Phase 1 Search
    // ========================================================================
    
    void solvep1(const kocsymm& kc, const permcube& pc, int togo, int sofar,
                 int movemask, int canon) {
        if (togo == 0) {
            if (kc == identity_kc)
                solvep2(pc, sofar);
            return;
        }
        if (finished)
            return;
        
        togo--;
        kocsymm kc2;
        permcube pc2;
        int newmovemask;
        
        while (!finished && movemask) {
            int mv = ffs(movemask) - 1;
            movemask &= movemask - 1;
            kc2 = kc;
            kc2.move(mv);
            int nd = phase1::lookup(kc2, togo, newmovemask);
            if (nd <= togo && (togo == nd || togo + nd >= 5)) {
                pc2 = pc;
                pc2.move(mv);
                moves[sofar] = mv;
                int new_canon = cubepos::next_cs(canon, mv);
                solvep1(kc2, pc2, togo, sofar + 1,
                        newmovemask & cubepos::cs_mask(new_canon), new_canon);
            }
        }
    }

    // ========================================================================
    // Phase 2 Search
    // ========================================================================
    
    void solvep2(const permcube& pc, int sofar) {
        phase2probes++;
        int d = phase2::lookup(pc);
        
        if (d + sofar < bestsol) {
            moveseq ms = phase2::solve(pc, bestsol - sofar - 1);
            if ((int)(ms.size()) + sofar < bestsol &&
                (ms.size() > 0 || pc == identity_pc)) {
                bestsol = ms.size() + sofar;
                for (unsigned int i = 0; i < ms.size(); i++)
                    moves[sofar + i] = ms[i];
                memcpy(bestmoves, moves, bestsol);
                solmap = curm;
                if (bestsol <= target_length)
                    finished = 1;
            }
        }
        
        if (phase2probes >= phase2limit && bestsol < MAX_MOVES)
            finished = 1;
    }

    // ========================================================================
    // Work Processing
    // ========================================================================
    
    void dowork();
    static void* worker(void* s) {
        twophasesolver* solv = (twophasesolver*)s;
        solv->dowork();
        return 0;
    }
    
    char pad[256];  // Padding to avoid false sharing
} solvers[MAX_THREADS];

// ============================================================================
// Input Processing
// ============================================================================

int getwork(cubepos& cp) {
    static int input_seq = 1;
    const int BUFSIZE = 1000;
    char buf[BUFSIZE + 1];
    
    get_global_lock();
    if (fgets(buf, BUFSIZE, stdin) == 0) {
        release_global_lock();
        return -1;
    }
    
    // Parse Singmaster notation
    if (cp.parse_Singmaster(buf) != 0) {
        error("! could not parse Singmaster notation");
    }
    
    int r = input_seq++;
    release_global_lock();
    return r;
}

void twophasesolver::dowork() {
    cubepos cp;
    int seq;
    while (1) {
        seq = getwork(cp);
        if (seq <= 0)
            return;
        solve(seq, cp);
    }
}

// ============================================================================
// Main Program
// ============================================================================

int main() {
    // Initialize
    phase1::init(skipwrite);
    phase2::init(skipwrite);
    pthread_mutex_init(&my_mutex, NULL);

    // Start worker threads
    pthread_t p_thread[MAX_THREADS];
    for (int ti = 1; ti < numthreads; ti++)
        pthread_create(&(p_thread[ti]), NULL, twophasesolver::worker, solvers + ti);
    solvers[0].dowork();
    for (int ti = 1; ti < numthreads; ti++)
        pthread_join(p_thread[ti], 0);
    
    return 0;
}