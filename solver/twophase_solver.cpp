#include "twophase_solver.h"

#include <cstring>
#include <strings.h> // ffs

using namespace std;

// Check whether two cube positions are equivalent under any of
// the symmetries used by the Kociemba coordinate system.
int cubes_equal_up_to_symmetry(const cubepos& cp1, const cubepos& cp2) {
    cubepos tmp;
    for (int m = 0; m < CUBE_SYMM; ++m) {
        cp2.remap_into(m, tmp);
        if (cp1 == tmp) {
            return 1;
        }
    }
    return 0;
}

TwophaseSolver::TwophaseSolver()
    : phase2probes(0),
      bestsol(MAX_MOVES),
      finished(0),
      curm(0),
      solmap(0),
      seq(0),
      minmindepth(MAX_MOVES) {
}

void TwophaseSolver::solve(int seqarg, cubepos& cp) {
    pos = cp;
    phase2probes = 0;
    bestsol = MAX_MOVES;
    finished = 0;
    seq = seqarg;

    // Build six orientations: three axes × two inversions. We keep the
    // best pruning depth over all and avoid searching symmetrically
    // equivalent states twice.
    minmindepth = MAX_MOVES;
    cubepos cpi, cp2;
    pos.invert_into(cpi);
    int ind = 0;

    for (int inv = 0; inv < 2; ++inv) {
        for (int mm = 0; mm < 3; ++mm, ++ind) {
            int m = CUBE_SYMM * mm;
            if (inv) {
                cpi.remap_into(m, cp2);
            } else {
                pos.remap_into(m, cp2);
            }

            cp6[ind] = cp2;
            kc6[ind] = CubeSymmetry(cp2);
            pc6[ind] = permcube(cp2);
            kc6[ind].canon_into(kccanon6[ind]);
            mindepth[ind] = phase1prune::lookup(kc6[ind]);

            if (mindepth[ind] < minmindepth) {
                minmindepth = mindepth[ind];
            }

            uniq[ind] = 1 & (axesmask >> ind);

            // Discard this orientation if it is equivalent (same canonical
            // coordinates and same cube state up to symmetry) to an earlier
            // one we already plan to search.
            for (int i = 0; i < ind; ++i) {
                if (uniq[i] && kccanon6[ind] == kccanon6[i] &&
                    cubes_equal_up_to_symmetry(cp6[ind], cp6[i])) {
                    uniq[ind] = 0;
                    break;
                }
            }
        }
    }

    // Iterative deepening over the minimal phase 1 depth for all
    // non‑equivalent orientations.
    for (int d = minmindepth; d < bestsol && !finished; ++d) {
        for (curm = 0; curm < 6; ++curm) {
            if (!uniq[curm]) {
                continue;
            }
            if (finished || d >= bestsol || d < mindepth[curm]) {
                continue;
            }
            solve_phase1(kc6[curm], pc6[curm], d, 0, ALLMOVEMASK, CANONSEQSTART);
        }
    }

    // Rebuild the move sequence in the original orientation.
    moveseq sol;
    int m = cubepos::invm[(solmap % 3) * CUBE_SYMM];
    for (int i = 0; i < bestsol; ++i) {
        sol.push_back(cubepos::move_map[m][bestmoves[i]]);
    }
    if (solmap >= 3) {
        sol = cubepos::invert_sequence(sol);
    }

    // Sanity check: applying the moves must return to the solved cube
    // relative to the original scrambled position.
    cubepos cpt;
    for (size_t i = 0; i < sol.size(); ++i) {
        cpt.move(sol[i]);
    }
    if (cpt != pos) {
        error("! move sequence doesn't work");
    }

    report_solution(pos, seq, phase2probes, sol);
}

void TwophaseSolver::solve_phase1(const CubeSymmetry& kc,
                                  const permcube& pc,
                                  int togo,
                                  int sofar,
                                  int movemask,
                                  int canon) {
    if (togo == 0) {
        if (kc == identity_kc) {
            solve_phase2(pc, sofar);
        }
        return;
    }
    if (finished) {
        return;
    }

    --togo;
    CubeSymmetry kc2;
    permcube pc2;
    int newmovemask = 0;

    while (!finished && movemask) {
        int mv = ffs(movemask) - 1;
        movemask &= movemask - 1;

        kc2 = kc;
        kc2.move(mv);
        int nd = phase1prune::lookup(kc2, togo, newmovemask);

        if (nd <= togo && (togo == nd || togo + nd >= 5)) {
            pc2 = pc;
            pc2.move(mv);
            moves[sofar] = static_cast<unsigned char>(mv);
            int new_canon = cubepos::next_cs(canon, mv);
            solve_phase1(kc2,
                         pc2,
                         togo,
                         sofar + 1,
                         newmovemask & cubepos::cs_mask(new_canon),
                         new_canon);
        }
    }
}

void TwophaseSolver::solve_phase2(const permcube& pc, int sofar) {
    ++phase2probes;
    int d = phase2prune::lookup(pc);

    if (d + sofar < bestsol) {
        moveseq ms = phase2prune::solve(pc, bestsol - sofar - 1);
        if (static_cast<int>(ms.size()) + sofar < bestsol &&
            (!ms.empty() || pc == identity_pc)) {
            bestsol = static_cast<int>(ms.size()) + sofar;
            for (size_t i = 0; i < ms.size(); ++i) {
                moves[sofar + static_cast<int>(i)] = static_cast<unsigned char>(ms[i]);
            }
            memcpy(bestmoves, moves, bestsol);
            solmap = curm;
            if (bestsol <= target_length) {
                finished = 1;
            }
        }
    }

    if (phase2probes >= phase2limit && bestsol < MAX_MOVES) {
        finished = 1;
    }
}

void TwophaseSolver::dowork() {
    cubepos cp;
    int seq_id = 0;

    while (true) {
        seq_id = getwork(cp);
        if (seq_id <= 0) {
            return; // EOF or error
        }
        solve(seq_id, cp);
    }
}

void* TwophaseSolver::worker_entry(void* s) {
    TwophaseSolver* solver = static_cast<TwophaseSolver*>(s);
    solver->dowork();
    return 0;
}

// Allocate the per‑thread solver instances.
TwophaseSolver solvers[MAX_THREADS];
