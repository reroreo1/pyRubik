import os
# Suppress libdecor warnings on Wayland
os.environ.setdefault('SDL_VIDEODRIVER', 'x11')

from twophase_solver import solve_state, is_twophase_available
from collections import deque
from pygame.locals import *
from OpenGL.GLU import *
from OpenGL.GL import *
from PIL import Image
import numpy as np
import pygame
import random
import math

# Color definitions (RGB)
COLORS = {
    'W': (1.0, 1.0, 1.0),    # White
    'Y': (1.0, 1.0, 0.0),    # Yellow
    'R': (1.0, 0.0, 0.0),    # Red
    'O': (1.0, 0.3, 0.0),    # Orange
    'G': (0.0, 0.8, 0.0),    # Green
    'B': (0.0, 0.0, 1.0),    # Blue
    'K': (0.0, 0.0, 0.0)     # Black (spacing)
}

# Move notation
FACE_MOVES = ['F', 'B', 'U', 'D', 'L', 'R']
MOVE_MODIFIERS = ['', "'", '2']


import numpy as np
from OpenGL.GL import *

import numpy as np
from OpenGL.GL import *

class Cubie:
    """Represents a single cubie (small cube) in the Rubik's Cube"""
    def __init__(self, position, colors):
        self.position = np.array(position, dtype=float)
        self.colors = colors  # Dictionary mapping face to color
        self.size = 0.95  # Slightly smaller than 1.0 for spacing effect
        self.corner_radius = 0.08  # Radius for rounded corners
        self.corner_segments = 4  # Smoothness of corners (4 is good balance)
        
        # Pre-calculate rounded square geometry once
        self._vertex_cache = {}
        
    def _generate_rounded_square_vertices(self, size):
        """Generate vertices for a rounded square (cached for performance)"""
        # Check cache first
        cache_key = (size, self.corner_radius, self.corner_segments)
        if cache_key in self._vertex_cache:
            return self._vertex_cache[cache_key]
        
        vertices = []
        half_size = size / 2
        inset = half_size - self.corner_radius
        
        # Define the four corner centers in 2D
        corners = [
            (inset, inset),    # Top-right
            (-inset, inset),   # Top-left
            (-inset, -inset),  # Bottom-left
            (inset, -inset)    # Bottom-right
        ]
        
        # Starting angles for each corner
        start_angles = [0, 90, 180, 270]
        
        # Generate rounded corners
        for (cx, cy), start_angle in zip(corners, start_angles):
            for i in range(self.corner_segments + 1):
                angle = np.radians(start_angle + i * 90 / self.corner_segments)
                x = cx + self.corner_radius * np.cos(angle)
                y = cy + self.corner_radius * np.sin(angle)
                vertices.append((x, y))
        
        # Cache the result
        self._vertex_cache[cache_key] = vertices
        return vertices
    
    def _draw_rounded_face(self, face_name, center, normal, up, color):
        """Draw a single face with rounded corners"""
        # Get 2D vertices from cache
        vertices_2d = self._generate_rounded_square_vertices(self.size)
        
        # Calculate right vector (perpendicular to normal and up)
        right = np.cross(normal, up)
        
        # Draw filled face using triangle fan
        glNormal3f(*normal)
        glColor3f(*color)
        
        glBegin(GL_TRIANGLE_FAN)
        glVertex3fv(center)  # Center point
        for x, y in vertices_2d:
            vertex = center + x * right + y * up
            glVertex3fv(vertex)
        # Close the fan
        x, y = vertices_2d[0]
        vertex = center + x * right + y * up
        glVertex3fv(vertex)
        glEnd()
        
        # Draw edge outline
        glColor3f(0, 0, 0)
        glLineWidth(1.5)
        glBegin(GL_LINE_LOOP)
        for x, y in vertices_2d:
            vertex = center + x * right + y * up
            glVertex3fv(vertex)
        glEnd()
    
    def draw(self):
        """Draw the cubie with colored faces and rounded corners"""
        glPushMatrix()
        glTranslatef(*self.position)
        
        s = self.size / 2
        
        # Define face data: (name, center, normal, up_vector)
        faces = [
            ('front', [0, 0, s], [0, 0, 1], [0, 1, 0]),
            ('back', [0, 0, -s], [0, 0, -1], [0, 1, 0]),
            ('top', [0, s, 0], [0, 1, 0], [0, 0, -1]),
            ('bottom', [0, -s, 0], [0, -1, 0], [0, 0, 1]),
            ('right', [s, 0, 0], [1, 0, 0], [0, 1, 0]),
            ('left', [-s, 0, 0], [-1, 0, 0], [0, 1, 0])
        ]
        
        # Enable lighting for better appearance
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        
        for face_name, center, normal, up in faces:
            color = self.colors.get(face_name, (0.1, 0.1, 0.1))  # Default to dark gray
            self._draw_rounded_face(
                face_name,
                np.array(center, dtype=float),
                np.array(normal, dtype=float),
                np.array(up, dtype=float),
                color
            )
        
        glDisable(GL_LIGHTING)
        glPopMatrix()
    
    def rotate(self, axis, angle):
        """Rotate the cubie around a given axis by angle (in degrees)"""
        rad = np.radians(angle)
        cos_a = np.cos(rad)
        sin_a = np.sin(rad)
        
        # Rotation matrices for each axis
        if axis == 'x':
            rotation_matrix = np.array([
                [1, 0, 0],
                [0, cos_a, -sin_a],
                [0, sin_a, cos_a]
            ])
        elif axis == 'y':
            rotation_matrix = np.array([
                [cos_a, 0, sin_a],
                [0, 1, 0],
                [-sin_a, 0, cos_a]
            ])
        elif axis == 'z':
            rotation_matrix = np.array([
                [cos_a, -sin_a, 0],
                [sin_a, cos_a, 0],
                [0, 0, 1]
            ])
        else:
            return
        
        # Rotate position
        self.position = rotation_matrix @ self.position
        
        # Update color mapping (rotate the colors to new faces)
        # This would need to be implemented based on your specific needs
        pass
    

