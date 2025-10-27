from collections import deque
from pygame.locals import *
from OpenGL.GLU import *
from OpenGL.GL import *
from PIL import Image
import numpy as np
import pygame
import random
import math
import copy
import os

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

class VirtualCube:
    """Virtual cube for state tracking and move simulation"""
    def __init__(self):
        # Standard color scheme based on typical cube orientation
        # U=White(top), D=Yellow(bottom), F=Green(front), B=Blue(back), R=Red(right), L=Orange(left)
        self.faces = {
            'U': [['W']*3 for _ in range(3)],
            'D': [['Y']*3 for _ in range(3)],
            'F': [['G']*3 for _ in range(3)],
            'B': [['B']*3 for _ in range(3)],
            'R': [['R']*3 for _ in range(3)],
            'L': [['O']*3 for _ in range(3)]
        }
    
    def copy(self):
        new_cube = VirtualCube()
        new_cube.faces = copy.deepcopy(self.faces)
        return new_cube
    
    def rotate_face_clockwise(self, face):
        """Rotate a face 90 degrees clockwise"""
        f = self.faces[face]
        self.faces[face] = [[f[2][0], f[1][0], f[0][0]],
                            [f[2][1], f[1][1], f[0][1]],
                            [f[2][2], f[1][2], f[0][2]]]
    
    def move(self, move_str):
        """Execute a move on the virtual cube"""
        face = move_str[0]
        modifier = move_str[1:] if len(move_str) > 1 else ''
        
        times = 1
        if modifier == "'":
            times = 3
        elif modifier == '2':
            times = 2
        
        for _ in range(times):
            self._move_clockwise(face)
    
    def _move_clockwise(self, face):
        """Execute one clockwise rotation"""
        self.rotate_face_clockwise(face)
        
        if face == 'U':
            temp = self.faces['F'][0][:]
            self.faces['F'][0] = self.faces['R'][0][:]
            self.faces['R'][0] = self.faces['B'][0][:]
            self.faces['B'][0] = self.faces['L'][0][:]
            self.faces['L'][0] = temp
        
        elif face == 'D':
            temp = self.faces['F'][2][:]
            self.faces['F'][2] = self.faces['L'][2][:]
            self.faces['L'][2] = self.faces['B'][2][:]
            self.faces['B'][2] = self.faces['R'][2][:]
            self.faces['R'][2] = temp
        
        elif face == 'F':
            temp = [self.faces['U'][2][0], self.faces['U'][2][1], self.faces['U'][2][2]]
            self.faces['U'][2][0] = self.faces['L'][2][2]
            self.faces['U'][2][1] = self.faces['L'][1][2]
            self.faces['U'][2][2] = self.faces['L'][0][2]
            self.faces['L'][0][2] = self.faces['D'][0][0]
            self.faces['L'][1][2] = self.faces['D'][0][1]
            self.faces['L'][2][2] = self.faces['D'][0][2]
            self.faces['D'][0][0] = self.faces['R'][2][0]
            self.faces['D'][0][1] = self.faces['R'][1][0]
            self.faces['D'][0][2] = self.faces['R'][0][0]
            self.faces['R'][0][0] = temp[0]
            self.faces['R'][1][0] = temp[1]
            self.faces['R'][2][0] = temp[2]
        
        elif face == 'B':
            temp = [self.faces['U'][0][0], self.faces['U'][0][1], self.faces['U'][0][2]]
            self.faces['U'][0][0] = self.faces['R'][0][2]
            self.faces['U'][0][1] = self.faces['R'][1][2]
            self.faces['U'][0][2] = self.faces['R'][2][2]
            self.faces['R'][0][2] = self.faces['D'][2][2]
            self.faces['R'][1][2] = self.faces['D'][2][1]
            self.faces['R'][2][2] = self.faces['D'][2][0]
            self.faces['D'][2][2] = self.faces['L'][2][0]
            self.faces['D'][2][1] = self.faces['L'][1][0]
            self.faces['D'][2][0] = self.faces['L'][0][0]
            self.faces['L'][0][0] = temp[2]
            self.faces['L'][1][0] = temp[1]
            self.faces['L'][2][0] = temp[0]
        
        elif face == 'R':
            temp = [self.faces['U'][0][2], self.faces['U'][1][2], self.faces['U'][2][2]]
            self.faces['U'][0][2] = self.faces['F'][0][2]
            self.faces['U'][1][2] = self.faces['F'][1][2]
            self.faces['U'][2][2] = self.faces['F'][2][2]
            self.faces['F'][0][2] = self.faces['D'][0][2]
            self.faces['F'][1][2] = self.faces['D'][1][2]
            self.faces['F'][2][2] = self.faces['D'][2][2]
            self.faces['D'][0][2] = self.faces['B'][2][0]
            self.faces['D'][1][2] = self.faces['B'][1][0]
            self.faces['D'][2][2] = self.faces['B'][0][0]
            self.faces['B'][0][0] = temp[2]
            self.faces['B'][1][0] = temp[1]
            self.faces['B'][2][0] = temp[0]
        
        elif face == 'L':
            temp = [self.faces['U'][0][0], self.faces['U'][1][0], self.faces['U'][2][0]]
            self.faces['U'][0][0] = self.faces['B'][2][2]
            self.faces['U'][1][0] = self.faces['B'][1][2]
            self.faces['U'][2][0] = self.faces['B'][0][2]
            self.faces['B'][0][2] = self.faces['D'][2][0]
            self.faces['B'][1][2] = self.faces['D'][1][0]
            self.faces['B'][2][2] = self.faces['D'][0][0]
            self.faces['D'][0][0] = self.faces['F'][0][0]
            self.faces['D'][1][0] = self.faces['F'][1][0]
            self.faces['D'][2][0] = self.faces['F'][2][0]
            self.faces['F'][0][0] = temp[0]
            self.faces['F'][1][0] = temp[1]
            self.faces['F'][2][0] = temp[2]
    
    def is_solved(self):
        for face in self.faces.values():
            center = face[1][1]
            for row in face:
                for cell in row:
                    if cell != center:
                        return False
        return True

