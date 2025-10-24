# pyRubik

A small OpenGL + Pygame Rubik's Cube visualizer and solver (Kociemba-style).  

## Prerequisites
- Python 3.10+ recommended
- OpenGL drivers for your GPU

## Setup (Unix)
1. ```bash
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. (Optional) put a background image named `background.jpg` in the project root if you enabled background drawing.


## Troubleshooting
- ModuleNotFoundError: No module named 'OpenGL' — install PyOpenGL:
  ```bash
  pip install PyOpenGL PyOpenGL_accelerate
  ```
- Black screen after adding background:
  - Ensure `background.jpg` exists and is a valid image in the project root.
  - Ensure Pillow converted the image to RGBA before uploading to OpenGL.
  - If texture fails, run from terminal to see printed errors.
- If text or textures look wrong, check OpenGL pixel unpack alignment:
  `glPixelStorei(GL_UNPACK_ALIGNMENT, 1)`

## Notes