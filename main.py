import pygame as pg
from pygame.locals import *
from OpenGL.GL import *
from editor.buffer import Buffer
from rendering.renderer import EditorRenderer
from editor.cursor import Cursor
from editor.modes import EditorMode, EditorState
from input_handling.keyboard_handler import KeyboardHandler

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
FPS = 60

def init_opengl():
    """Initialize basic OpenGL settings."""
    glViewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_DEPTH_TEST)

FONT_PATH = "assets/fonts/Consolas.ttf"
FONT_SIZE = 24

def main():
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
    pg.display.set_caption("PyOpenGL Text Editor")
    clock = pg.time.Clock()

    init_opengl()

    # Initialize editor components
    editor_buffer = Buffer()
    editor_renderer = EditorRenderer(FONT_PATH, FONT_SIZE)
    cursor = Cursor()
    editor_state = EditorState()

    keyboard_handler = KeyboardHandler(editor_buffer, editor_state, cursor, editor_renderer)
    keyboard_handler._update_syntax_highlighting_for_buffer()

    editor_renderer._calculate_visible_lines(SCREEN_HEIGHT)

    running = True
    while running:
        dt = clock.tick(FPS)
        action_taken = False

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            
            if event.type == pg.KEYDOWN:

                action_taken_by_handler = keyboard_handler.handle_keydown(event)

                if action_taken_by_handler & (editor_state.mode != EditorMode.COMMAND):
                    cursor.visible = True
                    cursor.blink_timer = 0
                
        if cursor.line < editor_state.viewport_start_line:
            editor_state.viewport_start_line = cursor.line
        elif cursor.line >= editor_state.viewport_start_line + editor_renderer.visible_lines_in_viewport:
            editor_state.viewport_start_line = cursor.line - editor_renderer.visible_lines_in_viewport + 1
        
        # Clamp viewport_start_line to be valid
        if editor_buffer.get_line_count() > 0:
             max_start_line = max(0, editor_buffer.get_line_count() - editor_renderer.visible_lines_in_viewport)
             editor_state.viewport_start_line = max(0, min(editor_state.viewport_start_line, max_start_line))
        else: # Buffer is empty
             editor_state.viewport_start_line = 0

        # Fix cursor if went out of frame for some reason
        if cursor.line < editor_state.viewport_start_line:
            editor_state.viewport_start_line = cursor.line
        elif cursor.line >= editor_state.viewport_start_line + editor_renderer.visible_lines_in_viewport:
            new_start = cursor.line - editor_renderer.visible_lines_in_viewport + 1
            editor_state.viewport_start_line = max(0, new_start)

        # Re-clamp after the general scroll-to-view adjustment
        if editor_buffer.get_line_count() > 0:
                max_possible_start_line = max(0, editor_buffer.get_line_count() - editor_renderer.visible_lines_in_viewport)
                editor_state.viewport_start_line = max(0, min(editor_state.viewport_start_line, max_possible_start_line))
        else:
                editor_state.viewport_start_line = 0

        cursor.blink_timer += dt
        if cursor.blink_timer >= cursor.blink_rate:
            cursor.blink_timer = 0
            cursor.visible = not cursor.visible

        glClear(GL_COLOR_BUFFER_BIT)
        editor_renderer.render_buffer(editor_buffer, editor_state, SCREEN_HEIGHT)
        editor_renderer.render_cursor(cursor, editor_buffer, editor_state, cursor.visible)
        editor_renderer.render_status_bar(editor_state, editor_buffer, SCREEN_WIDTH, SCREEN_HEIGHT)

        pg.display.flip()

    editor_renderer.cleanup()
    pg.quit()

if __name__ == '__main__':
    main()