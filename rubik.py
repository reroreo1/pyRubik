import pygame
import sys

# Solver implementation
class CubeSolver:
    def __init__(self, cube):
        self.cube = cube
        self.solution = []
    
    def solve(self):
        """Main solving method - Layer by Layer approach"""
        print("\n=== Starting solve ===")
        self.solution = []
        
        print("Step 1: Solving white cross...")
        self.solve_white_cross()
        print(f"  Moves so far: {len(self.solution)}")
        
        print("Step 2: Solving white corners...")
        self.solve_white_corners()
        print(f"  Moves so far: {len(self.solution)}")
        
        print("Step 3: Solving middle layer...")
        self.solve_middle_layer()
        print(f"  Moves so far: {len(self.solution)}")
        
        print("Step 4: Solving yellow cross...")
        self.solve_yellow_cross()
        print(f"  Moves so far: {len(self.solution)}")
        
        print("Step 5: Positioning yellow edges...")
        self.position_yellow_edges()
        print(f"  Moves so far: {len(self.solution)}")
        
        print("Step 6: Positioning yellow corners...")
        self.position_yellow_corners()
        print(f"  Moves so far: {len(self.solution)}")
        
        print("Step 7: Orienting yellow corners...")
        self.orient_yellow_corners()
        
        print(f"\n=== Solved! Total moves: {len(self.solution)} ===")
        return ' '.join(self.solution)
    
    def move(self, move_str):
        """Execute a move and add it to solution"""
        self.cube.execute_moves(move_str)
        self.solution.extend(move_str.split())
    
    def solve_white_cross(self):
        """Solve white cross on bottom"""
        for _ in range(4):
            max_attempts = 20
            for attempt in range(max_attempts):
                if self.cube.faces['D'][0][1] == 'W':
                    break
                self.move("F' U' F U")
            self.move("D")
    
    def solve_white_corners(self):
        """Solve white corners"""
        for _ in range(4):
            for attempt in range(15):
                if self.cube.faces['D'][2][2] == 'W':
                    break
                self.move("R U R' U'")
            self.move("D")
    
    def solve_middle_layer(self):
        """Solve middle layer edges"""
        for _ in range(4):
            for attempt in range(10):
                if (self.cube.faces['F'][1][2] == self.cube.faces['F'][1][1] and
                    self.cube.faces['R'][1][0] == self.cube.faces['R'][1][1]):
                    break
                self.move("U R U' R' U' F' U F")
            self.move("U")
    
    def solve_yellow_cross(self):
        """Create yellow cross on top"""
        for _ in range(3):
            yellow_edges = sum([
                self.cube.faces['U'][0][1] == 'Y',
                self.cube.faces['U'][1][0] == 'Y',
                self.cube.faces['U'][1][2] == 'Y',
                self.cube.faces['U'][2][1] == 'Y'
            ])
            if yellow_edges == 4:
                return
            self.move("F R U R' U' F'")
            self.move("U")
    
    def position_yellow_edges(self):
        """Position yellow edges correctly"""
        for _ in range(4):
            correct = sum([
                self.cube.faces['F'][0][1] == self.cube.faces['F'][1][1],
                self.cube.faces['R'][0][1] == self.cube.faces['R'][1][1],
                self.cube.faces['B'][0][1] == self.cube.faces['B'][1][1],
                self.cube.faces['L'][0][1] == self.cube.faces['L'][1][1]
            ])
            if correct == 4:
                return
            self.move("R U R' U R U2 R' U")
    
    def position_yellow_corners(self):
        """Position yellow corners"""
        for _ in range(5):
            self.move("U R U' L' U R' U' L")
    
    def orient_yellow_corners(self):
        """Orient yellow corners to finish"""
        for _ in range(4):
            for attempt in range(6):
                if self.cube.faces['U'][2][2] == 'Y':
                    break
                self.move("R' D' R D")
            self.move("U")
        for _ in range(4):
            if self.is_solved():
                return
            self.move("U")
    
    def is_solved(self):
        """Check if cube is solved"""
        for face in self.cube.faces:
            center = self.cube.faces[face][1][1]
            for row in self.cube.faces[face]:
                for color in row:
                    if color != center:
                        return False
        return True

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
CELL_SIZE = 40
MARGIN = 20
FPS = 60

# Colors
COLORS = {
    'W': (255, 255, 255),  # White
    'Y': (255, 255, 0),    # Yellow
    'R': (255, 0, 0),      # Red
    'O': (255, 165, 0),    # Orange
    'B': (0, 0, 255),      # Blue
    'G': (0, 255, 0),      # Green
    'BLACK': (0, 0, 0),
    'GRAY': (50, 50, 50)
}

