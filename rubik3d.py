import copy
from collections import deque
import time
import pygame
import sys
import random

class CubeState:
    """Coordinate-based cube representation using group theory"""
    corner_names = ['URF','UFL','ULB','UBR','DFR','DLF','DBL','DRB']
    edge_names = ['UR','UF','UL','UB','DR','DF','DL','DB','FR','FL','BL','BR']

    def __init__(self):
        self.corner_positions = list(range(8))
        self.corner_orientations = [0]*8  # 0,1,2
        self.edge_positions = list(range(12))
        self.edge_orientations = [0]*12   # 0,1

    def copy(self):
        return copy.deepcopy(self)

    def move(self, move):
        """Apply one move (U, R, F, D, L, B and their variants)"""
        if move.endswith("2"):
            self._apply_move(move[0])
            self._apply_move(move[0])
        elif move.endswith("'"):
            self._apply_move(move[0])
            self._apply_move(move[0])
            self._apply_move(move[0])
        else:
            self._apply_move(move[0])

    def _apply_move(self, move):
        """Core move transformation tables"""
        if move == 'U':
            self._cycle(self.corner_positions, (0,1,2,3))
            self._cycle(self.edge_positions, (0,1,2,3))
        elif move == 'D':
            self._cycle(self.corner_positions, (4,7,6,5))
            self._cycle(self.edge_positions, (4,7,6,5))
        elif move == 'F':
            self._cycle(self.corner_positions, (0,4,5,1))
            self._cycle(self.edge_positions, (1,9,5,8))
            for i in [0,1,4,5]:
                self.corner_orientations[i] = (self.corner_orientations[i] + (1 if i in (0,5) else 2)) % 3
            for i in [1,5,8,9]:
                self.edge_orientations[i] ^= 1
        elif move == 'B':
            self._cycle(self.corner_positions, (2,3,7,6))
            self._cycle(self.edge_positions, (3,11,7,10))
            for i in [2,3,6,7]:
                self.corner_orientations[i] = (self.corner_orientations[i] + (1 if i in (3,6) else 2)) % 3
            for i in [3,7,10,11]:
                self.edge_orientations[i] ^= 1
        elif move == 'R':
            self._cycle(self.corner_positions, (0,3,7,4))
            self._cycle(self.edge_positions, (0,11,4,8))
            for i in [0,3,4,7]:
                self.corner_orientations[i] = (self.corner_orientations[i] + (1 if i in (0,7) else 2)) % 3
        elif move == 'L':
            self._cycle(self.corner_positions, (1,5,6,2))
            self._cycle(self.edge_positions, (2,9,6,10))
            for i in [1,2,5,6]:
                self.corner_orientations[i] = (self.corner_orientations[i] + (1 if i in (2,5) else 2)) % 3

    def _cycle(self, arr, idxs):
        temp = arr[idxs[0]]
        for i in range(3):
            arr[idxs[i]] = arr[idxs[i+1]]
        arr[idxs[3]] = temp

    def is_solved(self):
        return (self.corner_positions == list(range(8)) and
                self.corner_orientations == [0]*8 and
                self.edge_positions == list(range(12)) and
                self.edge_orientations == [0]*12)
    
    def get_corner_orientation_coord(self):
        """Convert corner orientations to coordinate (0-2186)"""
        coord = 0
        for i in range(7):
            coord = coord * 3 + self.corner_orientations[i]
        return coord
    
    def get_edge_orientation_coord(self):
        """Convert edge orientations to coordinate (0-2047)"""
        coord = 0
        for i in range(11):
            coord = coord * 2 + self.edge_orientations[i]
        return coord
    
    def get_ud_slice_coord(self):
        """Get coordinate for middle slice edges (0-494)"""
        n = 0
        k = 0
        coord = 0
        for i in range(11, -1, -1):
            if self.edge_positions[i] >= 8:
                coord += self._binomial(11-i, k+1)
                k += 1
        return coord
    
    def _binomial(self, n, k):
        """Calculate binomial coefficient"""
        if k > n or k < 0:
            return 0
        if k == 0 or k == n:
            return 1
        result = 1
        for i in range(min(k, n-k)):
            result = result * (n - i) // (i + 1)
        return result
    
    def is_in_g1(self):
        """Check if cube is in G1 subgroup (Phase 1 solved)"""
        if any(self.edge_orientations):
            return False
        if any(self.corner_orientations):
            return False
        for i in range(8):
            if self.edge_positions[i] >= 8:
                return False
        return True


