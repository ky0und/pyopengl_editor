import pygame as pg
from pygame.locals import *
from OpenGL.GL import *
from editor.buffer import Buffer
from rendering.renderer import EditorRenderer
from editor.cursor import Cursor

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



FONT_PATH = "assets/fonts/Consolas.ttf" # Or your font
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

    cursor_blink_timer = 0
    cursor_visible = True
    CURSOR_BLINK_RATE = 500 # milliseconds

    running = True
    while running:
        dt = clock.tick(FPS)

        action_taken = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            if event.type == pg.KEYDOWN:
                current_cursor_line = cursor.line

                if event.key == pg.K_ESCAPE:
                    running = False
                elif event.key == pg.K_RETURN:
                    editor_renderer.invalidate_line_cache(cursor.line)
                    
                    editor_renderer.handle_lines_inserted(insert_idx=cursor.line + 1, num_inserted_lines=1)
                    
                    editor_buffer.split_line(cursor.line, cursor.col)
                    
                    cursor.line += 1
                    cursor.col = 0
                    action_taken = True
                    
                elif event.key == pg.K_BACKSPACE:
                    if cursor.col > 0: # Character deleted within the current line.
                        editor_renderer.invalidate_line_cache(cursor.line)
                        editor_buffer.delete_char(cursor.line, cursor.col)
                        cursor.col -= 1
                        action_taken = True
                    elif cursor.line > 0: # Backspace at start of a line, merging with previous
                        editor_renderer.invalidate_line_cache(cursor.line - 1)
                        editor_renderer.handle_lines_deleted(delete_idx=cursor.line, num_deleted_lines=1)

                        prev_line_len = len(editor_buffer.get_line(cursor.line - 1))
                        editor_buffer.delete_char(cursor.line, 0)
                        
                        cursor.line -= 1
                        cursor.col = prev_line_len
                        action_taken = True

                elif event.key == pg.K_LEFT:
                    cursor.move_left(editor_buffer)
                elif event.key == pg.K_RIGHT:
                    cursor.move_right(editor_buffer)
                elif event.key == pg.K_UP:
                    cursor.move_up(editor_buffer)
                elif event.key == pg.K_DOWN:
                    cursor.move_down(editor_buffer)
                elif event.unicode:
                    if event.unicode.isprintable() or event.unicode == '\t':
                        # Only current line content changes.
                        editor_renderer.invalidate_line_cache(cursor.line)
                        
                        if event.unicode == '\t':
                             for _ in range(4):
                                 editor_buffer.insert_char(cursor.line, cursor.col, ' ')
                                 cursor.col += 1
                        else:
                            editor_buffer.insert_char(cursor.line, cursor.col, event.unicode)
                            cursor.col += 1
                        action_taken = True
                
                if action_taken:
                    cursor_visible = True
                    cursor_blink_timer = 0
                    
        cursor_blink_timer += dt
        if cursor_blink_timer >= CURSOR_BLINK_RATE:
            cursor_blink_timer = 0
            cursor_visible = not cursor_visible

        glClear(GL_COLOR_BUFFER_BIT)
        editor_renderer.render_buffer(editor_buffer)
        editor_renderer.render_cursor(cursor, editor_buffer, cursor_visible)

        pg.display.flip()

    editor_renderer.cleanup()
    pg.quit()

if __name__ == '__main__':
    main()