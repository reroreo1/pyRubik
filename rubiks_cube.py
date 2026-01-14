from twophase_solver import solve_state, is_twophase_available
from collections import deque
from pygame.locals import *
from OpenGL.GLU import *
from OpenGL.GL import *
from cubie import Cubie
import numpy as np
import random
import math


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

class RubiksCube:
    """Represents the complete 3x3x3 Rubik's Cube"""
    def __init__(self, auto_animate=False, speed=8.0):
        self.cubies = []
        self.animator = MoveAnimator(speed=speed)
        self.move_queue = deque()
        self.current_solution = []
        self.solving = False
        self.shuffling = False
        self.shuffle_total = 0
        self.move_history = []
        self.auto_moving = auto_animate
        self.initialize_cube()
        if auto_animate:
            self._queue_initial_animation()
        
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
    
    def _queue_initial_animation(self):
        """Queue initial animation: forward sequence then backward"""
        # Extended sequence with more moves to keep animation busy during loading
        initial_sequence = ['R', 'U', 'F', 'D', 'L', 'B', 'R', 'U', 'F', 'D','R', 'U', 'F', 'D', 'L', 'B', 'R', 'U', 'F', 'D','R', 'U', 'F', 'D', 'L', 'B', 'R', 'U', 'F', 'D']
        reverse_sequence = [move + "'" for move in reversed(initial_sequence)]
        
        self.queue_moves(initial_sequence, track_history=False)
        self.queue_moves(reverse_sequence, track_history=False)
    
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
                
                # Check if shuffling is complete
                if self.shuffling and not self.move_queue:
                    self.shuffling = False
                
                # Re-loop auto-animation
                if self.auto_moving and not self.move_queue and not self.solving and not self.shuffling:
                    self._queue_initial_animation()
    
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
    
    def shuffle(self, num_moves=21):
        """Shuffle the cube with random moves, avoiding redundant sequences"""
        if self.animator.is_animating() or self.move_queue:
            return
        
        # Clear history before shuffling
        self.move_history = []
        
        moves = []
        last_face = None
        
        for _ in range(num_moves):
            # Pick a face different from the last one to avoid canceling moves
            available_faces = [f for f in FACE_MOVES if f != last_face]
            face = random.choice(available_faces)
            modifier = random.choice(MOVE_MODIFIERS)
            moves.append(face + modifier)
            last_face = face
        
        self.shuffling = True
        self.shuffle_total = len(moves)
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
            solution = solve_state(cube_state)
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
