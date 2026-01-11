#include "solver_input.h"
#include "solver_config.h"

#include <cstdio>

// Thread‑safe wrapper around stdin parsing. All threads share the same
// input stream, so access is serialized via the global lock.

int getwork(cubepos& cp) {
    static int input_seq = 1;
    const int BUFSIZE = 1000;
    char buf[BUFSIZE + 1];

    get_global_lock();

    if (fgets(buf, BUFSIZE, stdin) == 0) {
        release_global_lock();
        return -1;  // EOF
    }

    // Parse Singmaster notation into a cubepos instance.
    if (cp.parse_Singmaster(buf) != 0) {
        error("! could not parse Singmaster notation");
        return -1;
    }

    int r = input_seq++;
    release_global_lock();
    return r;
}
