CXX = g++
CXXFLAGS = -DHALF -O3 -Wall -DLEVELCOUNTS

default: all

HSOURCES = cubepos.h cube_symmetry.h phase1.h phase2.h \
	twophase_solver.h

BINARIES = twophase


all: $(BINARIES)

clean:
	rm -f $(BINARIES)  *.o

fclean: clean
	rm -f *.dat

re: fclean all

twophase: solver_main.cpp twophase_solver.cpp \
	phase1.cpp phase1.h phase2.cpp phase2.h cube_symmetry.cpp cube_symmetry.h cubepos.cpp cubepos.h
	$(CXX) $(CXXFLAGS) -o twophase solver_main.cpp twophase_solver.cpp \
		phase1.cpp phase2.cpp cube_symmetry.cpp cubepos.cpp -lpthread
