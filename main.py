import pygame as pg
from pygame.locals import *
from OpenGL.GL import *
from editor.buffer import Buffer
from rendering.renderer import EditorRenderer
from editor.cursor import Cursor
from editor.modes import EditorMode, EditorState

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
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
FONT_SIZE = 30

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

    running = True
    while running:
        dt = clock.tick(FPS)
        action_taken = False

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            
            if event.type == pg.KEYDOWN:
                action_taken = False

                # --- Mode Independent Keys ---
                if event.key == pg.K_ESCAPE:
                    if editor_state.mode == EditorMode.INSERT:
                        editor_state.switch_to_mode(EditorMode.NORMAL)
                        current_line_text = editor_buffer.get_line(cursor.line)
                        if cursor.col > 0 and cursor.col <= len(current_line_text):
                             cursor.col -= 1
                        action_taken = True


                # --- NORMAL MODE ---
                if editor_state.mode == EditorMode.NORMAL:
                    if not action_taken:
                        if event.key == pg.K_i: # Insert mode (before cursor)
                            editor_state.switch_to_mode(EditorMode.INSERT)
                            action_taken = True
                        elif event.key == pg.K_a: # Insert mode (append after cursor)
                            current_line_text = editor_buffer.get_line(cursor.line)
                            if cursor.col < len(current_line_text): # Don't go past EOL
                                cursor.col += 1
                            editor_state.switch_to_mode(EditorMode.INSERT)
                            action_taken = True
                        # TODO Add 'o' and 'O' commands that relate to https://vim.rtorr.com/
                        elif event.key == pg.K_h:
                            cursor.move_left(editor_buffer, mode_is_normal=True)
                            action_taken = True
                        elif event.key == pg.K_j:
                            cursor.move_down(editor_buffer)
                            action_taken = True
                        elif event.key == pg.K_k:
                            cursor.move_up(editor_buffer)
                            action_taken = True
                        elif event.key == pg.K_l:
                            cursor.move_right(editor_buffer, mode_is_normal=True)
                            action_taken = True
                        # TODO Add other normal mode commands here (x, dd, yy, p etc.)

                # --- INSERT MODE ---
                elif editor_state.mode == EditorMode.INSERT:
                    if not action_taken:
                        if event.key == pg.K_RETURN:
                            editor_renderer.invalidate_line_cache(cursor.line)
                            editor_renderer.handle_lines_inserted(insert_idx=cursor.line + 1, num_inserted_lines=1)
                            editor_buffer.split_line(cursor.line, cursor.col)
                            cursor.line += 1
                            cursor.col = 0
                            action_taken = True
                        elif event.key == pg.K_BACKSPACE:
                            if cursor.col > 0:
                                editor_renderer.invalidate_line_cache(cursor.line)
                                editor_buffer.delete_char(cursor.line, cursor.col)
                                cursor.col -= 1
                            elif cursor.line > 0:
                                editor_renderer.invalidate_line_cache(cursor.line - 1)
                                editor_renderer.handle_lines_deleted(delete_idx=cursor.line, num_deleted_lines=1)
                                prev_line_len = len(editor_buffer.get_line(cursor.line - 1))
                                editor_buffer.delete_char(cursor.line, 0)
                                cursor.line -= 1
                                cursor.col = prev_line_len
                            action_taken = True
                        elif event.key == pg.K_LEFT:
                            cursor.move_left(editor_buffer, mode_is_normal=False)
                            action_taken = True
                        elif event.key == pg.K_RIGHT:
                            cursor.move_right(editor_buffer, mode_is_normal=False)
                            action_taken = True
                        elif event.key == pg.K_UP:
                            cursor.move_up(editor_buffer)
                            action_taken = True
                        elif event.key == pg.K_DOWN:
                            cursor.move_down(editor_buffer)
                            action_taken = True
                        elif event.unicode:
                            if event.unicode.isprintable() or event.unicode == '\t':
                                editor_renderer.invalidate_line_cache(cursor.line)
                                if event.unicode == '\t':
                                     for _ in range(4): # Simple tab to 4 spaces
                                         editor_buffer.insert_char(cursor.line, cursor.col, ' ')
                                         cursor.col += 1
                                else:
                                    editor_buffer.insert_char(cursor.line, cursor.col, event.unicode)
                                    cursor.col += 1
                                action_taken = True
                
                if action_taken:
                    cursor.visible = True
                    cursor.blink_timer = 0
                    
        cursor.blink_timer += dt
        if cursor.blink_timer >= cursor.blink_rate:
            cursor.blink_timer = 0
            cursor.visible = not cursor.visible

        glClear(GL_COLOR_BUFFER_BIT)
        editor_renderer.render_buffer(editor_buffer)
        editor_renderer.render_cursor(cursor, editor_buffer, cursor.visible)
        editor_renderer.render_status_bar(editor_state, SCREEN_WIDTH, SCREEN_HEIGHT)

        pg.display.flip()

    editor_renderer.cleanup()
    pg.quit()

if __name__ == '__main__':
    main()