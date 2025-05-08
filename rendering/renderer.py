from .text_renderer import TextRenderer
from OpenGL.GL import *

class EditorRenderer:
    def __init__(self, font_path, font_size):
        self.text_renderer = TextRenderer(font_path, font_size, color=(220, 220, 220))
        self.line_height = self.text_renderer.line_height
        self.visible_lines_in_viewport = 0
        self.padding_x = 5
        self.padding_y = 5
        # Key: line_index, Value: (texture_id, actual_text_width, texture_height, text_content_str)
        self.line_texture_cache = {}
        self.cursor_color = (240, 240, 240, 255)
        self.cursor_width = 2
        status_font_size = max(12, int(font_size * 0.8))

        try:
            self.status_text_renderer = TextRenderer(font_path, status_font_size, color=(180, 180, 180))
        except Exception as e:
            print(f"Could not create status_text_renderer: {e}, falling back.")
            self.status_text_renderer = self.text_renderer

        try:
            self.line_num_renderer = TextRenderer(font_path, font_size, color=(100, 100, 120))
        except Exception:
            self.line_num_renderer = self.text_renderer

        self.line_number_width = 0
        self.gutter_padding = 5            

      
    def _calculate_visible_lines(self, screen_height):
        """Calculate how many lines fit in the main text area."""
        available_height = screen_height
        available_height -= (2 * self.padding_y)

        if hasattr(self, 'status_text_renderer') and self.status_text_renderer:
            available_height -= self.status_text_renderer.line_height
        
        if self.line_height > 0:
            self.visible_lines_in_viewport = max(1, int(available_height / self.line_height))
        else:
            self.visible_lines_in_viewport = 25



    def _calculate_line_number_width(self, buffer_obj):
        """Calculates the width needed for the line number gutter."""
        max_line_num = buffer_obj.get_line_count()
        if max_line_num == 0:
            return self.text_renderer.get_string_width("1") + self.gutter_padding # Min width for at least "1"
        
        return self.line_num_renderer.get_string_width(str(max_line_num)) + self.gutter_padding

    def render_buffer(self, buffer_obj, editor_state, screen_height_param):
        if self.visible_lines_in_viewport == 0:
             self._calculate_visible_lines(screen_height_param)

        current_y = self.padding_y
        self.line_number_width = self._calculate_line_number_width(buffer_obj)  
        text_area_start_x = self.padding_x + self.line_number_width

        # Determine the range of lines to render based on viewport
        start_render_line = editor_state.viewport_start_line
        end_render_line = min(buffer_obj.get_line_count(), 
                              start_render_line + self.visible_lines_in_viewport)

        for i in range(start_render_line, end_render_line):
            display_line_index = i - start_render_line

            line_num_str = str(i + 1) # Line numbers are 1-indexed for display
            ln_tex_id, ln_w, ln_h = self.line_num_renderer.render_text_to_texture(line_num_str)

            ln_y_pos = self.padding_y + (display_line_index * self.line_height)
            ln_tex_id, ln_w, ln_h = self.line_num_renderer.render_text_to_texture(line_num_str)

            if ln_tex_id:
                ln_x_pos = self.padding_x + (self.line_number_width - self.gutter_padding - ln_w)
                self.line_num_renderer.draw_text(ln_tex_id, ln_x_pos, current_y, ln_w, ln_h)
                self.line_num_renderer.cleanup_texture(ln_tex_id)

            line_text = buffer_obj.get_line(i)
            cached_entry = self.line_texture_cache.get(i)
            texture_id, tex_w, tex_h = None, 0, self.line_height 

            if cached_entry and cached_entry[3] == line_text: # Content matches
                texture_id, tex_w, tex_h_cached, _ = cached_entry
                tex_h = tex_h_cached 
            else: # Not cached or text changed
                if cached_entry: # Text changed for this line number, cleanup old
                    self.text_renderer.cleanup_texture(cached_entry[0])
                
                texture_id, tex_w, tex_h_rendered = self.text_renderer.render_text_to_texture(line_text)
                # tex_h_rendered should be self.line_height
                self.line_texture_cache[i] = (texture_id, tex_w, tex_h_rendered, line_text)
                tex_h = tex_h_rendered

            if texture_id is not None: # tex_w can be 0 for empty lines
                 self.text_renderer.draw_text(texture_id, text_area_start_x, current_y, tex_w, tex_h)
            
            current_y += self.line_height

        # Pruning for lines that no longer exist at the end of the buffer
        max_buffer_line = buffer_obj.get_line_count() -1
        keys_to_prune = [k for k in self.line_texture_cache if k > max_buffer_line]
        for k in keys_to_prune:
            self._cleanup_cached_texture(k)


    def render_cursor(self, cursor_obj, buffer_obj, editor_state, is_visible=True):
        if not is_visible:
            return
        
        # Cursor position relative to viewport
        cursor_display_line = cursor_obj.line - editor_state.viewport_start_line

        # Only render cursor if it's within the visible part of the viewport
        if not (0 <= cursor_display_line < self.visible_lines_in_viewport):
            return

        text_area_start_x = self.padding_x + self.line_number_width 

        line_num = cursor_obj.line
        col_num = cursor_obj.col

        cursor_display_line_index = line_num - editor_state.viewport_start_line
        
        if not (0 <= cursor_display_line_index < self.visible_lines_in_viewport):
            return

        current_line_text = buffer_obj.get_line(line_num)
        if current_line_text is None: return

        text_before_cursor = current_line_text[:col_num]
        
        cursor_x_offset = text_area_start_x + self.text_renderer.get_string_width(text_before_cursor)
        
        cursor_y_offset = self.padding_y + (cursor_display_line_index * self.line_height)

        glColor4ub(self.cursor_color[0], self.cursor_color[1], self.cursor_color[2], self.cursor_color[3])
        glDisable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glVertex2f(cursor_x_offset, cursor_y_offset)                                  # Top-left
        glVertex2f(cursor_x_offset + self.cursor_width, cursor_y_offset)              # Top-right
        glVertex2f(cursor_x_offset + self.cursor_width, cursor_y_offset + self.line_height) # Bottom-right
        glVertex2f(cursor_x_offset, cursor_y_offset + self.line_height)               # Bottom-left
        glEnd()

    def render_status_bar(self, editor_state, screen_width, screen_height):
        """Renders the status bar on the bottom left of the screen."""
        if not hasattr(self, 'status_text_renderer'):
            return

        mode_name = f"-- {editor_state.mode.name} --"
        
        texture_id, tex_w, tex_h = \
            self.status_text_renderer.render_text_to_texture(mode_name)

        if texture_id:
            x_pos = self.padding_x 
            y_pos = screen_height - tex_h - self.padding_y 

            self.status_text_renderer.draw_text(texture_id, x_pos, y_pos, tex_w, tex_h)
            self.status_text_renderer.cleanup_texture(texture_id)

    def _cleanup_cached_texture(self, line_num):
        """Helper to remove and cleanup a single cached texture by line number."""
        entry = self.line_texture_cache.pop(line_num, None)
        if entry:
            self.text_renderer.cleanup_texture(entry[0])

    def cleanup(self):
        """Cleanup all cached textures."""
        for texture_id, _, _, _ in self.line_texture_cache.values():
            self.text_renderer.cleanup_texture(texture_id)
        self.line_texture_cache.clear()

    def invalidate_line_cache(self, line_num):
        """Invalidates a single line if its content changes (but line num stays)."""
        self._cleanup_cached_texture(line_num)
    

    def handle_lines_inserted(self, insert_idx, num_inserted_lines):
        """Shift cache entries when lines are inserted."""
        if num_inserted_lines <= 0:
            return

        keys_to_shift = sorted([k for k in self.line_texture_cache if k >= insert_idx], reverse=True)

        for old_idx in keys_to_shift:
            new_idx = old_idx + num_inserted_lines
            self.line_texture_cache[new_idx] = self.line_texture_cache.pop(old_idx)
        
    def handle_lines_deleted(self, delete_idx, num_deleted_lines):
        """Remove deleted lines from cache and shift subsequent entries."""
        if num_deleted_lines <= 0:
            return

        # Delete textures for the lines that are actually removed
        for i in range(num_deleted_lines):
            self._cleanup_cached_texture(delete_idx + i)

        # Shift cache entries for lines that were below the deleted block
        keys_to_shift = sorted([k for k in self.line_texture_cache if k >= delete_idx + num_deleted_lines])

        for old_idx in keys_to_shift:
            new_idx = old_idx - num_deleted_lines
            self.line_texture_cache[new_idx] = self.line_texture_cache.pop(old_idx)
        
    def invalidate_all_cache(self):
        keys_to_remove = list(self.line_texture_cache.keys())
        for k in keys_to_remove:
            self._cleanup_cached_texture(k)

    def cleanup(self):
        self.invalidate_all_cache()
