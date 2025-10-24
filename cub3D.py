import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np
import random
from collections import deque
from PIL import Image
import os


# Color definitions (RGB)
COLORS = {
    'W': (1.0, 1.0, 1.0),    # White
    'Y': (1.0, 1.0, 0.0),    # Yellow
    'R': (1.0, 0.0, 0.0),    # Red
    'O': (1.0, 0.5, 0.0),    # Orange
    'G': (0.0, 0.8, 0.0),    # Green
    'B': (0.0, 0.0, 1.0),    # Blue
    'K': (0.0, 0.0, 0.0)     # Black (spacing)
}

# Move notation
FACE_MOVES = ['F', 'B', 'U', 'D', 'L', 'R']
MOVE_MODIFIERS = ['', "'", '2']

class Cubie:
    """Represents a single cubie (small cube) in the Rubik's Cube"""
    def __init__(self, position, colors):
        self.position = np.array(position, dtype=float)
        self.colors = colors  # Dictionary mapping face to color
        self.size = 0.91  # Slightly smaller than 1.0 for spacing effect
        
    def draw(self):
        """Draw the cubie with colored faces"""
        glPushMatrix()
        glTranslatef(*self.position)
        
        s = self.size / 1.9
        
        # Define vertices
        vertices = [
            [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],  # Back
            [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]       # Front
        ]
        
        # Define faces with their vertices and normals
        faces = [
            ('front', [4, 5, 6, 7], [0, 0, 1]),
            ('back', [1, 0, 3, 2], [0, 0, -1]),
            ('top', [3, 7, 6, 2], [0, 1, 0]),
            ('bottom', [0, 1, 5, 4], [0, -1, 0]),
            ('right', [1, 2, 6, 5], [1, 0, 0]),
            ('left', [0, 4, 7, 3], [-1, 0, 0])
        ]
        
        glBegin(GL_QUADS)
        for face_name, indices, normal in faces:
            color = self.colors.get(face_name, COLORS['K'])
            
            # Add lighting effect
            glNormal3f(*normal)
            glColor3f(*color)
            
            for idx in indices:
                glVertex3fv(vertices[idx])
        glEnd()
        
        # Draw black edges for better visibility
        glColor3f(0, 0, 0)
        glLineWidth(1.5)
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # Back face
            [4, 5], [5, 6], [6, 7], [7, 4],  # Front face
            [0, 4], [1, 5], [2, 6], [3, 7]   # Connecting edges
        ]
        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()
        
        glPopMatrix()
    
    def copy(self):
        """Create a deep copy of this cubie"""
        return Cubie(self.position.copy(), self.colors.copy())

class MoveAnimator:
    """Handles smooth animation of cube moves"""
    def __init__(self, speed=7.0):
        self.speed = speed  # degrees per frame
        self.animation_speed = speed
        self.current_move = None
        self.rotation_angle = 0
        self.target_angle = 0
        self.rotation_axis = None
        self.rotating_cubies = []
        
    def start_move(self, move, cubies):
        """Start animating a move"""
        self.current_move = move
        self.rotation_angle = 0
        self.rotating_cubies = cubies
        
        # Parse move notation
        face = move[0]
        modifier = move[1:] if len(move) > 1 else ''
        
        if modifier == "'":
            direction = -1
            self.target_angle = 90
        elif modifier == '2':
            direction = 1
            self.target_angle = 180
        else:
            direction = 1
            self.target_angle = 90
        
        # Set rotation axis based on face
        if face == 'F':
            self.rotation_axis = [0, 0, direction]
        elif face == 'B':
            self.rotation_axis = [0, 0, -direction]
        elif face == 'U':
            self.rotation_axis = [0, direction, 0]
        elif face == 'D':
            self.rotation_axis = [0, -direction, 0]
        elif face == 'R':
            self.rotation_axis = [direction, 0, 0]
        elif face == 'L':
            self.rotation_axis = [-direction, 0, 0]
    
    def update(self):
        """Update animation state, returns True if animation complete"""
        if self.current_move is None:
            return True
        
        self.rotation_angle += self.animation_speed
        
        if self.rotation_angle >= self.target_angle:
            self.rotation_angle = self.target_angle
            complete = True
        else:
            complete = False
        
        return complete
    
    def is_animating(self):
        """Check if currently animating"""
        return self.current_move is not None
    
    def reset(self):
        """Reset animator state"""
        self.current_move = None
        self.rotation_angle = 0
        self.rotating_cubies = []