import numpy as np

class MoveAnimator:
    """Handles smooth animation of cube moves"""
    
    def __init__(self, speed=10.0):
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
            self.rotation_axis = [0, 0, -direction]
        elif face == 'B':
            self.rotation_axis = [0, 0, direction]
        elif face == 'U':
            self.rotation_axis = [0, -direction, 0]
        elif face == 'D':
            self.rotation_axis = [0, direction, 0]
        elif face == 'R':
            self.rotation_axis = [-direction, 0, 0]
        elif face == 'L':
            self.rotation_axis = [direction, 0, 0]
    
    def update(self):
        """Update animation state, returns True if animation complete"""
        if self.current_move is None:
            return True
        
        # Simple smooth easing using smoothstep
        progress = min(1.0, self.rotation_angle / self.target_angle)
        eased = progress * progress * (3 - 2 * progress)
        
        # Increment rotation
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
        self.move_history = []
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
        self.move_history = []
    
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
    
    def to_singmaster(self):
        """
        Convert visual cube state directly to Singmaster notation for twophase.
        Format: 12 edges + 8 corners
        
        Looking at cube with Green=Front, White=Up:
        - Face arrays are [row][col] where row 0 is top, col 0 is left
        """
        # Map RGB to face letter based on center colors
        def rgb_to_face(rgb):
            if rgb is None:
                return '?'
            color_map = {
                'W': 'U', 'Y': 'D', 'G': 'F', 'B': 'B', 'R': 'R', 'O': 'L'
            }
            for letter, color in COLORS.items():
                if letter != 'K' and np.allclose(rgb, color, atol=0.1):
                    return color_map.get(letter, '?')
            return '?'
        
        # Get face states - each is 3x3 array [row][col]
        U = self.get_face_state('top')
        D = self.get_face_state('bottom')
        F = self.get_face_state('front')
        B = self.get_face_state('back')
        R = self.get_face_state('right')
        L = self.get_face_state('left')
        
        # Standard Singmaster edge order: UF UR UB UL DF DR DB DL FR FL BR BL
        # Face arrays: row 0=top, row 2=bottom when looking at face
        # U face: row 0 = front edge, row 2 = back edge (looking down from above)
        # D face: row 0 = back edge, row 2 = front edge (looking up from below)
        edges = []
        
        # UF - U front edge + F top edge
        edges.append(rgb_to_face(U[0][1]) + rgb_to_face(F[0][1]))
        # UR - U right edge + R top edge
        edges.append(rgb_to_face(U[1][2]) + rgb_to_face(R[0][1]))
        # UB - U back edge + B top edge
        edges.append(rgb_to_face(U[2][1]) + rgb_to_face(B[0][1]))
        # UL - U left edge + L top edge
        edges.append(rgb_to_face(U[1][0]) + rgb_to_face(L[0][1]))
        # DF - D front edge + F bottom edge
        edges.append(rgb_to_face(D[2][1]) + rgb_to_face(F[2][1]))
        # DR - D right edge + R bottom edge
        edges.append(rgb_to_face(D[1][2]) + rgb_to_face(R[2][1]))
        # DB - D back edge + B bottom edge
        edges.append(rgb_to_face(D[0][1]) + rgb_to_face(B[2][1]))
        # DL - D left edge + L bottom edge
        edges.append(rgb_to_face(D[1][0]) + rgb_to_face(L[2][1]))
        # FR - F right edge + R front edge (left side of R when looking at R)
        edges.append(rgb_to_face(F[1][2]) + rgb_to_face(R[1][0]))
        # FL - F left edge + L front edge (right side of L when looking at L)
        edges.append(rgb_to_face(F[1][0]) + rgb_to_face(L[1][2]))
        # BR - B left edge (its right when looking at it) + R back edge (right side of R)
        edges.append(rgb_to_face(B[1][0]) + rgb_to_face(R[1][2]))
        # BL - B right edge (its left when looking at it) + L back edge (left side of L)
        edges.append(rgb_to_face(B[1][2]) + rgb_to_face(L[1][0]))
        
        # Standard Singmaster corner order: UFR URB UBL ULF DRF DFL DLB DBR
        # Corner positions based on get_face_state coordinate mapping:
        # U: row0=front, row2=back; D: row0=back, row2=front
        corners = []
        
        # UFR - U front-right, F top-right, R top-left
        corners.append(rgb_to_face(U[0][2]) + rgb_to_face(F[0][2]) + rgb_to_face(R[0][0]))
        # URB - U back-right, R top-right, B top-left
        corners.append(rgb_to_face(U[2][2]) + rgb_to_face(R[0][2]) + rgb_to_face(B[0][0]))
        # UBL - U back-left, B top-right, L top-left
        corners.append(rgb_to_face(U[2][0]) + rgb_to_face(B[0][2]) + rgb_to_face(L[0][0]))
        # ULF - U front-left, L top-right, F top-left
        corners.append(rgb_to_face(U[0][0]) + rgb_to_face(L[0][2]) + rgb_to_face(F[0][0]))
        # DRF - D front-right, R bottom-left, F bottom-right
        corners.append(rgb_to_face(D[2][2]) + rgb_to_face(R[2][0]) + rgb_to_face(F[2][2]))
        # DFL - D front-left, F bottom-left, L bottom-right
        corners.append(rgb_to_face(D[2][0]) + rgb_to_face(F[2][0]) + rgb_to_face(L[2][2]))
        # DLB - D back-left, L bottom-left, B bottom-right
        corners.append(rgb_to_face(D[0][0]) + rgb_to_face(L[2][0]) + rgb_to_face(B[2][2]))
        # DBR - D back-right, B bottom-left, R bottom-right
        corners.append(rgb_to_face(D[0][2]) + rgb_to_face(B[2][0]) + rgb_to_face(R[2][2]))
        
        return ' '.join(edges + corners)
    
    def queue_move(self, move):
        """Add a move to the queue"""
        self.move_queue.append(move)
        # Track move history for solver (only if not solving)
        if not self.solving:
            self.move_history.append(move)
    
    def queue_moves(self, moves, track_history=True):
        """Add multiple moves to the queue"""
        for move in moves:
            self.move_queue.append(move)
            # Track move history for solver (only if not solving)
            if track_history and not self.solving:
                self.move_history.append(move)
    
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
                    print(f"Cube Solved Successfully!")
                    print(f"------------------------------------------------------------------------------------------------")
    
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
        
        # Clear history before shuffling
        self.move_history = []
        
        moves = []
        for _ in range(num_moves):
            face = random.choice(FACE_MOVES)
            modifier = random.choice(MOVE_MODIFIERS)
            moves.append(face + modifier)
        
        self.queue_moves(moves)
        print(f"Shuffling with ({len(moves)} moves) ==> {' '.join(moves)}")
    
    
    def solve(self):
        """Solve the cube using TwoPhase algorithm"""
        # Cancel any ongoing animation/solve first
        if self.animator.is_animating() or self.move_queue:
            self.move_queue.clear()
            self.animator.reset()
            self.solving = False
            print("Cancelled current solve. Press S again to solve from current state.")
            return
        
        # Check if already solved
        if self.is_solved():
            print("Cube is already solved!")
            return
        
        # Get cube state directly from visual cube
        cube_state = self.to_singmaster()
        
        solution = None
        if is_twophase_available():
            solution = solve_state(cube_state, threads=4, max_length=50)
            if solution:
                print(f"solving with  ({len(solution)} moves)  ==> {' '.join(solution)}")
        
        if solution:
            self.current_solution = solution
            self.solving = True
            self.queue_moves(solution, track_history=False)
        else:
            print("Could not find solution!")

    
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
        self.target_rotation_x = 25
        self.target_rotation_y = 45
        self.current_rotation_x = 25
        self.current_rotation_y = 45
        self.camera_smoothness = 0.1
        self.mouse_down = False
        self.last_mouse_pos = None
        
        # Zoom control
        self.zoom = 10.0          # Camera distance
        self.target_zoom = 10.0   # Target for smooth zoom
        self.min_zoom = 7.0       # Closest zoom
        self.max_zoom = 20.0      # Farthest zoom
        
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
    
    def load_background_texture(self):
        """Load and setup background texture"""
        # Load image using PIL
        try:
            image_path = os.path.join(os.path.dirname(__file__), "background.jpg")
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
        glEnable(GL_BLEND)  # Enable blending for transparency
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # Set blend function

        # Draw background panel
        padding = 10
        panel_width = 305
        panel_height = 230
        x_start = self.width - panel_width - padding -10
        y_start = self.height - panel_height - padding - 10
        
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
            self.draw_text_2d(status_text, 440 , 40, self.font, (100, 255, 100))
            
            # Display current move
            if current_move:
                move_text = f"Move: {current_move}"
                self.draw_text_2d(move_text, 550, 100, self.font, (255, 255, 100))

            # Display move sequence
            if remaining_moves:
                sequence_text = "Next: " + " ".join(list(remaining_moves)[:10])
                if len(remaining_moves) > 10:
                    sequence_text += "..."
                self.draw_text_2d(sequence_text, 490, 740, self.small_font, (200, 200, 200))
        
        elif self.cube.animator.is_animating():
            move_text = f"Move: {self.cube.animator.current_move}"
            self.draw_text_2d(move_text, 550, 100, self.font, (255, 255, 100))
    
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
            
            # Scroll wheel zoom
            if event.type == MOUSEWHEEL:
                self.target_zoom -= event.y * 0.5  # Scroll up = zoom in
                self.target_zoom = max(self.min_zoom, min(self.max_zoom, self.target_zoom))
            
            if event.type == MOUSEMOTION:
                if self.mouse_down:
                    pos = pygame.mouse.get_pos()
                    if self.last_mouse_pos:
                        dx = pos[0] - self.last_mouse_pos[0]
                        dy = pos[1] - self.last_mouse_pos[1]
                        self.target_rotation_y += dx * 0.5
                        self.target_rotation_x = max(min(self.target_rotation_x + dy * 0.5, 45), -45)
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
                    self.target_rotation_x = 25
                    self.target_rotation_y = 45

        return True
    
    def draw_controls_guide(self):
        """Display control guide with border at bottom-left"""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Panel dimensions and position
        padding = 10
        panel_width = 240
        panel_height = 220
        x_start = padding
        y_start = self.height - panel_height - padding
        border_width = 2
        
        # Draw border (black)
        glColor4f(0.1, 0.1, 0.1, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(x_start - border_width, y_start - border_width)
        glVertex2f(x_start + panel_width + border_width, y_start - border_width)
        glVertex2f(x_start + panel_width + border_width, y_start + panel_height + border_width)
        glVertex2f(x_start - border_width, y_start + panel_height + border_width)
        glEnd()
        
        # Draw text
        lines = [
            ("Controls", True),  # (text, is_header)
            ("Mouse Drag", "Rotate view"),
            ("F/B/U/D/L/R", "Rotate faces"),
            ("X", "Shuffle cube"),
            ("S", "Solve cube"),
            ("W", "Reset cube"),
            ("Q", "Quit program"),
            ("SPACE", "Auto-rotate"),
            ("ESC", "Reset camera")
        ]
        
        text_x = x_start + 15
        text_y = y_start + 25
        line_height = 22
        
        # Draw header
        header_text, _ = lines[0]
        self.draw_text_2d(header_text, text_x + 45, text_y, self.font, (200, 200, 200))
        
        # Draw command lines
        for i, (command, description) in enumerate(lines[1:], 1):
            y = text_y + i * line_height
            # Draw command (left column)
            self.draw_text_2d(command, text_x, y, self.small_font, (255, 255, 100))
            # Draw description (right column)
            self.draw_text_2d(description, text_x + 100, y, self.small_font, (230, 230, 230))
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def render(self):
        glClearColor(0.85, 0.85, 0.85, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Smooth zoom interpolation
        self.zoom += (self.target_zoom - self.zoom) * self.camera_smoothness
        gluLookAt(0, 0, self.zoom, 0, 0, 0, 0, 1, 0)

        # Smooth camera interpolation
        self.current_rotation_x += (self.target_rotation_x - self.current_rotation_x) * self.camera_smoothness
        self.current_rotation_y += (self.target_rotation_y - self.current_rotation_y) * self.camera_smoothness

        glRotatef(self.current_rotation_x, 1, 0, 0)
        glRotatef(self.current_rotation_y, 0, 1, 0)

        if self.auto_rotate:
            self.target_rotation_y += 0.1

        self.draw_background()
        self.cube.draw()
        self.draw_2d_minimap()
        self.draw_move_display()
        self.draw_controls_guide()

    def run(self):
        """Main game loop"""
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