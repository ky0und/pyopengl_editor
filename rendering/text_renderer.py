import pygame as pg
from OpenGL.GL import *
from pygame import freetype

if not freetype.get_init():
    freetype.init()

class TextRenderer:
    def __init__(self, font_path, font_size, color=(200, 200, 200)):
        try:
            self.font = freetype.Font(font_path, font_size)
        except Exception as e:
            print(f"Error loading font {font_path}: {e}")
            print("Falling back to default system font.")
            self.font = freetype.SysFont("monospace", font_size)
        
        self.font_size = font_size
        self.color = color
        self.ascender = self.font.get_sized_ascender()
        self.descender = self.font.get_sized_descender()
        self.line_height = self.get_highest_glyph_height()

    def get_highest_glyph_height(self) -> int:
        """Returns the height of the highest glyph"""

        # Each metric is a tuple: (min_x, max_x, min_y, max_y, horizontal_advance_x, vertical_advance_y)
        metrics = self.font.get_metrics("#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~';")
        max_y = max(metrics, key=lambda x: x[3])[3]
        return max_y + abs(self.descender)

    def render_text_to_texture(self, text_string: str):
        """
        Renders a string to a Pygame surface of FIXED LINE HEIGHT, with text
        baseline-aligned. Then converts this surface to an OpenGL texture.
        Returns (texture_id, actual_text_width, fixed_texture_height).
        """
        actual_text_width = self.get_string_width(text_string)

        if not text_string.strip() and actual_text_width == 0:
            return None, 0, self.line_height
        
        if actual_text_width == 0 and text_string:
             actual_text_width = self.font.get_rect(text_string).width
        
        surface_width = max(1, actual_text_width)
        surface_height = self.line_height

        target_surface = pg.Surface((surface_width, surface_height), pg.SRCALPHA)
        target_surface.fill((0,0,0,0))

        try:
            self.font.origin = True
            self.font.render_to(target_surface, (0, self.ascender), text_string, fgcolor=self.color)
            self.font.origin = False
        except pg.error as e:
            print(f"Pg error rendering text '{text_string[:20]}...': {e}")
            return None, actual_text_width, self.line_height
        except Exception as e:
            print(f"General error rendering text '{text_string[:20]}...': {e}")
            return None, actual_text_width, self.line_height

        # Convert Pygame surface to OpenGL texture data
        texture_data = pg.image.tostring(target_surface, "RGBA", True)

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface_width, surface_height, 0, 
                     GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        glBindTexture(GL_TEXTURE_2D, 0) # Unbind

        return tex_id, actual_text_width, surface_height # surface_height is self.line_height
    
    def draw_text(self, text_texture_id, x, y, width, height):
        """Draws a pre-rendered text texture at (x, y)."""
        if text_texture_id is None:
            return

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, text_texture_id)

        glBegin(GL_QUADS)

        # Tex Coords (s, t): (0,0) bottom-left, (1,0) bottom-right, (1,1) top-right, (0,1) top-left
        glTexCoord2f(0, 0); glVertex2f(x, y + height)       # Bottom-left
        glTexCoord2f(1, 0); glVertex2f(x + width, y + height) # Bottom-right
        glTexCoord2f(1, 1); glVertex2f(x + width, y)        # Top-right
        glTexCoord2f(0, 1); glVertex2f(x, y)                 # Top-left
        glEnd()

        glDisable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, 0)

    def get_char_width(self, char):
        """Gets the advance width of a single character."""
        if not char or len(char) != 1:
            return 0
        _surf, rect = self.font.render(char, fgcolor=(0,0,0))
        return rect.width if rect else 0 # rect.width is advance

    def get_string_width(self, text_string: str) -> int:
        """Calculates the total advance width of a string using font metrics."""
        if not text_string:
            return 0
        
        metrics = self.font.get_metrics(text_string)
        if not metrics:
            # This can happen for strings with no renderable glyphs or just spaces.
            # Fallback to get_rect for such cases, as it considers the space taken.
            return self.font.get_rect(text_string).width

        total_advance = 0
        for metric in metrics:
            if metric: # Each metric is a tuple: (min_x, max_x, min_y, max_y, horizontal_advance_x, vertical_advance_y)
                total_advance += metric[4]  # horizontal_advance_x
        return int(round(total_advance))

    def cleanup_texture(self, texture_id):
        """Deletes an OpenGL texture."""
        if texture_id is not None:
            glDeleteTextures(1, [texture_id])