class KociembaSolver:
    """Two-phase Kociemba algorithm solver"""
    
    PHASE1_MOVES = ['U', 'U2', "U'", 'D', 'D2', "D'", 
                    'L', 'L2', "L'", 'R', 'R2', "R'",
                    'F', 'F2', "F'", 'B', 'B2', "B'"]
    
    PHASE2_MOVES = ['U', 'U2', "U'", 'D', 'D2', "D'", 
                    'L2', 'R2', 'F2', 'B2']
    
    def __init__(self):
        self.solution = []
        self.best_length = 999
        
    def solve(self, cube, max_depth=24):
        """Main solving method using IDA* for both phases"""
        print("Starting Kociemba two-phase solver...")
        start_time = time.time()
        
        print("Phase 1: Solving orientation and UD-slice...")
        phase1_solution = self._phase1_search(cube, max_depth=12)
        
        if not phase1_solution:
            print("Phase 1 failed!")
            return None
        
        print(f"Phase 1 complete: {len(phase1_solution)} moves")
        
        cube_g1 = cube.copy()
        for move in phase1_solution:
            cube_g1.move(move)
        
        print("Phase 2: Solving permutations...")
        phase2_solution = self._phase2_search(cube_g1, max_depth=18)
        
        if not phase2_solution:
            print("Phase 2 failed!")
            return None
        
        print(f"Phase 2 complete: {len(phase2_solution)} moves")
        
        solution = phase1_solution + phase2_solution
        elapsed = time.time() - start_time
        
        print(f"\nTotal solution: {len(solution)} moves in {elapsed:.3f}s")
        
        return solution
    
    def _phase1_search(self, cube, max_depth):
        """IDA* search for phase 1"""
        for depth in range(max_depth + 1):
            result = self._phase1_ida(cube, depth, [], None)
            if result:
                return result
        return None
    
    def _phase1_ida(self, cube, depth, moves, last_move):
        """Recursive IDA* for phase 1"""
        if cube.is_in_g1():
            return moves
        
        if depth == 0:
            return None
        
        for move in self.PHASE1_MOVES:
            if last_move and move[0] == last_move[0]:
                continue
            if last_move and self._opposite_faces(move[0], last_move[0]):
                if move < last_move:
                    continue
            
            new_cube = cube.copy()
            new_cube.move(move)
            
            result = self._phase1_ida(new_cube, depth - 1, moves + [move], move)
            if result:
                return result
        
        return None
    
    def _phase2_search(self, cube, max_depth):
        """IDA* search for phase 2"""
        for depth in range(max_depth + 1):
            result = self._phase2_ida(cube, depth, [], None)
            if result:
                return result
        return None
    
    def _phase2_ida(self, cube, depth, moves, last_move):
        """Recursive IDA* for phase 2"""
        if cube.is_solved():
            return moves
        
        if depth == 0:
            return None
        
        for move in self.PHASE2_MOVES:
            if last_move and move[0] == last_move[0]:
                continue
            if last_move and self._opposite_faces(move[0], last_move[0]):
                if move < last_move:
                    continue
            
            new_cube = cube.copy()
            new_cube.move(move)
            
            result = self._phase2_ida(new_cube, depth - 1, moves + [move], move)
            if result:
                return result
        
        return None
    
    def _opposite_faces(self, f1, f2):
        """Check if two faces are opposite"""
        opposites = {'U': 'D', 'D': 'U', 'L': 'R', 'R': 'L', 'F': 'B', 'B': 'F'}
        return opposites.get(f1) == f2


