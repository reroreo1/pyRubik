"""
TwoPhase Solver Integration
Bridges Python Rubik's cube visualizer with the C++ twophase solver.
"""

import subprocess
import os

# Path to twophase executable
TWOPHASE_PATH = os.path.join(os.path.dirname(__file__), 'solver', 'twophase')


def simplify_moves(moves):
    """Simplify move sequence by cancelling redundant moves."""
    if not moves:
        return moves
    
    def parse_move(m):
        face = m[0]
        if len(m) == 1:
            return (face, 1)
        elif m.endswith("'"):
            return (face, 3)
        elif m.endswith("2"):
            return (face, 2)
        return (face, 1)
    
    def to_move(face, count):
        count = count % 4
        if count == 0:
            return None
        elif count == 1:
            return face
        elif count == 2:
            return face + "2"
        elif count == 3:
            return face + "'"
        return None
    
    simplified = []
    for move in moves:
        face, count = parse_move(move)
        if simplified:
            last_face, last_count = parse_move(simplified[-1])
            if last_face == face:
                simplified.pop()
                new_count = (last_count + count) % 4
                if new_count != 0:
                    new_move = to_move(face, new_count)
                    if new_move:
                        simplified.append(new_move)
                continue
        simplified.append(move)
    
    if len(simplified) < len(moves):
        return simplify_moves(simplified)
    return simplified


def convert_from_twophase_notation(moves):
    """Convert twophase notation (R1, R3, R2) to standard notation (R, R', R2)."""
    result = []
    for move in moves:
        if move.endswith('1'):
            result.append(move[0])
        elif move.endswith('3'):
            result.append(move[0] + "'")
        elif move.endswith('2'):
            result.append(move)
    return result


def invert_moves(moves):
    """Invert a sequence of moves: reverse order and invert each move."""
    result = []
    for move in reversed(moves):
        if len(move) == 1:
            result.append(move + "'")
        elif move.endswith("'"):
            result.append(move[0])
        elif move.endswith('2'):
            result.append(move)
    return result


def parse_twophase_solution(solution_str):
    """Parse concatenated twophase solution like 'R1U1R3F2' into list."""
    moves = []
    i = 0
    while i < len(solution_str):
        if i + 1 < len(solution_str) and solution_str[i].isalpha() and solution_str[i+1].isdigit():
            moves.append(solution_str[i:i+2])
            i += 2
        else:
            i += 1
    return moves


def solve_state(cube_state_singmaster, threads=4, max_length=50, twophase_path=None):
    """
    Solve cube from its current state using Singmaster notation.
    
    Args:
        cube_state_singmaster: Singmaster notation string
        threads: Number of threads for solver
        max_length: Maximum solution length
    
    Returns:
        List of solution moves or None
    """
    if twophase_path is None:
        twophase_path = TWOPHASE_PATH
    
    try:
        solver_dir = os.path.dirname(twophase_path)
        result = subprocess.run(
            [twophase_path, '-t', str(threads), '-s', str(max_length)],
            input=cube_state_singmaster + '\n',
            capture_output=True,
            text=True,
            timeout=30,
            cwd=solver_dir
        )
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and all(c.isalpha() or c.isdigit() for c in line):
                solution_twophase = parse_twophase_solution(line)
                if solution_twophase:
                    scramble = convert_from_twophase_notation(solution_twophase)
                    solution = invert_moves(scramble)
                    return simplify_moves(solution)
        return None
        
    except subprocess.TimeoutExpired:
        print("TwoPhase solver timed out")
        return None
    except FileNotFoundError:
        print(f"TwoPhase executable not found at: {twophase_path}")
        return None
    except Exception as e:
        print(f"Error running TwoPhase solver: {e}")
        return None


def is_twophase_available(twophase_path=None):
    """Check if twophase executable exists and is runnable."""
    if twophase_path is None:
        twophase_path = TWOPHASE_PATH
    return os.path.isfile(twophase_path) and os.access(twophase_path, os.X_OK)
