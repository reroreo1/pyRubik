import os
import subprocess
import threading

# Suppress libdecor warnings on Wayland
os.environ.setdefault('SDL_VIDEODRIVER', 'x11')
from PIL import Image
from rubiks_cube import RubiksCube
import pygame
from pygame.locals import *
from OpenGL.GLU import *
from OpenGL.GL import *


class CubeViewer:
    """Main application class"""
    def __init__(self):
        pygame.init()
        self.width, self.height = 1200, 800
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Rubik's Cube Solver")
        self.background_texture = self.load_background_texture()
        self.loading_texture = self.load_loading_texture()
        
        # Initialize solver in background
        self.solver_initialized = False
        self.solver_progress = 0  # 0-100 for progress bar
        self.solver_phase = "Loading..."  # Current phase text
        self.solver_thread = threading.Thread(target=self._initialize_solver, daemon=True)
        self.solver_thread.start()
        
        # Create loading cube with auto-animation and slower speed (5.0 instead of 10.0)
        self.loading_cube = RubiksCube(auto_animate=True, speed=5.0)
        
        # Main cube (NO auto-animation - starts solved, normal speed 10.0)
        self.cube = RubiksCube(auto_animate=False, speed=10.0)
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
        self.auto_rotate = True
        
        # Font for text display
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Clock for FPS
        self.clock = pygame.time.Clock()
    
    def _initialize_solver(self):
        """Initialize solver by running it with test input (background thread)"""
        try:
            solver_dir = os.path.join(os.path.dirname(__file__), 'solver')
            solver_path = os.path.join(solver_dir, 'twophase')
            
            # Check if pruning tables already exist
            data1_path = os.path.join(solver_dir, 'data1.dat')
            data2_path = os.path.join(solver_dir, 'data2.dat')
            
            if os.path.exists(data1_path) and os.path.exists(data2_path):
                # Tables already exist, just mark as ready
                self.solver_progress = 100
                self.solver_phase = "Ready!"
                print("✓ Solver tables already initialized")
                self.solver_initialized = True
                return
            
            test_input = "DL FD BL FR BD UL UR BU LF FU RB DR DLB RBU LUB DRF FLD RUF BRD FUL\n"
            
            # Run solver with unbuffered output to generate tables
            process = subprocess.Popen(
                [solver_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
                cwd=solver_dir
            )
            
            # Send input
            process.stdin.write(test_input)
            process.stdin.close()
            
            # Read output line by line in real-time
            for line in process.stdout:
                line = line.strip()
                if line:
                    if '[phase1:' in line:
                        self.solver_phase = "Generating Phase 1..."
                        try:
                            percent = int(line.split('[phase1:')[1].split('%')[0])
                            self.solver_progress = max(1, min(50, percent // 2))
                        except:
                            pass
                    elif '[phase2:' in line:
                        self.solver_phase = "Generating Phase 2..."
                        try:
                            percent = int(line.split('[phase2:')[1].split('%')[0])
                            self.solver_progress = 50 + max(1, min(50, percent // 2))
                        except:
                            pass
            
            process.wait(timeout=300)
            self.solver_progress = 100
            self.solver_phase = "Ready!"
            print("✓ Solver initialized successfully")
            self.solver_initialized = True
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except:
                pass
            print("⚠ Solver initialization timed out")
            self.solver_progress = 100
            self.solver_initialized = True
        except Exception as e:
            print(f"⚠ Solver initialization error: {e}")
            self.solver_progress = 100
            self.solver_initialized = True
        
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
            image_path = os.path.join(os.path.dirname(__file__), "./images/background.jpg")
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

    def load_loading_texture(self):
        """Load and setup loading screen image"""
        try:
            image_path = os.path.join(os.path.dirname(__file__), "images", "loading.jpg")
            image = Image.open(image_path)
            ix, iy = image.size
            image_data = image.tobytes("raw", "RGBA", 0, -1)
        except Exception as e:
            print(f"Could not load loading image: {e}")
            return None

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
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
        center_x = self.width // 2
        
        if self.cube.shuffling and self.cube.move_queue:
            remaining_moves = list(self.cube.move_queue)
            current_move = self.cube.animator.current_move if self.cube.animator.is_animating() else None
            done = self.cube.shuffle_total - len(remaining_moves)
            
            # Display shuffling status (bright yellow, centered)
            status_text = f"SHUFFLING  {done}/{self.cube.shuffle_total}"
            text_width = len(status_text) * 10
            self.draw_text_2d(status_text, center_x - text_width // 2, 40, self.font, (255, 255, 50))
            
            # Display current move (centered, below cube, above next moves)
            if current_move:
                move_text = f"[ {current_move} ]"
                self.draw_text_2d(move_text, center_x - 25, self.height - 100, self.font, (255, 255, 255))
        
        elif self.cube.solving and self.cube.current_solution:
            remaining_moves = list(self.cube.move_queue)
            current_move = self.cube.animator.current_move if self.cube.animator.is_animating() else None
            total = len(self.cube.current_solution)
            done = total - len(remaining_moves)
            
            # Display solving status (cube green, centered)
            status_text = f"SOLVING  {done}/{total}"
            text_width = len(status_text) * 10
            self.draw_text_2d(status_text, center_x - text_width // 2, 40, self.font, (0, 204, 0))
            
            # Display current move (centered, below cube, above next moves)
            if current_move:
                move_text = f"[ {current_move} ]"
                self.draw_text_2d(move_text, center_x - 25, self.height - 100, self.font, (255, 255, 255))

            # Display move sequence (centered at bottom)
            if remaining_moves:
                sequence_text = "Next: " + " ".join(list(remaining_moves)[:8])
                if len(remaining_moves) > 8:
                    sequence_text += " ..."
                text_width = len(sequence_text) * 7
                self.draw_text_2d(sequence_text, center_x - text_width // 2, self.height - 60, self.small_font, (220, 220, 220))
        
        elif self.cube.animator.is_animating():
            move_text = f"[ {self.cube.animator.current_move} ]"
            self.draw_text_2d(move_text, center_x - 25, self.height - 100, self.font, (255, 255, 255))
    
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
    
    def draw_loading_screen(self):
        """Draw loading screen with animated cube overlay and progress bar"""
        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Draw loading image background
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
        
        if self.loading_texture:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.loading_texture)
            glColor4f(1, 1, 1, 1)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex2f(0, 0)
            glTexCoord2f(1, 0); glVertex2f(self.width, 0)
            glTexCoord2f(1, 1); glVertex2f(self.width, self.height)
            glTexCoord2f(0, 1); glVertex2f(0, self.height)
            glEnd()
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        # Draw 3D animated cube on top (center of screen)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(45, self.width / self.height, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Position and rotate cube in center
        gluLookAt(0, 0, 10, 0, 0, 0, 0, 1, 0)
        glRotatef(25, 1, 0, 0)
        glRotatef(45, 0, 1, 0)
        
        # Draw the animated loading cube
        self.loading_cube.draw()
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        # Draw progress bar
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
        
        bar_width = 400
        bar_height = 20
        bar_x = (self.width - bar_width) // 2
        bar_y = self.height - 60
        
        # Progress bar background (dark)
        glColor4f(0.2, 0.2, 0.2, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y)
        glVertex2f(bar_x + bar_width, bar_y)
        glVertex2f(bar_x + bar_width, bar_y + bar_height)
        glVertex2f(bar_x, bar_y + bar_height)
        glEnd()
        
        # Progress bar fill (white)
        progress_width = bar_width * (self.solver_progress / 100.0)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y)
        glVertex2f(bar_x + progress_width, bar_y)
        glVertex2f(bar_x + progress_width, bar_y + bar_height)
        glVertex2f(bar_x, bar_y + bar_height)
        glEnd()
        
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def render(self):
        # Show loading screen while solver initializes
        if not self.solver_initialized:
            # Update loading cube animation
            self.loading_cube.update_animation()
            self.draw_loading_screen()
            return
        
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
            self.target_rotation_y += 0.15

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