# Face-based cube for visualization
class RubiksCube:
    def __init__(self):
        self.faces = {
            'U': ['W'] * 9,
            'R': ['R'] * 9,
            'F': ['G'] * 9,
            'D': ['Y'] * 9,
            'L': ['O'] * 9,
            'B': ['B'] * 9
        }

    def rotate_face_clockwise(self, face):
        f = self.faces[face]
        self.faces[face] = [
            f[6], f[3], f[0],
            f[7], f[4], f[1],
            f[8], f[5], f[2]
        ]

    def rotate_face_counterclockwise(self, face):
        f = self.faces[face]
        self.faces[face] = [
            f[2], f[5], f[8],
            f[1], f[4], f[7],
            f[0], f[3], f[6]
        ]

    def _rotate_face_clockwise_with_slices(self, face):
        self.rotate_face_clockwise(face)
        f = self.faces

        if face == 'U':
            temp = f['F'][0:3].copy()
            f['F'][0:3] = f['R'][0:3]
            f['R'][0:3] = f['B'][0:3]
            f['B'][0:3] = f['L'][0:3]
            f['L'][0:3] = temp
        elif face == 'D':
            temp = f['F'][6:9].copy()
            f['F'][6:9] = f['L'][6:9]
            f['L'][6:9] = f['B'][6:9]
            f['B'][6:9] = f['R'][6:9]
            f['R'][6:9] = temp
        elif face == 'F':
            temp = [f['U'][6], f['U'][7], f['U'][8]]
            f['U'][6], f['U'][7], f['U'][8] = f['L'][8], f['L'][5], f['L'][2]
            f['L'][8], f['L'][5], f['L'][2] = f['D'][2], f['D'][1], f['D'][0]
            f['D'][2], f['D'][1], f['D'][0] = f['R'][0], f['R'][3], f['R'][6]
            f['R'][0], f['R'][3], f['R'][6] = temp[0], temp[1], temp[2]
        elif face == 'B':
            temp = [f['U'][0], f['U'][1], f['U'][2]]
            f['U'][0], f['U'][1], f['U'][2] = f['R'][2], f['R'][5], f['R'][8]
            f['R'][2], f['R'][5], f['R'][8] = f['D'][8], f['D'][7], f['D'][6]
            f['D'][8], f['D'][7], f['D'][6] = f['L'][6], f['L'][3], f['L'][0]
            f['L'][6], f['L'][3], f['L'][0] = temp[0], temp[1], temp[2]
        elif face == 'L':
            temp = [f['U'][0], f['U'][3], f['U'][6]]
            f['U'][0], f['U'][3], f['U'][6] = f['B'][8], f['B'][5], f['B'][2]
            f['B'][8], f['B'][5], f['B'][2] = f['D'][0], f['D'][3], f['D'][6]
            f['D'][0], f['D'][3], f['D'][6] = f['F'][0], f['F'][3], f['F'][6]
            f['F'][0], f['F'][3], f['F'][6] = temp[0], temp[1], temp[2]
        elif face == 'R':
            temp = [f['U'][2], f['U'][5], f['U'][8]]
            f['U'][2], f['U'][5], f['U'][8] = f['F'][2], f['F'][5], f['F'][8]
            f['F'][2], f['F'][5], f['F'][8] = f['D'][2], f['D'][5], f['D'][8]
            f['D'][2], f['D'][5], f['D'][8] = f['B'][6], f['B'][3], f['B'][0]
            f['B'][6], f['B'][3], f['B'][0] = temp[0], temp[1], temp[2]

    def _rotate_face_counterclockwise_with_slices(self, face):
        for _ in range(3):
            self._rotate_face_clockwise_with_slices(face)

    def move(self, move):
        if move.endswith("2"):
            self._execute_basic(move[0], times=2)
        elif move.endswith("'"):
            self._execute_basic(move[0], times=3)
        else:
            self._execute_basic(move[0], times=1)

    def _execute_basic(self, face, times=1):
        for _ in range(times):
            self._rotate_face_clockwise_with_slices(face)

    def execute_moves(self, seq):
        for mv in seq.split():
            mv = mv.strip()
            if mv:
                self.move(mv)

    def is_solved(self):
        for k, v in self.faces.items():
            if any(st != v[4] for st in v):
                return False
        return True


WIDTH, HEIGHT = 900, 640
CELL_SIZE = 40
MARGIN = 20
FPS = 60

COLORS = {
    'W': (255, 255, 255),
    'Y': (255, 255, 0),
    'R': (255, 0, 0),
    'O': (255, 165, 0),
    'B': (0, 0, 255),
    'G': (0, 155, 0),
    'BLACK': (0, 0, 0),
    'GRAY': (200, 200, 200)
}

