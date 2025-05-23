from .text_renderer import TextRenderer
from OpenGL.GL import *
from editor.modes import EditorMode, EditorState
from syntax.highlighter import highlight_line, PYTHON_SYNTAX_RULES, TOKEN_TYPE_DEFAULT
from editor.buffer import Buffer
from editor.cursor import Cursor

class EditorRenderer:
    def __init__(self, font_path, font_size):
        self.text_renderer = TextRenderer(font_path, font_size)
        self.line_height = self.text_renderer.line_height
        self.visible_lines_in_viewport = 0
        self.padding_x = 5
        self.padding_y = 5
        # Key: line_index, Value: (texture_id, actual_text_width, texture_height, text_content_str)
        self.line_texture_cache = {}
        self.cursor_color = (240, 240, 240, 255)
        self.status_text_renderer_color = (180, 180, 180)
        self.line_num_renderer_color = (100, 100, 120)
        self.selection_bg_color_rgb = (50, 80, 120)
        self.cursor_width = 2
        status_font_size = max(12, int(font_size * 0.8))
        

        try:
            self.status_text_renderer = TextRenderer(font_path, status_font_size, self.status_text_renderer_color)
        except Exception: # Fallback
            self.status_text_renderer = self.text_renderer 


        # Line number renderer
        try:
            self.line_num_renderer = TextRenderer(font_path, font_size, self.line_num_renderer_color) 
        except Exception:
            self.line_num_renderer = self.text_renderer

        self.line_number_width = 0
        self.gutter_padding = 5            

    def get_selection_range(self, editor_state: EditorState, cursor_obj):
        """
        Determines the normalized selection range (start_line, start_col, end_line, end_col).
        The 'end' is typically exclusive for ranges but inclusive for single points or visual display.
        Returns None if not in visual mode or no anchor.
        """
        if editor_state.mode not in [EditorMode.VISUAL, EditorMode.VISUAL_LINE] or not editor_state.visual_mode_anchor:
            return None

        anchor_line, anchor_col = editor_state.visual_mode_anchor
        current_line, current_col = cursor_obj.line, cursor_obj.col

        # Normalize: start is always before or equal to end
        if (anchor_line, anchor_col) <= (current_line, current_col):
            sel_start_line, sel_start_col = anchor_line, anchor_col
            sel_end_line, sel_end_col = current_line, current_col
        else:
            sel_start_line, sel_start_col = current_line, current_col
            sel_end_line, sel_end_col = anchor_line, anchor_col
        
        return sel_start_line, sel_start_col, sel_end_line, sel_end_col

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



    def _calculate_line_number_width(self, buffer_obj: Buffer):
        """Calculates the width needed for the line number gutter."""
        max_line_num = buffer_obj.get_line_count()
        if max_line_num == 0:
            return self.text_renderer.get_string_width("1") + self.gutter_padding # Min width for at least "1"
        
        return self.line_num_renderer.get_string_width(str(max_line_num)) + self.gutter_padding

    def render_buffer(self, buffer_obj: Buffer, editor_state: EditorState, screen_height_param, cursor_obj: Cursor):
        if self.visible_lines_in_viewport == 0:
            self._calculate_visible_lines(screen_height_param)

        self.line_number_width = self._calculate_line_number_width(buffer_obj)  
        text_area_start_x = self.padding_x + self.line_number_width

        # Determine the range of lines to render based on viewport
        start_render_line = editor_state.viewport_start_line
        end_render_line = min(buffer_obj.get_line_count(), 
                              start_render_line + self.visible_lines_in_viewport)

        current_selection_details = self.get_selection_range(editor_state, cursor_obj)

        for i in range(start_render_line, end_render_line):
            display_line_index = i - start_render_line
            current_line_y_pos = self.padding_y + (display_line_index * self.line_height)

            if editor_state.mode in [EditorMode.VISUAL, EditorMode.VISUAL_LINE]:
                self._render_selection_for_line(i, current_line_y_pos, text_area_start_x,
                                                buffer_obj, current_selection_details, editor_state)

            line_num_str = str(i + 1) # Line numbers are 1-indexed for display
            ln_tex_id, ln_w, ln_h = self.line_num_renderer.render_text_to_texture(line_num_str, self.line_num_renderer_color)

            if ln_tex_id:
                ln_x_pos = self.padding_x + (self.line_number_width - self.gutter_padding - ln_w)
                self.line_num_renderer.draw_text(ln_tex_id, ln_x_pos, current_line_y_pos, ln_w, ln_h)
                self.line_num_renderer.cleanup_texture(ln_tex_id)

            line_text = buffer_obj.get_line(i)
            if line_text is None: line_text = ""

            cached_entry = self.line_texture_cache.get(i)
            texture_id, tex_w, tex_h = None, 0, self.line_height
            
            # Only re-render texture if text content changes.
            needs_texture_re_render = True
            if cached_entry and cached_entry[3] == line_text:
                 texture_id, tex_w, tex_h, _ = cached_entry
                 needs_texture_re_render = False

            if needs_texture_re_render:
                if cached_entry: self.text_renderer.cleanup_texture(cached_entry[0])
                
                if editor_state.current_syntax_rules:
                    # Syntax highlighting active: tokenize and render segmented
                    syntax_tokens = highlight_line(line_text, editor_state.current_syntax_rules)
                    texture_id, tex_w, tex_h_rendered = self.text_renderer.render_line_segmented_to_texture(
                        syntax_tokens
                    )
                else:
                    # No syntax highlighting: render plain
                    texture_id, tex_w, tex_h_rendered = self.text_renderer.render_text_to_texture(
                        line_text
                    )
                
                self.line_texture_cache[i] = (texture_id, tex_w, tex_h_rendered, line_text)
                tex_h = tex_h_rendered # tex_h will be self.line_height

            if texture_id is not None:
                 self.text_renderer.draw_text(texture_id, text_area_start_x, current_line_y_pos, tex_w, tex_h)
        
        # Pruning cache (as before)
        max_buffer_line = buffer_obj.get_line_count() - 1
        keys_to_prune = [k for k in self.line_texture_cache if k > max_buffer_line]
        for k_prune in keys_to_prune: self._cleanup_cached_texture(k_prune)

    def _render_selection_for_line(self, buffer_line_idx, line_y_pos, text_area_start_x,
                                   buffer_obj: Buffer, selection_details, editor_state: EditorState):
        if not selection_details:
            return

        sel_start_line, sel_start_col, sel_end_line, sel_end_col = selection_details

        if not (sel_start_line <= buffer_line_idx <= sel_end_line):
            return

        line_content = buffer_obj.get_line(buffer_line_idx)
        if line_content is None: return

        x1, x2 = 0, 0
        
        current_line_text_for_calc = line_content if line_content else " "

        is_fully_selected_line = False

        if editor_state.mode == EditorMode.VISUAL_LINE:
            is_fully_selected_line = True
        elif buffer_line_idx > sel_start_line and buffer_line_idx < sel_end_line:
            is_fully_selected_line = True

        if is_fully_selected_line:
            x1 = text_area_start_x
            line_render_width = self.text_renderer.get_string_width(current_line_text_for_calc)
            x2 = text_area_start_x + line_render_width
            if not line_content:
                 x2 = text_area_start_x + self.text_renderer.get_string_width(" ")
        else:
            if buffer_line_idx == sel_start_line:
                text_before_sel_start = current_line_text_for_calc[:sel_start_col]
                x1 = text_area_start_x + self.text_renderer.get_string_width(text_before_sel_start)
            else:
                x1 = text_area_start_x

            if buffer_line_idx == sel_end_line:
                if sel_end_col == -1 and not current_line_text_for_calc.strip():
                     x2 = text_area_start_x + self.text_renderer.get_string_width(" ")
                elif sel_end_col >= len(current_line_text_for_calc) - 1:
                     x2 = text_area_start_x + self.text_renderer.get_string_width(current_line_text_for_calc)
                else:
                     text_up_to_sel_end_inclusive = current_line_text_for_calc[:sel_end_col + 1]
                     x2 = text_area_start_x + self.text_renderer.get_string_width(text_up_to_sel_end_inclusive)
            else:
                 x2 = text_area_start_x + self.text_renderer.get_string_width(current_line_text_for_calc)


        if x1 < x2 : 
            glDisable(GL_TEXTURE_2D) 
            glColor3ub(*self.selection_bg_color_rgb)
            glRectf(x1, line_y_pos, x2, line_y_pos + self.line_height)
    

    def render_cursor(self, cursor_obj: Cursor, buffer_obj: Buffer, editor_state: EditorState, is_visible=True):
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

    def render_command_line(self, editor_state: EditorState, screen_width, screen_height):
        if editor_state.mode != EditorMode.COMMAND and not editor_state.command_buffer:
            # If not in command mode and no persistent message, render normal status bar
            return 

        cmd_renderer = self.status_text_renderer 
        
        text_to_render = editor_state.command_buffer
        
        texture_id, tex_w, tex_h = cmd_renderer.render_text_to_texture(text_to_render)

        if texture_id:
            x_pos = self.padding_x

            y_pos = screen_height - tex_h - self.padding_y 
            
            # glColor4f(0.1, 0.1, 0.1, 1.0)
            # glRectf(0, y_pos - self.padding_y, screen_width, screen_height)

            cmd_renderer.draw_text(texture_id, x_pos, y_pos, tex_w, tex_h)
            cmd_renderer.cleanup_texture(texture_id)

            if editor_state.mode == EditorMode.COMMAND:
                text_before_cmd_cursor = editor_state.command_buffer[:editor_state.command_cursor_pos]
                cursor_x_cmd = x_pos + cmd_renderer.get_string_width(text_before_cmd_cursor)
                
                cmd_cursor_height = cmd_renderer.line_height 

                glColor4ub(self.cursor_color[0], self.cursor_color[1], self.cursor_color[2], self.cursor_color[3])
                glDisable(GL_TEXTURE_2D)
                glBegin(GL_QUADS)
                glVertex2f(cursor_x_cmd, y_pos)
                glVertex2f(cursor_x_cmd + self.cursor_width, y_pos)
                glVertex2f(cursor_x_cmd + self.cursor_width, y_pos + cmd_cursor_height)
                glVertex2f(cursor_x_cmd, y_pos + cmd_cursor_height)
                glEnd()

    def render_status_bar(self, editor_state: EditorState, editor_buffer: Buffer, screen_width, screen_height):
        """Renders the status bar on the bottom left of the screen."""
        if editor_state.mode == EditorMode.COMMAND:
            self.render_command_line(editor_state, screen_width, screen_height)
            return # Early return, so command bar takes precedence

        if not hasattr(self, 'status_text_renderer'):
            return
        
        status_prefix = ""
        if editor_state.mode == EditorMode.OPERATOR_PENDING:
            status_prefix = f"({editor_state.active_operator.name[0].lower()}) "

        mode_name = f"-- {editor_state.mode.name} --"

        filepath_display = editor_buffer.filepath if editor_buffer.filepath else "[No Name]"
        dirty_indicator = " [+]" if editor_buffer.dirty else ""
        # cursor_pos_str = f"Ln {cursor_obj.line+1}, Col {cursor_obj.col+1}"

        status_text = f"{status_prefix}{mode_name}  {filepath_display}{dirty_indicator}"

        texture_id, tex_w, tex_h = \
            self.status_text_renderer.render_text_to_texture(status_text, self.status_text_renderer_color)

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