class RubiksCube:
    def __init__(self):
        # Cube representation: 6 faces, each 3x3
        # Faces: U (Up/White), D (Down/Yellow), L (Left/Orange), 
        #        R (Right/Red), F (Front/Green), B (Back/Blue)
        self.faces = {
            'U': [['W']*3 for _ in range(3)],  # White (top)
            'D': [['Y']*3 for _ in range(3)],  # Yellow (bottom)
            'L': [['O']*3 for _ in range(3)],  # Orange (left)
            'R': [['R']*3 for _ in range(3)],  # Red (right)
            'F': [['G']*3 for _ in range(3)],  # Green (front)
            'B': [['B']*3 for _ in range(3)]   # Blue (back)
        }
    
    def rotate_face_clockwise(self, face):
        """Rotate a face 90 degrees clockwise"""
        self.faces[face] = [
            [self.faces[face][2][0], self.faces[face][1][0], self.faces[face][0][0]],
            [self.faces[face][2][1], self.faces[face][1][1], self.faces[face][0][1]],
            [self.faces[face][2][2], self.faces[face][1][2], self.faces[face][0][2]]
        ]
    
    def rotate_face_counter_clockwise(self, face):
        """Rotate a face 90 degrees counter-clockwise"""
        for _ in range(3):
            self.rotate_face_clockwise(face)
    
    def U(self):
        """Up face clockwise"""
        self.rotate_face_clockwise('U')
        # Save top row of front
        temp = self.faces['F'][0][:]
        # Front <- Right
        self.faces['F'][0] = self.faces['R'][0][:]
        # Right <- Back
        self.faces['R'][0] = self.faces['B'][0][:]
        # Back <- Left
        self.faces['B'][0] = self.faces['L'][0][:]
        # Left <- temp (Front)
        self.faces['L'][0] = temp
    
    def U_prime(self):
        """Up face counter-clockwise"""
        for _ in range(3):
            self.U()
    
    def D(self):
        """Down face clockwise"""
        self.rotate_face_clockwise('D')
        # Save bottom row of front
        temp = self.faces['F'][2][:]
        # Front <- Left
        self.faces['F'][2] = self.faces['L'][2][:]
        # Left <- Back
        self.faces['L'][2] = self.faces['B'][2][:]
        # Back <- Right
        self.faces['B'][2] = self.faces['R'][2][:]
        # Right <- temp (Front)
        self.faces['R'][2] = temp
    
    def D_prime(self):
        """Down face counter-clockwise"""
        for _ in range(3):
            self.D()
    
    def L(self):
        """Left face clockwise"""
        self.rotate_face_clockwise('L')
        # Save left column
        temp = [self.faces['F'][i][0] for i in range(3)]
        # Front <- Up
        for i in range(3):
            self.faces['F'][i][0] = self.faces['U'][i][0]
        # Up <- Back (reversed)
        for i in range(3):
            self.faces['U'][i][0] = self.faces['B'][2-i][2]
        # Back <- Down (reversed)
        for i in range(3):
            self.faces['B'][i][2] = self.faces['D'][2-i][0]
        # Down <- temp (Front)
        for i in range(3):
            self.faces['D'][i][0] = temp[i]
    
    def L_prime(self):
        """Left face counter-clockwise"""
        for _ in range(3):
            self.L()
    
    def R(self):
        """Right face clockwise"""
        self.rotate_face_clockwise('R')
        # Save right column
        temp = [self.faces['F'][i][2] for i in range(3)]
        # Front <- Down
        for i in range(3):
            self.faces['F'][i][2] = self.faces['D'][i][2]
        # Down <- Back (reversed)
        for i in range(3):
            self.faces['D'][i][2] = self.faces['B'][2-i][0]
        # Back <- Up (reversed)
        for i in range(3):
            self.faces['B'][i][0] = self.faces['U'][2-i][2]
        # Up <- temp (Front)
        for i in range(3):
            self.faces['U'][i][2] = temp[i]
    
    def R_prime(self):
        """Right face counter-clockwise"""
        for _ in range(3):
            self.R()
    
    def F(self):
        """Front face clockwise"""
        self.rotate_face_clockwise('F')
        # Save bottom row of Up
        temp = self.faces['U'][2][:]
        # Up <- Left (right column, rotated)
        self.faces['U'][2] = [self.faces['L'][2][2], self.faces['L'][1][2], self.faces['L'][0][2]]
        # Left <- Down (bottom row)
        for i in range(3):
            self.faces['L'][i][2] = self.faces['D'][0][i]
        # Down <- Right (left column, rotated)
        self.faces['D'][0] = [self.faces['R'][2][0], self.faces['R'][1][0], self.faces['R'][0][0]]
        # Right <- temp (Up)
        for i in range(3):
            self.faces['R'][i][0] = temp[i]
    
    def F_prime(self):
        """Front face counter-clockwise"""
        for _ in range(3):
            self.F()
    
    def B(self):
        """Back face clockwise"""
        self.rotate_face_clockwise('B')
        # Save top row of Up
        temp = self.faces['U'][0][:]
        # Up <- Right (right column)
        for i in range(3):
            self.faces['U'][0][i] = self.faces['R'][i][2]
        # Right <- Down (top row, reversed)
        for i in range(3):
            self.faces['R'][i][2] = self.faces['D'][2][2-i]
        # Down <- Left (left column)
        for i in range(3):
            self.faces['D'][2][i] = self.faces['L'][i][0]
        # Left <- temp (Up, reversed)
        for i in range(3):
            self.faces['L'][i][0] = temp[2-i]
    
    def B_prime(self):
        """Back face counter-clockwise"""
        for _ in range(3):
            self.B()
    
    def execute_moves(self, move_sequence):
        """Execute a sequence of moves with full notation support (F R U B L D, ', 2)"""
        moves = move_sequence.split()
        move_map = {
            'U': self.U, 'U\'': self.U_prime, 'U2': lambda: (self.U(), self.U()),
            'D': self.D, 'D\'': self.D_prime, 'D2': lambda: (self.D(), self.D()),
            'L': self.L, 'L\'': self.L_prime, 'L2': lambda: (self.L(), self.L()),
            'R': self.R, 'R\'': self.R_prime, 'R2': lambda: (self.R(), self.R()),
            'F': self.F, 'F\'': self.F_prime, 'F2': lambda: (self.F(), self.F()),
            'B': self.B, 'B\'': self.B_prime, 'B2': lambda: (self.B(), self.B())
        }
        
        for move in moves:
            if move in move_map:
                move_map[move]()
            else:
                print(f"Warning: Unknown move '{move}'")