class Visualizer:
    def __init__(self, visual_cube, state_cube):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rubik's Cube - Kociemba Solver")
        self.clock = pygame.time.Clock()
        self.visual_cube = visual_cube
        self.state_cube = state_cube
        self.font = pygame.font.Font(None, 24)
        self.input_text = ""
        self.solution_text = ""
        
    def draw_face(self, face_name, x, y):
        face = self.visual_cube.faces[face_name]
        for row in range(3):
            for col in range(3):
                color = COLORS[face[row * 3 + col]]
                rect = pygame.Rect(
                    x + col * CELL_SIZE,
                    y + row * CELL_SIZE,
                    CELL_SIZE - 2,
                    CELL_SIZE - 2
                )
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, COLORS['BLACK'], rect, 2)
        
        label = self.font.render(face_name, True, COLORS['BLACK'])
        self.screen.blit(label, (x + CELL_SIZE, y - 22))
    
    def draw_cube_net(self):
        base_x = WIDTH // 2 - CELL_SIZE * 2.5
        base_y = 60
        
        self.draw_face('U', base_x + CELL_SIZE * 3, base_y)
        self.draw_face('L', base_x, base_y + CELL_SIZE * 3 + MARGIN)
        self.draw_face('F', base_x + CELL_SIZE * 3, base_y + CELL_SIZE * 3 + MARGIN)
        self.draw_face('R', base_x + CELL_SIZE * 6, base_y + CELL_SIZE * 3 + MARGIN)
        self.draw_face('B', base_x + CELL_SIZE * 9, base_y + CELL_SIZE * 3 + MARGIN)
        self.draw_face('D', base_x + CELL_SIZE * 3, base_y + CELL_SIZE * 6 + MARGIN*2)
    
    def draw_ui(self):
        instructions = [
            "CONTROLS: S=Scramble | V=SOLVE (Kociemba) | Q=Quit | ESC=Clear",
            "Type moves (space separated): F R U B L D (add ' for inverse, 2 for double)",
            "",
            f"Input: {self.input_text}_",
            f"Solution ({len(self.solution_text.split()) if self.solution_text else 0} moves): {self.solution_text[:100]}{'...' if len(self.solution_text) > 100 else ''}"
        ]
        
        y_offset = HEIGHT - 140
        for text in instructions:
            surface = self.font.render(text, True, COLORS['BLACK'])
            self.screen.blit(surface, (10, y_offset))
            y_offset += 25
    
    def sync_cubes(self, moves):
        """Apply moves to both cube representations"""
        self.visual_cube.execute_moves(moves)
        for move in moves.split():
            self.state_cube.move(move)
    
    def run(self):
        running = True
        
        while running:
            self.screen.fill(COLORS['GRAY'])
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    
                    elif event.key == pygame.K_ESCAPE:
                        self.input_text = ""
                    
                    elif event.key == pygame.K_s:
                        moves = []
                        faces = ['U','D','L','R','F','B']
                        suffixes = ['', "'", '2']
                        for _ in range(20):
                            moves.append(random.choice(faces) + random.choice(suffixes))
                        scramble = " ".join(moves)
                        self.sync_cubes(scramble)
                        print(f"Scrambled with: {scramble}")
                        self.input_text = ""
                        self.solution_text = ""
                    
                    elif event.unicode.lower() == 'v':
                        print("\n=== STARTING KOCIEMBA SOLVER ===")
                        solver = KociembaSolver()
                        solution = solver.solve(self.state_cube)
                        if solution:
                            self.solution_text = ' '.join(solution)
                            print(f"\nSolution: {self.solution_text}")
                            
                            # Verify
                            test_cube = self.state_cube.copy()
                            for move in solution:
                                test_cube.move(move)
                            if test_cube.is_solved():
                                print("✓ Solution verified!")
                            else:
                                print("✗ Verification failed!")
                        else:
                            print("No solution found!")
                        self.input_text = ""
                    
                    elif event.key == pygame.K_RETURN:
                        if self.input_text:
                            try:
                                self.sync_cubes(self.input_text)
                                print(f"Executed: {self.input_text}")
                            except Exception as e:
                                print(f"Error: {e}")
                            self.input_text = ""
                    
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    
                    elif event.key == pygame.K_SPACE:
                        self.input_text += " "
                    
                    elif event.key == pygame.K_QUOTE:
                        self.input_text += "'"
                    
                    elif event.unicode in "0123456789":
                        self.input_text += event.unicode
                    
                    else:
                        char = event.unicode.upper()
                        if char in "UDLRFB":
                            self.input_text += char
            
            self.draw_cube_net()
            self.draw_ui()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    visual_cube = RubiksCube()
    state_cube = CubeState()
    
    visualizer = Visualizer(visual_cube, state_cube)
    visualizer.run()