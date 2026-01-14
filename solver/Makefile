# Makefile for pyRubik C++ Solver
# Builds the two-phase cube solver binary

CXX = g++
CXXFLAGS = -O3 -Wall -Wextra -std=c++11
LDFLAGS = 

# Source files
SOURCES = solver_main.cpp twophase_solver.cpp phase1.cpp phase2.cpp cube_symmetry.cpp cubepos.cpp
OBJECTS = $(SOURCES:.cpp=.o)
TARGET = twophase

# Pruning table files (for cleanup)
PRUNING_TABLES = *.dat

.PHONY: all twophase clean fclean re

# Default target
all: $(TARGET)

# Build the solver binary
twophase: $(OBJECTS)
	@echo "Linking $(TARGET)..."
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $^ -o $@
	@echo "✓ $(TARGET) built successfully"
	@echo "Cleaning up object files..."
	rm -f $(OBJECTS)
	@echo "✓ Build complete"

# Compile C++ sources
%.o: %.cpp
	@echo "Compiling $<..."
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean build artifacts (keep pruning tables)
clean:
	@echo "Removing object files..."
	rm -f $(OBJECTS)
	@echo "✓ Clean complete"

# Full clean (remove everything including pruning tables)
fclean: clean
	@echo "Removing pruning tables and binary..."
	rm -f $(TARGET) $(PRUNING_TABLES)
	@echo "✓ Full clean complete"

# Rebuild everything
re: fclean all

# Display help
help:
	@echo "Solver Makefile targets:"
	@echo "  make              - Build solver (default)"
	@echo "  make twophase     - Build twophase binary"
	@echo "  make clean        - Remove object files"
	@echo "  make fclean       - Remove everything (binary + pruning tables)"
	@echo "  make re           - Full rebuild"
