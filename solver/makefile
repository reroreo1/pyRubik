CXX = g++
CXXFLAGS = -DHALF -O3 -Wall -DLEVELCOUNTS

default: all

HSOURCES = cubepos.h cube_symmetry.h phase1prune.h phase2prune.h \
	solver_config.h solver_solution_queue.h solver_input.h twophase_solver.h

BINARIES = twophase


all: $(BINARIES)

clean:
	rm -f $(BINARIES)  *.o

fclean: clean
	rm -f *.dat

re: fclean all

twophase: solver_main.cpp twophase_solver.cpp solver_input.cpp solver_solution_queue.cpp solver_config.cpp \
	phase1prune.cpp phase1prune.h phase2prune.cpp phase2prune.h cube_symmetry.cpp cube_symmetry.h cubepos.cpp cubepos.h
	$(CXX) $(CXXFLAGS) -o twophase solver_main.cpp twophase_solver.cpp solver_input.cpp \
		solver_solution_queue.cpp solver_config.cpp phase1prune.cpp phase2prune.cpp cube_symmetry.cpp cubepos.cpp -lpthread
