# Root Makefile for pyRubik project
# Builds the C++ solver and installs Python dependencies

.PHONY: all install clean fclean re help solver python

# Default target
all: solver

# Install Python dependencies
install:
	@echo "Installing Python dependencies into ./env..."
	pip install -r requirements.txt

# Build the C++ solver
solver:
	@echo "Building C++ solver..."
	cd solver && $(MAKE) twophase
	@echo "✓ Solver built successfully"


# Full clean (removes pruning tables too)
fclean:
	@echo "Full clean (removing pruning tables)..."
	cd solver && $(MAKE) fclean
	@echo "✓ Full clean complete"

# Rebuild everything
re: fclean all

# Build everything including Python dependencies
setup: install solver
	@echo "✓ Setup complete!"

# Run the main Python application
run:
	python3 cub3D.py

# Help message
help:
	@echo "pyRubik Makefile targets:"
	@echo ""
	@echo "  make all        - Build the C++ solver (default)"
	@echo "  make install    - Install Python dependencies from requirements.txt"
	@echo "  make setup      - Install Python deps and build solver"
	@echo "  make fclean     - Full clean (includes pruning tables)"
	@echo "  make solver     - Build the C++ solver"
	@echo "  make re         - Rebuild everything"
	@echo "  make help       - Show this help message"
	@echo ""
	@echo "Quick start:"
	@echo "  python3 -m venv env    # Create virtual environment"
	@echo "  source env/bin/activate    # Activate virtual environment"
	@echo "  make setup    # One-time setup"
	@echo "  make run  # Run the app"