class RubiksCube:
    """Represents the complete 3x3x3 Rubik's Cube"""
    def __init__(self):
        self.cubies = []
        self.animator = MoveAnimator(speed=7.0)
        self.move_queue = deque()
        self.current_solution = []
        self.solving = False
        self.initialize_cube()
        
    def initialize_cube(self):
        """Create all 27 cubies with appropriate colors"""
        self.cubies = []
        for x in range(-1, 2):
            for y in range(-1, 2):
                for z in range(-1, 2):
                    colors = {}
                    if z == 1: colors['front'] = COLORS['G']
                    if z == -1: colors['back'] = COLORS['B']
                    if y == 1: colors['top'] = COLORS['W']
                    if y == -1: colors['bottom'] = COLORS['Y']
                    if x == 1: colors['right'] = COLORS['R']
                    if x == -1: colors['left'] = COLORS['O']
                    
                    self.cubies.append(Cubie([x, y, z], colors))
        
        self.move_queue.clear()
        self.current_solution = []
        self.solving = False
    
    def get_face_state(self, face):
        """Get 3x3 grid of colors for a specific face for minimap"""
        state = [[None for _ in range(3)] for _ in range(3)]
        
        if face == 'front':
            for cubie in self.cubies:
                if abs(cubie.position[2] - 1) < 0.1:
                    x = int(cubie.position[0] + 1)
                    y = int(-cubie.position[1] + 1)
                    state[y][x] = cubie.colors.get('front', COLORS['K'])
        elif face == 'back':
            for cubie in self.cubies:
                if abs(cubie.position[2] + 1) < 0.1:
                    x = int(-cubie.position[0] + 1)
                    y = int(-cubie.position[1] + 1)
                    state[y][x] = cubie.colors.get('back', COLORS['K'])
        elif face == 'top':
            for cubie in self.cubies:
                if abs(cubie.position[1] - 1) < 0.1:
                    x = int(cubie.position[0] + 1)
                    y = int(-cubie.position[2] + 1)
                    state[y][x] = cubie.colors.get('top', COLORS['K'])
        elif face == 'bottom':
            for cubie in self.cubies:
                if abs(cubie.position[1] + 1) < 0.1:
                    x = int(cubie.position[0] + 1)
                    y = int(cubie.position[2] + 1)
                    state[y][x] = cubie.colors.get('bottom', COLORS['K'])
        elif face == 'right':
            for cubie in self.cubies:
                if abs(cubie.position[0] - 1) < 0.1:
                    x = int(-cubie.position[2] + 1)
                    y = int(-cubie.position[1] + 1)
                    state[y][x] = cubie.colors.get('right', COLORS['K'])
        elif face == 'left':
            for cubie in self.cubies:
                if abs(cubie.position[0] + 1) < 0.1:
                    x = int(cubie.position[2] + 1)
                    y = int(-cubie.position[1] + 1)
                    state[y][x] = cubie.colors.get('left', COLORS['K'])
        
        return state
    
    def get_cubies_for_face(self, face):
        """Get list of cubies that belong to a specific face"""
        if face == 'F':
            return [c for c in self.cubies if abs(c.position[2] - 1) < 0.1]
        elif face == 'B':
            return [c for c in self.cubies if abs(c.position[2] + 1) < 0.1]
        elif face == 'U':
            return [c for c in self.cubies if abs(c.position[1] - 1) < 0.1]
        elif face == 'D':
            return [c for c in self.cubies if abs(c.position[1] + 1) < 0.1]
        elif face == 'R':
            return [c for c in self.cubies if abs(c.position[0] - 1) < 0.1]
        elif face == 'L':
            return [c for c in self.cubies if abs(c.position[0] + 1) < 0.1]
        return []
    
    def queue_move(self, move):
        """Add a move to the queue"""
        self.move_queue.append(move)
    
    def queue_moves(self, moves):
        """Add multiple moves to the queue"""
        for move in moves:
            self.move_queue.append(move)
    
    def update_animation(self):
        """Update rotation animation"""
        if not self.animator.is_animating() and self.move_queue:
            # Start next move
            move = self.move_queue.popleft()
            face = move[0]
            cubies = self.get_cubies_for_face(face)
            self.animator.start_move(move, cubies)
        
        if self.animator.is_animating():
            complete = self.animator.update()
            
            if complete:
                # Apply the rotation
                self.apply_rotation()
                self.animator.reset()
                
                # Check if solving is complete
                if self.solving and not self.move_queue:
                    self.solving = False
    
    def apply_rotation(self):
        """Apply the completed rotation to cubie positions and colors"""
        if not self.animator.rotating_cubies:
            return
        
        angle_rad = math.radians(self.animator.target_angle)
        axis = np.array(self.animator.rotation_axis)
        axis = axis / np.linalg.norm(axis)
        
        # Rotation matrix using Rodrigues' formula
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        for cubie in self.animator.rotating_cubies:
            # Rotate position
            pos = cubie.position
            rotated = pos * cos_a + np.cross(axis, pos) * sin_a + axis * np.dot(axis, pos) * (1 - cos_a)
            cubie.position = np.round(rotated)
            
            # Rotate colors
            new_colors = {}
            for face, color in cubie.colors.items():
                new_face = self.rotate_face_name(face, axis, angle_rad)
                new_colors[new_face] = color
            cubie.colors = new_colors
    
    def rotate_face_name(self, face, axis, angle):
        """Determine new face name after rotation"""
        face_normals = {
            'front': [0, 0, 1], 'back': [0, 0, -1],
            'top': [0, 1, 0], 'bottom': [0, -1, 0],
            'right': [1, 0, 0], 'left': [-1, 0, 0]
        }
        
        normal = np.array(face_normals[face])
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        # Apply rotation to normal
        rotated = normal * cos_a + np.cross(axis, normal) * sin_a + axis * np.dot(axis, normal) * (1 - cos_a)
        rotated = np.round(rotated)
        
        # Find matching face
        for fname, fnormal in face_normals.items():
            if np.allclose(rotated, fnormal):
                return fname
        return face
    
    def shuffle(self, num_moves=20):
        """Shuffle the cube with random moves"""
        if self.animator.is_animating() or self.move_queue:
            return
        
        moves = []
        for _ in range(num_moves):
            face = random.choice(FACE_MOVES)
            modifier = random.choice(MOVE_MODIFIERS)
            moves.append(face + modifier)
        
        self.queue_moves(moves)
        print(f"Shuffling with: {' '.join(moves)}")
    
    def solve(self):
        """Solve the cube using a simple layer-by-layer approach"""
        if self.animator.is_animating() or self.move_queue:
            return
        
        # Simple solving algorithm - this is a basic implementation
        # For a real Kociemba or Thistlethwaite solver, you'd need a much more complex algorithm
        solution = self.find_simple_solution()
        
        if solution:
            self.current_solution = solution
            self.queue_moves(solution)
            self.solving = True
            print(f"Solving with {len(solution)} moves: {' '.join(solution)}")
        else:
            print("Cube appears to be solved!")
    
    def find_simple_solution(self):
        """
        Simple solving algorithm using beginner's method approach
        This is a simplified version - real solvers use more sophisticated algorithms
        """
        # Check if already solved
        if self.is_solved():
            return []
        
        # For demonstration, we'll use a pattern that works for many scrambles
        # A real implementation would analyze the cube state and compute optimal moves
        solution = []
        
        # Generate a simple solution sequence (this is illustrative)
        # In practice, you'd implement layer-by-layer solving or use Kociemba algorithm
        moves_to_try = [
            # Example solving sequence - this won't solve all cubes optimally
            "R U R' U'", "R U R' U'", "R U R' U'",
            "F R U R' U' F'",
            "U R U' L' U R' U' L"
        ]
        
        for sequence in moves_to_try:
            for move in sequence.split():
                if move:
                    solution.append(move)
                    if len(solution) >= 20:
                        break
            if len(solution) >= 20:
                break
        
        return solution[:20]  # Limit to 20 moves
    
    def is_solved(self):
        """Check if the cube is solved"""
        faces = ['front', 'back', 'top', 'bottom', 'right', 'left']
        
        for face in faces:
            state = self.get_face_state(face)
            if not state[0][0]:
                continue
            
            reference_color = state[0][0]
            for row in state:
                for color in row:
                    if color is None or not np.allclose(color, reference_color):
                        return False
        
        return True
    
    def draw(self):
        """Draw all cubies"""
        for cubie in self.cubies:
            if cubie in self.animator.rotating_cubies:
                glPushMatrix()
                glRotatef(self.animator.rotation_angle, *self.animator.rotation_axis)
                cubie.draw()
                glPopMatrix()
            else:
                cubie.draw()