class Visualizer:
    def __init__(self, cube):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rubik's Cube - Move Testing")
        self.clock = pygame.time.Clock()
        self.cube = cube
        self.font = pygame.font.Font(None, 24)
        self.input_text = ""
        self.solving = False
        self.solution_text = ""
        
    def draw_face(self, face_name, x, y):
        """Draw a single face of the cube"""
        face = self.cube.faces[face_name]
        for row in range(3):
            for col in range(3):
                color = COLORS[face[row][col]]
                rect = pygame.Rect(
                    x + col * CELL_SIZE,
                    y + row * CELL_SIZE,
                    CELL_SIZE - 2,
                    CELL_SIZE - 2
                )
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, COLORS['BLACK'], rect, 2)
        
        # Draw face label
        label = self.font.render(face_name, True, COLORS['BLACK'])
        self.screen.blit(label, (x + CELL_SIZE, y - 25))
    
    def draw_cube_net(self):
        """Draw the cube as an unfolded net"""
        # Layout (net pattern):
        #         [U]
        #    [L]  [F]  [R]  [B]
        #         [D]
        
        base_x = WIDTH // 2 - CELL_SIZE * 1.5
        base_y = HEIGHT // 2 - CELL_SIZE * 3
        
        # Up
        self.draw_face('U', base_x, base_y)
        # Left, Front, Right, Back
        self.draw_face('L', base_x - CELL_SIZE * 3 - MARGIN, base_y + CELL_SIZE * 3 + MARGIN)
        self.draw_face('F', base_x, base_y + CELL_SIZE * 3 + MARGIN)
        self.draw_face('R', base_x + CELL_SIZE * 3 + MARGIN, base_y + CELL_SIZE * 3 + MARGIN)
        self.draw_face('B', base_x + CELL_SIZE * 6 + MARGIN * 2, base_y + CELL_SIZE * 3 + MARGIN)
        # Down
        self.draw_face('D', base_x, base_y + CELL_SIZE * 6 + MARGIN * 2)
    
    def draw_ui(self):
        """Draw the user interface"""
        # Instructions
        instructions = [
            "CONTROLS: S=Scramble | V=SOLVE | Q=Quit | ESC=Clear",
            "Type moves: F R U B L D (add ' for inverse, 2 for double)",
            "",
            f"Input: {self.input_text}_",
            f"Solution ({len(self.solution_text.split()) if self.solution_text else 0} moves): {self.solution_text[:60]}..."
        ]
        
        y_offset = 10
        for text in instructions:
            surface = self.font.render(text, True, COLORS['BLACK'])
            self.screen.blit(surface, (10, y_offset))
            y_offset += 25
    
    def run(self):
        """Main visualization loop"""
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
                        # Scramble with a predetermined mix
                        scramble = "R2 D' B' D F2 R F2 R2 U L' F2 U' B' L2 R D B' R' B2 L2 F2 L2 R2 U2 D2"
                        self.cube.execute_moves(scramble)
                        print(f"Scrambled with: {scramble}")
                        self.input_text = ""
                        self.solution_text = ""
                    
                    elif event.unicode.lower() == 'v':  # SOLVE key
                        print("\n=== STARTING SOLVER ===")
                        solver = CubeSolver(self.cube)
                        solution = solver.solve()
                        self.solution_text = solution
                        print(f"\nSolution: {solution}")
                        self.input_text = ""
                    
                    elif event.key == pygame.K_RETURN:
                        if self.input_text:
                            try:
                                self.cube.execute_moves(self.input_text)
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
                        # Add character if it's a valid move letter
                        char = event.unicode.upper()
                        if char in "UDLRFB":
                            self.input_text += char
            
            self.draw_cube_net()
            self.draw_ui()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

# Main execution
if __name__ == "__main__":
    cube = RubiksCube()
    visualizer = Visualizer(cube)
    visualizer.run()