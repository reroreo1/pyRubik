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
        self._vertex_cache = {}

    def _generate_rounded_square_vertices(self, size):
        cache_key = (size, self.corner_radius, self.corner_segments)
        if cache_key in self._vertex_cache:
            return self._vertex_cache[cache_key]
        vertices = []
        half_size = size / 2
        inset = half_size - self.corner_radius
        corners = [
            (inset, inset),    # Top-right
            (-inset, inset),   # Top-left
            (-inset, -inset),  # Bottom-left
            (inset, -inset)    # Bottom-right
        ]
        start_angles = [0, 90, 180, 270]
        for (cx, cy), start_angle in zip(corners, start_angles):
            for i in range(self.corner_segments + 1):
                angle = np.radians(start_angle + i * 90 / self.corner_segments)
                x = cx + self.corner_radius * np.cos(angle)
                y = cy + self.corner_radius * np.sin(angle)
                vertices.append((x, y))
        self._vertex_cache[cache_key] = vertices
        return vertices

    def _draw_rounded_face(self, face_name, center, normal, up, color):
        vertices_2d = self._generate_rounded_square_vertices(self.size)
        right = np.cross(normal, up)
        glNormal3f(*normal)
        glColor3f(*color)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3fv(center)
        for x, y in vertices_2d:
            vertex = center + x * right + y * up
            glVertex3fv(vertex)
        x, y = vertices_2d[0]
        vertex = center + x * right + y * up
        glVertex3fv(vertex)
        glEnd()
        glColor3f(0, 0, 0)
        glLineWidth(1.5)
        glBegin(GL_LINE_LOOP)
        for x, y in vertices_2d:
            vertex = center + x * right + y * up
            glVertex3fv(vertex)
        glEnd()

    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        s = self.size / 2
        faces = [
            ('front', [0, 0, s], [0, 0, 1], [0, 1, 0]),
            ('back', [0, 0, -s], [0, 0, -1], [0, 1, 0]),
            ('top', [0, s, 0], [0, 1, 0], [0, 0, -1]),
            ('bottom', [0, -s, 0], [0, -1, 0], [0, 0, 1]),
            ('right', [s, 0, 0], [1, 0, 0], [0, 1, 0]),
            ('left', [-s, 0, 0], [-1, 0, 0], [0, 1, 0])
        ]
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        for face_name, center, normal, up in faces:
            color = self.colors.get(face_name, (0.1, 0.1, 0.1))
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
        rad = np.radians(angle)
        cos_a = np.cos(rad)
        sin_a = np.sin(rad)
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
        self.position = rotation_matrix @ self.position
        pass