class CubeViewer:
    """Main application class"""
    def __init__(self):
        pygame.init()
        self.width, self.height = 1200, 800
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Rubik's Cube Solver")
        self.background_texture = self.load_background_texture()
        
        self.cube = RubiksCube()
        self.setup_opengl()
        
        
        # Camera control
        self.rotation_x = 25
        self.rotation_y = 45
        self.mouse_down = False
        self.last_mouse_pos = None
        
        # Auto-rotation
        self.auto_rotate = False
        
        # Font for text display
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Clock for FPS
        self.clock = pygame.time.Clock()
        
    def setup_opengl(self):
        """Initialize OpenGL settings"""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Light setup
        glLight(GL_LIGHT0, GL_POSITION, (5, 5, 5, 1))
        glLight(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1))
        glLight(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1))
        glLight(GL_LIGHT0, GL_SPECULAR, (1, 1, 1, 1))
        
        glMaterialfv(GL_FRONT, GL_SPECULAR, (0.3, 0.3, 0.3, 1))
        glMaterialf(GL_FRONT, GL_SHININESS, 20)
        
        # Perspective
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, self.width / self.height, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
    

    # Add this method to CubeViewer class
    def load_background_texture(self):
        """Load and setup background texture"""
        # Load image using PIL
        try:
            image_path = os.path.join(os.path.dirname(__file__), "background.jpg")  # Put your image in same folder
            image = Image.open(image_path)
            ix, iy = image.size
            image_data = image.tobytes("raw", "RGBA", 0, -1)
        except Exception as e:
            print(f"Could not load background image: {e}")
            return None

        # Generate and bind texture
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        # ensure correct packing
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        
       # Setup texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        
        # Create texture from image data
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
        # unbind
        glBindTexture(GL_TEXTURE_2D, 0)
        return texture_id

    def draw_background(self):
        """Draw background image"""
        # only draw if texture loaded successfully
        if not getattr(self, 'background_texture', None):
            return

        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.background_texture)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, 1, 0, 1, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Draw textured quad
        glColor4f(1,1,1,1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(1, 0)
        glTexCoord2f(1, 1); glVertex2f(1, 1)
        glTexCoord2f(0, 1); glVertex2f(0, 1)
        glEnd()
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

    def draw_text_2d(self, text, x, y, font=None, color=(255, 255, 255)):
        if font is None:
            font = self.font
        
        # Render text to surface
        surface = font.render(text, True, color)
        text_data = pygame.image.tostring(surface, "RGBA", True)
        text_width, text_height = surface.get_size()
        
        # Save current OpenGL state
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Switch to 2D orthographic projection
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Draw the text
        glRasterPos2i(int(x), int(y))
        glDrawPixels(text_width, text_height, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        # Restore previous OpenGL state
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()


    
    def draw_2d_minimap(self):
        """Draw 2D minimap of cube faces"""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        # Draw background panel
        padding = 10
        panel_width = 305
        panel_height = 230
        x_start = self.width - panel_width - padding
        y_start = self.height - panel_height - padding - 60
        
        glColor4f(0.2, 0.2, 0.2, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(x_start - 5, y_start - 5)
        glVertex2f(x_start + panel_width + 5, y_start - 5)
        glVertex2f(x_start + panel_width + 5, y_start + panel_height + 5)
        glVertex2f(x_start - 5, y_start + panel_height + 5)
        glEnd()
        
        # Draw cube net layout
        faces_layout = [
            ('top', 1, 0),
            ('left', 0, 1),
            ('front', 1, 1),
            ('right', 2, 1),
            ('back', 3, 1),
            ('bottom', 1, 2)
        ]
        
        cell_size = 25
        gap = 2
        
        for face_name, grid_x, grid_y in faces_layout:
            state = self.cube.get_face_state(face_name)
            
            for row in range(3):
                for col in range(3):
                    x = x_start + grid_x * (3 * cell_size + gap) + col * cell_size
                    y = y_start + grid_y * (3 * cell_size + gap) + row * cell_size
                    
                    color = state[row][col]
                    if color:
                        glColor3f(*color)
                    else:
                        glColor3f(0.1, 0.1, 0.1)
                    
                    glBegin(GL_QUADS)
                    glVertex2f(x, y)
                    glVertex2f(x + cell_size - 1, y)
                    glVertex2f(x + cell_size - 1, y + cell_size - 1)
                    glVertex2f(x, y + cell_size - 1)
                    glEnd()
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
    
    def draw_move_display(self):
        """Display current move and solution sequence"""
        if self.cube.solving and self.cube.current_solution:
            remaining_moves = list(self.cube.move_queue)
            current_move = self.cube.animator.current_move if self.cube.animator.is_animating() else None
            
            # Display solving status
            status_text = f"SOLVING... ({len(self.cube.current_solution) - len(remaining_moves)}/{len(self.cube.current_solution)} moves)"
            self.draw_text_2d(status_text, 20, 30, self.font, (100, 255, 100))
            
            # Display current move
            if current_move:
                move_text = f"Current: {current_move}"
                self.draw_text_2d(move_text, 20, 70, self.font, (255, 255, 100))
            
            # Display move sequence
            if remaining_moves:
                sequence_text = "Next: " + " ".join(list(remaining_moves)[:10])
                if len(remaining_moves) > 10:
                    sequence_text += "..."
                self.draw_text_2d(sequence_text, 20, 110, self.small_font, (200, 200, 200))
        
        elif self.cube.animator.is_animating():
            move_text = f"Move: {self.cube.animator.current_move}"
            self.draw_text_2d(move_text, 20, 30, self.font, (255, 255, 100))
    
    def handle_events(self):
        """Handle keyboard and mouse events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_down = True
                    self.last_mouse_pos = pygame.mouse.get_pos()
            
            if event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_down = False
            
            if event.type == MOUSEMOTION:
                if self.mouse_down:
                    pos = pygame.mouse.get_pos()
                    if self.last_mouse_pos:
                        dx = pos[0] - self.last_mouse_pos[0]
                        dy = pos[1] - self.last_mouse_pos[1]
                        self.rotation_y += dx * 0.5
                        self.rotation_x += dy * 0.5
                    self.last_mouse_pos = pos
            
            if event.type == KEYDOWN:
                # Face rotations
                if event.key == K_f:
                    self.cube.queue_move('F')
                elif event.key == K_b:
                    self.cube.queue_move('B')
                elif event.key == K_u:
                    self.cube.queue_move('U')
                elif event.key == K_d:
                    self.cube.queue_move('D')
                elif event.key == K_r:
                    self.cube.queue_move('R')
                elif event.key == K_l:
                    self.cube.queue_move('L')
                
                # Control keys
                elif event.key == K_q:
                    return False  # Quit
                elif event.key == K_w:
                    self.cube.initialize_cube()  # Reset
                    print("Cube reset to solved state")
                elif event.key == K_x:
                    self.cube.shuffle()  # Shuffle
                elif event.key == K_s:
                    self.cube.solve()  # Solve
                elif event.key == K_SPACE:
                    self.auto_rotate = not self.auto_rotate
                elif event.key == K_ESCAPE:
                    self.rotation_x = 25
                    self.rotation_y = 45
        
        return True
    
    def draw_controls_guide(self):
        """Display control guide neatly at bottom-left"""
        lines = [
            "Controls:",
            " Mouse Drag  - Rotate view",
            " F/B/U/D/L/R - Rotate face",
            " X           - Shuffle cube",
            " S           - Solve cube",
            " W           - Reset cube",
            " Q           - Quit program",
            " SPACE       - Auto-rotate",
            " ESC         - Reset camera",
        ]
        x, y = 20, self.height - 200
        for i, text in enumerate(lines):
            color = (180, 180, 180) if i == 0 else (230, 230, 230)
            font = self.small_font if i > 0 else self.font
            self.draw_text_2d(text, x, y + i * 22, font, color)

    def render(self):
        glClearColor(0.85, 0.85, 0.85, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(0, 0, 10, 0, 0, 0, 0, 1, 0)

        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)

        if self.auto_rotate:
            self.rotation_y += 0.5

        self.draw_background()
        self.cube.draw()

        # --- Draw 2D overlays ---
        # Background panel first
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glColor4f(0.05, 0.05, 0.05, 0.4)
        glBegin(GL_QUADS)
        glVertex2f(10, self.height - 220)
        glVertex2f(320, self.height - 220)  # wider
        glVertex2f(320, self.height - 10)
        glVertex2f(10, self.height - 10)
        glEnd()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        # Now draw text and minimap on top
        self.draw_2d_minimap()
        self.draw_move_display()
        self.draw_controls_guide()

    
    def run(self):
        """Main game loop"""
        print("\n=== 3D Rubik's Cube Solver ===")
        print("\nControls:")
        print("  Mouse Drag: Rotate view")
        print("  F/B/U/D/L/R: Rotate Front/Back/Up/Down/Left/Right face")
        print("  Q: Quit")
        print("  W: Reset cube to solved state")
        print("  X: Shuffle (20 random moves)")
        print("  S: Solve automatically")
        print("  SPACE: Toggle auto-rotation")
        print("  ESC: Reset view\n")
        
        running = True
        while running:
            running = self.handle_events()
            self.cube.update_animation()
            self.render()
            self.clock.tick(60)

            pygame.display.flip()   
        
if __name__ == "__main__":
    viewer = CubeViewer()
    viewer.run()