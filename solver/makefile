CXX = g++
CXXFLAGS = -DHALF -O3 -Wall -DLEVELCOUNTS

default: all

HSOURCES = bestsol.h corner_order.h cubepos.h kocsymm.h phase1prune.h phase2prune.h

BINARIES = twophase


all: $(BINARIES) 

clean:
	rm -f $(BINARIES)  *.o

fclean: clean
	rm -f *.dat

re: fclean all


twophase: twophase.cpp phase1prune.cpp phase1prune.h phase2prune.cpp phase2prune.h kocsymm.cpp kocsymm.h cubepos.cpp cubepos.h
	$(CXX) $(CXXFLAGS) -o twophase twophase.cpp phase1prune.cpp phase2prune.cpp kocsymm.cpp cubepos.cpp -lpthread
