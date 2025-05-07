import pygame as pg
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

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


def main():
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
    pg.display.set_caption("PyOpenGL Text Editor")
    clock = pg.time.Clock()

    init_opengl()

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False

        glClear(GL_COLOR_BUFFER_BIT)

        pg.display.flip()
        clock.tick(FPS)

    pg.quit()

if __name__ == '__main__':
    main()