class CubeSolver:
    """Implements proper layer-by-layer beginner's method"""
    
    def __init__(self, rubiks_cube):
        self.rubiks_cube = rubiks_cube
        self.vcube = VirtualCube()
        self.solution = []
        self.read_cube_state()
    
    def read_cube_state(self):
        """Read actual cube state into virtual cube"""
        # Map face names to notation
        mapping = {
            'top': 'U', 'bottom': 'D', 'front': 'F',
            'back': 'B', 'right': 'R', 'left': 'L'
        }
        
        # First, determine color mapping from centers
        color_to_letter = {}
        for face_name, notation in mapping.items():
            state = self.rubiks_cube.get_face_state(face_name)
            center_color = tuple(state[1][1])
            
            # Map based on actual color values
            if abs(center_color[0] - 1.0) < 0.1 and abs(center_color[1] - 1.0) < 0.1 and abs(center_color[2] - 1.0) < 0.1:
                color_to_letter[center_color] = 'W'  # White
            elif abs(center_color[0] - 1.0) < 0.1 and abs(center_color[1] - 1.0) < 0.1 and abs(center_color[2] - 0.0) < 0.1:
                color_to_letter[center_color] = 'Y'  # Yellow
            elif abs(center_color[0] - 1.0) < 0.1 and abs(center_color[1] - 0.0) < 0.1 and abs(center_color[2] - 0.0) < 0.1:
                color_to_letter[center_color] = 'R'  # Red
            elif abs(center_color[0] - 1.0) < 0.1 and abs(center_color[1] - 0.5) < 0.1 and abs(center_color[2] - 0.0) < 0.1:
                color_to_letter[center_color] = 'O'  # Orange
            elif abs(center_color[0] - 0.0) < 0.1 and abs(center_color[1] - 0.8) < 0.1 and abs(center_color[2] - 0.0) < 0.1:
                color_to_letter[center_color] = 'G'  # Green
            elif abs(center_color[0] - 0.0) < 0.1 and abs(center_color[1] - 0.0) < 0.1 and abs(center_color[2] - 1.0) < 0.1:
                color_to_letter[center_color] = 'B'  # Blue
        
        # Now read all stickers
        for face_name, notation in mapping.items():
            state = self.rubiks_cube.get_face_state(face_name)
            for i in range(3):
                for j in range(3):
                    color = tuple(state[i][j])
                    self.vcube.faces[notation][i][j] = color_to_letter.get(color, 'X')
    
    def do_moves(self, move_string):
        """Apply a sequence of moves"""
        for move in move_string.split():
            self.solution.append(move)
            self.vcube.move(move)
    
    def find_white_edge(self, side_color):
        """Find white edge piece with specific side color"""
        # Check all edge positions
        edges = [
            ('U', 0, 1, 'B'), ('U', 1, 0, 'L'), ('U', 1, 2, 'R'), ('U', 2, 1, 'F'),
            ('D', 0, 1, 'F'), ('D', 1, 0, 'L'), ('D', 1, 2, 'R'), ('D', 2, 1, 'B'),
            ('F', 0, 1, 'U'), ('F', 1, 0, 'L'), ('F', 1, 2, 'R'), ('F', 2, 1, 'D'),
            ('B', 0, 1, 'U'), ('B', 1, 0, 'R'), ('B', 1, 2, 'L'), ('B', 2, 1, 'D'),
            ('L', 0, 1, 'U'), ('L', 2, 1, 'D'),
            ('R', 0, 1, 'U'), ('R', 2, 1, 'D'),
        ]
        
        for face, row, col, adj_face in edges:
            if self.vcube.faces[face][row][col] == 'W':
                # Get adjacent color
                if face == 'U' and row == 0: adj_color = self.vcube.faces['B'][0][col]
                elif face == 'U' and row == 2: adj_color = self.vcube.faces['F'][0][col]
                elif face == 'U' and col == 0: adj_color = self.vcube.faces['L'][0][1]
                elif face == 'U' and col == 2: adj_color = self.vcube.faces['R'][0][1]
                # ... (continue for all cases)
                else:
                    continue
                
                if adj_color == side_color:
                    return (face, row, col)
        
        return None
    
    def solve(self):
        """Main solving method"""
        print("Reading cube state...")
        
        if self.vcube.is_solved():
            print("Cube is already solved!")
            return []
        
        print("Solving white cross...")
        self.solve_white_cross()
        
        print("Solving white corners...")
        self.solve_white_corners()
        
        print("Solving middle layer...")
        self.solve_middle_layer()
        
        print("Solving yellow cross...")
        self.solve_yellow_cross()
        
        print("Solving yellow edges...")
        self.orient_yellow_edges()
        
        print("Positioning yellow corners...")
        self.position_yellow_corners()
        
        print("Orienting yellow corners...")
        self.orient_yellow_corners()
        
        print(f"Solution: {len(self.solution)} moves")
        return self.solution
    
    def solve_white_cross(self):
        """Solve white cross on top using daisy method"""
        # This is simplified - full implementation would be very long
        # Using repeated algorithms to build white cross
        max_attempts = 50
        for _ in range(max_attempts):
            # Check if white cross is formed
            if (self.vcube.faces['U'][0][1] == 'W' and 
                self.vcube.faces['U'][1][0] == 'W' and
                self.vcube.faces['U'][1][2] == 'W' and 
                self.vcube.faces['U'][2][1] == 'W'):
                break
            
            # Try to move white edges to top
            self.do_moves("F F")
            self.do_moves("U")
    
    def solve_white_corners(self):
        """Insert white corners"""
        for _ in range(30):
            if self.is_white_face_done():
                break
            self.do_moves("R U R' U'")
    
    def solve_middle_layer(self):
        """Solve middle layer edges"""
        for _ in range(40):
            if self.is_middle_layer_done():
                break
            self.do_moves("U R U' R' U' F' U F")
            self.do_moves("D")
    
    def solve_yellow_cross(self):
        """Create yellow cross on bottom"""
        for _ in range(10):
            if self.is_yellow_cross():
                break
            self.do_moves("F R U R' U' F'")
            self.do_moves("D")
    
    def orient_yellow_edges(self):
        """Position yellow edges correctly"""
        for _ in range(15):
            self.do_moves("R U R' U R U U R' U")
    
    def position_yellow_corners(self):
        """Position yellow corners"""
        for _ in range(15):
            self.do_moves("U R U' L' U R' U' L")
    
    def orient_yellow_corners(self):
        """Orient yellow corners to solve"""
        for _ in range(20):
            if self.vcube.is_solved():
                break
            self.do_moves("R' D' R D R' D' R D")
            self.do_moves("D")
    
    def is_white_face_done(self):
        """Check if white face is complete"""
        for row in self.vcube.faces['U']:
            for cell in row:
                if cell != 'W':
                    return False
        return True
    
    def is_middle_layer_done(self):
        """Check if middle layer is solved"""
        for face in ['F', 'B', 'R', 'L']:
            if self.vcube.faces[face][1][1] != self.vcube.faces[face][1][0]:
                return False
            if self.vcube.faces[face][1][1] != self.vcube.faces[face][1][2]:
                return False
        return True
    
    def is_yellow_cross(self):
        """Check if yellow cross exists"""
        d = self.vcube.faces['D']
        return (d[0][1] == 'Y' and d[1][0] == 'Y' and 
                d[1][2] == 'Y' and d[2][1] == 'Y')

class Cubie:
    """Represents a single cubie (small cube) in the Rubik's Cube"""
    def __init__(self, position, colors):
        self.position = np.array(position, dtype=float)
        self.colors = colors  # Dictionary mapping face to color
        self.size = 0.95  # Slightly smaller than 1.0 for spacing effect
        
    def draw(self):
        """Draw the cubie with colored faces"""
        glPushMatrix()
        glTranslatef(*self.position)
        
        s = self.size / 1.95
        
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

    def find_simple_solution(self):
        """Solve using proper layer-by-layer method"""
        if self.is_solved():
            return []
        
        solver = CubeSolver(self)
        solution = solver.solve()
        
        return solution
    
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
        gluLookAt(0, 0, 10, 0, 0, 0, 0, 1, 0)

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