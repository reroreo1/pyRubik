#ifndef SOLVER_INPUT_H
#define SOLVER_INPUT_H

#include "cubepos.h"

// Read a single cube position from stdin in Singmaster notation.
// Returns a positive sequence id on success, or a non‑positive value
// on EOF or error. Thread‑safe via the global mutex.
int getwork(cubepos& cp);

#endif // SOLVER_INPUT_H
