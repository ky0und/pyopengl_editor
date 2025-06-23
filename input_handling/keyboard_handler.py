import pygame as pg
import os
from editor.modes import EditorMode, EditorState, Operator
from editor.buffer import Buffer
from editor.cursor import Cursor
from rendering.renderer import EditorRenderer
from syntax.highlighter import get_rules_for_extension

class KeyboardHandler:
    def __init__(self, editor_buffer: Buffer, 
                 editor_state: EditorState, 
                 cursor: Cursor, 
                 editor_renderer: EditorRenderer):
        self.buffer = editor_buffer
        self.state = editor_state
        self.cursor = cursor
        self.renderer = editor_renderer

    def _reset_buffer_state_for_new_load(self):
        """Resets cursor and tells renderer to clear all line caches."""
        self.cursor.line = 0
        self.cursor.col = 0
        self.state.viewport_start_line = 0
        self.renderer.invalidate_all_cache()

    def handle_keydown(self, event):
        """
        Processes a Pygame KEYDOWN event based on the current editor mode.
        Returns True if an action was taken that should reset cursor blink, False otherwise.
        """
        action_taken = False

        # --- Handle COMMAND mode input first if active ---
        if self.state.mode == EditorMode.COMMAND:
            action_taken = self._handle_command_mode(event)
            return action_taken

        # --- Handle OPERATOR_PENDING mode before general Esc or Normal/Insert ---        
        if self.state.mode == EditorMode.OPERATOR_PENDING:
            action_taken = self._handle_operator_pending_mode(event)
            return action_taken

        # --- Handle VISUAL mode inputs before general Esc ---
        if self.state.mode in [EditorMode.VISUAL, EditorMode.VISUAL_LINE]:
            action_taken = self._handle_visual_mode(event)
            return action_taken

        # --- Global Mode-Independent Keys ---
        if event.key == pg.K_ESCAPE:
            if self.state.mode == EditorMode.INSERT:
                self.state.switch_to_mode(EditorMode.NORMAL)
                current_line_text = self.buffer.get_line(self.cursor.line)
                if self.cursor.col > 0 and self.cursor.col <= len(current_line_text or ""):
                    self.cursor.col -= 1
                action_taken = True
            elif self.state.mode == EditorMode.OPERATOR_PENDING: # Esc cancels operator
                self.state.reset_operator_state()
                action_taken = True
            return action_taken

        # --- Mode-Specific Handling ---
        if self.state.mode == EditorMode.NORMAL:
            action_taken = self._handle_normal_mode(event)
        elif self.state.mode == EditorMode.INSERT:
            action_taken = self._handle_insert_mode(event)
        
        return action_taken

    def _get_normalized_selection_range(self):
        """Helper to get (start_line, start_col, end_line, end_col) from visual state."""
        if not self.state.visual_mode_anchor:
            return None
        
        al, ac = self.state.visual_mode_anchor
        cl, cc = self.cursor.line, self.cursor.col

        if (al, ac) <= (cl, cc):
            return al, ac, cl, cc
        else:
            return cl, cc, al, ac

    def _handle_visual_mode(self, event):
        action_taken = True # Most keys extend selection or perform action
        original_cursor_line = self.cursor.line
        original_cursor_col = self.cursor.col

        if event.key == pg.K_ESCAPE:
            self.state.switch_to_mode(EditorMode.NORMAL) # Exits visual, clears anchor
            return True

        # --- Operators in Visual Mode ---
        # Pressing d, c, y will apply to selection and exit visual mode
        op_to_apply = None
        if event.key == pg.K_d: op_to_apply = Operator.DELETE
        elif event.key == pg.K_c: op_to_apply = Operator.CHANGE
        elif event.key == pg.K_y: op_to_apply = Operator.YANK

        if op_to_apply:
            selection = self._get_normalized_selection_range()
            if not selection:
                self.state.switch_to_mode(EditorMode.NORMAL); return True # Should not happen
            
            start_l, start_c, end_l, end_c = selection
            is_linewise_selection = (self.state.mode == EditorMode.VISUAL_LINE)

            if is_linewise_selection:
                # For linewise, select whole lines from start_l to end_l
                text_to_operate_on = self._get_text_range(start_l, 0, end_l, 0, True)
            else: # Character-wise
                # Adjust end_c to be inclusive for _get_text_range if it expects that
                # Our current _get_text_range for charwise is inclusive on end_c
                text_to_operate_on = self._get_text_range(start_l, start_c, end_l, end_c, False)

            if text_to_operate_on is not None: # Check if text was actually selected
                self.state.set_register(text_to_operate_on, is_linewise_selection)

                if op_to_apply == Operator.DELETE or op_to_apply == Operator.CHANGE:
                    # --- Perform Deletion ---
                    if is_linewise_selection:
                        num_lines = end_l - start_l + 1
                        self.renderer.handle_lines_deleted(start_l, num_lines)
                        for _ in range(num_lines):
                            if start_l < self.buffer.get_line_count():
                                self.buffer.lines.pop(start_l)
                        if not self.buffer.lines: self.buffer.lines.append("")
                        self.buffer._mark_dirty()
                        self.cursor.line = min(start_l, self.buffer.get_line_count() - 1)
                        self.cursor.col = 0
                    else: # Character-wise deletion
                        if start_l == end_l: # Single line character-wise delete
                            line_content = self.buffer.get_line(start_l)
                            if line_content is not None:
                                self.renderer.invalidate_line_cache(start_l)
                                # end_c is inclusive index of selection
                                self.buffer.lines[start_l] = line_content[:start_c] + line_content[end_c + 1:]
                                self.buffer._mark_dirty()
                                self.cursor.line = start_l
                                self.cursor.col = start_c
                        else: # Multi-line character-wise delete
                            # 1. Get the part of the first line to keep (prefix)
                            first_line_content = self.buffer.get_line(start_l) or ""
                            prefix_first_line = first_line_content[:start_c]

                            # 2. Get the part of the last line to keep (suffix)
                            last_line_content = self.buffer.get_line(end_l) or ""
                            # end_c is inclusive, so suffix starts at end_c + 1
                            suffix_last_line = last_line_content[end_c + 1:]
                            
                            # 3. Combine prefix and suffix onto the first line
                            self.buffer.lines[start_l] = prefix_first_line + suffix_last_line
                            self.renderer.invalidate_line_cache(start_l) # First line changed

                            # 4. Determine lines to delete (middle lines + the original last line of selection)
                            # Lines from start_l + 1 up to and including end_l need to be removed
                            num_intermediate_lines_to_delete = end_l - (start_l + 1) + 1
                            
                            if num_intermediate_lines_to_delete > 0:
                                self.renderer.handle_lines_deleted(start_l + 1, num_intermediate_lines_to_delete)
                                for _ in range(num_intermediate_lines_to_delete):
                                    if start_l + 1 < self.buffer.get_line_count(): # Check bounds
                                        self.buffer.lines.pop(start_l + 1) # Keep popping at start_l + 1
                            
                            if not self.buffer.lines: self.buffer.lines.append("") # Ensure not empty
                            self.buffer._mark_dirty()
                            
                            # Set cursor position
                            self.cursor.line = start_l
                            self.cursor.col = start_c
                    
                    # After deletion, if operator was CHANGE, switch to INSERT mode
                    if op_to_apply == Operator.CHANGE:
                        # Ensure cursor column is valid before insert (might be EOL after deletion)
                        current_line_text = self.buffer.get_line(self.cursor.line) or ""
                        self.cursor.col = min(self.cursor.col, len(current_line_text))
                        self.state.switch_to_mode(EditorMode.INSERT)
                    else: # DELETE
                        self.state.switch_to_mode(EditorMode.NORMAL)
                else: # YANK (no buffer modification, just copy to register)
                    self.state.switch_to_mode(EditorMode.NORMAL) 
            else: # text_to_operate_on was None (should not happen if selection is valid)
                self.state.switch_to_mode(EditorMode.NORMAL)
            return True # Action was taken

        # --- Handle PAGEUP/PAGEDOWN ---
        page_size = self.renderer.visible_lines_in_viewport -1
        if page_size <=0: page_size = 1 
        
        # --- Movement in Visual Mode (Extends Selection) ---
        if event.key == pg.K_h: self.cursor.move_left(self.buffer, mode_is_normal=True)
        elif event.key == pg.K_l: self.cursor.move_right(self.buffer, mode_is_normal=True)
        elif event.key == pg.K_k: self.cursor.move_up(self.buffer)
        elif event.key == pg.K_j: self.cursor.move_down(self.buffer)
        elif event.key == pg.K_PAGEUP:
            action_taken = self._scroll_viewport(-page_size)
            return action_taken
        elif event.key == pg.K_PAGEDOWN:
            action_taken = self._scroll_viewport(page_size)
            return action_taken
        elif event.key == pg.K_w:
            self.cursor.move_word_forward(self.buffer)
            action_taken = True
        elif event.key == pg.K_b:
            self.cursor.move_word_backward(self.buffer)
            action_taken = True
        elif event.key == pg.K_e:
            self.cursor.move_to_word_end(self.buffer)
            action_taken = True

        # Add more motions: w, b, e, $, 0, G, gg etc.
        # These motions will update self.cursor, and the selection highlight will adjust automatically.
        
        # If cursor moved, it's an action
        if (self.cursor.line, self.cursor.col) != (original_cursor_line, original_cursor_col):
            action_taken = True
        else: # No movement, no operator, perhaps an unhandled key
            action_taken = False
            
        return action_taken

    # Following https://vim.rtorr.com/
    def _handle_normal_mode(self, event):
        action_taken = False
        mods = pg.key.get_mods()
        current_cursor_tuple = (self.cursor.line, self.cursor.col)

        # --- Entering Visual Modes ---
        if event.key == pg.K_v: 
            if mods & pg.KMOD_SHIFT: # 'V' - linewise visual
                self.state.switch_to_mode(EditorMode.VISUAL_LINE, anchor_pos=current_cursor_tuple)
            else: # 'v'  - character-wise visual
                self.state.switch_to_mode(EditorMode.VISUAL, anchor_pos=current_cursor_tuple)
            action_taken = True
            return action_taken

        if mods & pg.KMOD_CTRL:
            page_size_ctrl = self.renderer.visible_lines_in_viewport - 2 
            if page_size_ctrl <= 0 : page_size_ctrl = 1

            if event.key == pg.K_b:
                action_taken = self._scroll_viewport(-page_size_ctrl)
                return action_taken 
            elif event.key == pg.K_f:
                action_taken = self._scroll_viewport(page_size_ctrl)
                return action_taken 

        if event.key == pg.K_SEMICOLON and (mods & pg.KMOD_SHIFT): # ':' key
            self.state.switch_to_mode(EditorMode.COMMAND)
            action_taken = True
            return action_taken # Exclusive for entering command mode

        # --- Operator Keys ---
        current_cursor_tuple = (self.cursor.line, self.cursor.col)
        if event.key == pg.K_d:   # 'd' - Delete
            self.state.start_operator(Operator.DELETE, current_cursor_tuple)
            self.state.pending_operator_keystrokes = "d" # For 'dd'
            action_taken = True 
        elif event.key == pg.K_c: # 'c' - Change
            self.state.start_operator(Operator.CHANGE, current_cursor_tuple)
            self.state.pending_operator_keystrokes = "c" # For 'cc'
            action_taken = True
        elif event.key == pg.K_y: # 'y' - Yank
            self.state.start_operator(Operator.YANK, current_cursor_tuple)
            self.state.pending_operator_keystrokes = "y" # For 'yy'
            action_taken = True

        if self.state.mode == EditorMode.OPERATOR_PENDING:
             return action_taken # Early return so next event gets processed by _handle_operator_pending_mode()

        # --- Put Commands ---
        if event.key == pg.K_p: # 'p' - (put after/below cursor) or 'P' (put before/above)
            is_uppercase_P = bool(mods & pg.KMOD_SHIFT)
            
            yanked_text, is_linewise = self.state.get_register_content()
            if not yanked_text: # Nothing in register
                action_taken = False
                return action_taken

            action_taken = True
            if is_linewise:
                # Split the yanked text into lines
                lines_to_put = yanked_text.splitlines()
                if not lines_to_put and yanked_text == "":
                    lines_to_put = [""]

                put_line_idx = self.cursor.line
                if not is_uppercase_P: # 'p' - put below current line
                    put_line_idx += 1
                
                self.renderer.handle_lines_inserted(insert_idx=put_line_idx, num_inserted_lines=len(lines_to_put))
                for i, line_to_insert in enumerate(lines_to_put):
                    self.buffer.lines.insert(put_line_idx + i, line_to_insert)
                
                self.buffer._mark_dirty()
                self.cursor.line = put_line_idx
                self.cursor.col = 0
            else: # Character-wise put
                put_target_line_idx = self.cursor.line
                put_target_col_idx = self.cursor.col

                if not is_uppercase_P: # 'p' - put after cursor char
                    current_line_len = len(self.buffer.get_line(put_target_line_idx) or "")
                    if current_line_len > 0 and put_target_col_idx < current_line_len :
                        put_target_col_idx += 1

                if '\n' in yanked_text:
                    parts = yanked_text.split('\n')
                    first_part = parts[0]
                    remaining_parts = parts[1:]

                    original_line_content = self.buffer.get_line(put_target_line_idx) or ""
                    
                    prefix = original_line_content[:put_target_col_idx]
                    suffix = original_line_content[put_target_col_idx:]

                    self.buffer.lines[put_target_line_idx] = prefix + first_part
                    self.renderer.invalidate_line_cache(put_target_line_idx)
                    
                    lines_to_insert_for_renderer = []
                    current_insert_line_idx = put_target_line_idx + 1

                    for i, part in enumerate(remaining_parts):
                        if i == len(remaining_parts) - 1: # Last part of the yanked text
                            lines_to_insert_for_renderer.append(part + suffix)
                        else:
                            lines_to_insert_for_renderer.append(part)
                    
                    if lines_to_insert_for_renderer:
                        self.renderer.handle_lines_inserted(current_insert_line_idx, len(lines_to_insert_for_renderer))
                        for i, line_content in enumerate(lines_to_insert_for_renderer):
                            self.buffer.lines.insert(current_insert_line_idx + i, line_content)

                    if is_uppercase_P:
                        self.cursor.line = put_target_line_idx
                        self.cursor.col = put_target_col_idx
                    else: # 'p'
                        self.cursor.line = put_target_line_idx + len(remaining_parts)
                        last_pasted_segment_len = len(remaining_parts[-1]) if remaining_parts else len(first_part)
                        self.cursor.col = (len(prefix) if self.cursor.line == put_target_line_idx else 0) + last_pasted_segment_len -1
                        if self.cursor.line > put_target_line_idx :
                            self.cursor.col = len(remaining_parts[-1]) -1
                        else: 
                            self.cursor.col = put_target_col_idx + len(first_part) -1

                else: # Single-line character-wise put (no newlines in yanked_text)
                    current_line = self.buffer.get_line(put_target_line_idx)
                    if current_line is not None: # Should always be true if line index is valid
                        self.renderer.invalidate_line_cache(put_target_line_idx)
                        new_line_content = current_line[:put_target_col_idx] + yanked_text + current_line[put_target_col_idx:]
                        self.buffer.lines[put_target_line_idx] = new_line_content
                        
                        # Set cursor position
                        if is_uppercase_P: # 'P'
                            self.cursor.col = put_target_col_idx
                        else: # 'p'
                            self.cursor.col = put_target_col_idx + len(yanked_text) -1 # End of inserted text
                            if len(yanked_text) == 0 : self.cursor.col = put_target_col_idx # if empty string, stay

            # Ensure cursor is valid after put
            self.cursor.set_pos(self.cursor.line, self.cursor.col, self.buffer) # Use existing set_pos for clamping
            return action_taken

        # --- Regular Normal Mode Commands (if not a Ctrl command) ---
        if event.key == pg.K_i: # Insert mode (before cursor)
            self.state.switch_to_mode(EditorMode.INSERT)
            action_taken = True
        elif event.key == pg.K_a: # Insert mode (append after cursor)
            current_line_text = self.buffer.get_line(self.cursor.line)
            if self.cursor.col < len(current_line_text or ""): # Don't go past EOL
                self.cursor.col += 1
            self.state.switch_to_mode(EditorMode.INSERT)
            action_taken = True
        elif event.key == pg.K_o:
            if pg.key.get_mods() & pg.KMOD_SHIFT: # 'O' - Open line above
                self.renderer.handle_lines_inserted(insert_idx=self.cursor.line, num_inserted_lines=1)
                self.buffer.lines.insert(self.cursor.line, "")
                self.cursor.col = 0
                self.state.switch_to_mode(EditorMode.INSERT)
                action_taken = True
            else: # 'o' - Open line below
                self.renderer.handle_lines_inserted(insert_idx=self.cursor.line + 1, num_inserted_lines=1)
                self.buffer.lines.insert(self.cursor.line + 1, "")
                self.cursor.line += 1
                self.cursor.col = 0
                self.state.switch_to_mode(EditorMode.INSERT)
                action_taken = True
        elif event.key == pg.K_x:
            current_line_text = self.buffer.get_line(self.cursor.line)
            if current_line_text is not None and self.cursor.col < len(current_line_text):
                self.renderer.invalidate_line_cache(self.cursor.line)
                self.buffer.delete_char_at_cursor(self.cursor.line, self.cursor.col)
                if self.cursor.col >= len(self.buffer.get_line(self.cursor.line) or "") and self.cursor.col > 0:
                    self.cursor.col -= 1
                action_taken = True
        elif event.key == pg.K_h: # 'h' - move cursor left
            self.cursor.move_left(self.buffer, mode_is_normal=True)
            action_taken = True
        elif event.key == pg.K_j: # 'j' - move cursor down
            self.cursor.move_down(self.buffer)
            action_taken = True
        elif event.key == pg.K_k: # 'k' - move cursor up
            if self.cursor.line == self.state.viewport_start_line and self.cursor.line > 0:
                self.state.viewport_start_line -= 1
            self.cursor.move_up(self.buffer)
            action_taken = True
        elif event.key == pg.K_l: # 'l' - move cursor right
            self.cursor.move_right(self.buffer, mode_is_normal=True)
            action_taken = True
        elif event.key == pg.K_0 or (event.key == pg.K_RIGHTPAREN and mods & pg.KMOD_SHIFT): # '0' (often Shift+0 for ')' key)
            self.cursor.move_to_line_start(self.buffer)
            action_taken = True
        elif event.key == pg.K_6 and mods & pg.KMOD_SHIFT: # '^' (Shift+6)
            self.cursor.move_to_first_non_whitespace(self.buffer)
            action_taken = True
        elif event.key == pg.K_4 and mods & pg.KMOD_SHIFT: # '$' (Shift+4)
            self.cursor.move_to_line_end(self.buffer, mode_is_normal=True)
            action_taken = True
        elif event.key == pg.K_w:
            self.cursor.move_word_forward(self.buffer)
            action_taken = True
        elif event.key == pg.K_b:
            self.cursor.move_word_backward(self.buffer)
            action_taken = True
        elif event.key == pg.K_e:
            self.cursor.move_to_word_end(self.buffer)
            action_taken = True

        return action_taken

    # Following https://vim.rtorr.com/
    def _handle_insert_mode(self, event):
        action_taken = False
        # --- Handle PAGEUP/PAGEDOWN ---
        page_size = self.renderer.visible_lines_in_viewport -1
        if page_size <=0: page_size = 1

        if event.key == pg.K_RETURN:
            self.renderer.invalidate_line_cache(self.cursor.line)
            self.renderer.handle_lines_inserted(insert_idx=self.cursor.line + 1, num_inserted_lines=1)
            self.buffer.split_line(self.cursor.line, self.cursor.col)
            self.cursor.line += 1
            self.cursor.col = 0
            action_taken = True
        elif event.key == pg.K_PAGEUP:
            action_taken = self._scroll_viewport(-page_size)
            return action_taken
        elif event.key == pg.K_PAGEDOWN:
            action_taken = self._scroll_viewport(page_size)
            return action_taken
        elif event.key == pg.K_DELETE:
            # Invalidate cache for current line and potentially next if merging
            self.renderer.invalidate_line_cache(self.cursor.line)
            if self.cursor.line + 1 < self.buffer.get_line_count():
                self.renderer.invalidate_line_cache(self.cursor.line + 1) # If merge happens

            if self.buffer.delete_char_at_cursor(self.cursor.line, self.cursor.col):
                current_line_len = len(self.buffer.get_line(self.cursor.line) or "")
                if self.cursor.col > current_line_len : # If cursor was past EOL of merged line
                    self.cursor.col = current_line_len
                
                action_taken = True
        elif event.key == pg.K_BACKSPACE:
            prev_cursor_line = self.cursor.line
            
            is_merge = (self.cursor.col == 0 and self.cursor.line > 0)

            if self.buffer.delete_char(self.cursor.line, self.cursor.col):
                if is_merge:
                    self.renderer.invalidate_line_cache(prev_cursor_line - 1)
                    self.renderer.handle_lines_deleted(delete_idx=prev_cursor_line, num_deleted_lines=1)
                    self.cursor.line -=1
                    self.cursor.col = len(self.buffer.get_line(self.cursor.line) or "")
                else:
                    self.renderer.invalidate_line_cache(self.cursor.line)
                    self.cursor.col -=1
                action_taken = True
            action_taken = True
        elif event.key == pg.K_LEFT:
            self.cursor.move_left(self.buffer, mode_is_normal=False)
            action_taken = True
        elif event.key == pg.K_RIGHT:
            self.cursor.move_right(self.buffer, mode_is_normal=False)
            action_taken = True
        elif event.key == pg.K_UP:
            if self.cursor.line == self.state.viewport_start_line and self.cursor.line > 0:
                self.state.viewport_start_line -= 1
            self.cursor.move_up(self.buffer)
            action_taken = True
        elif event.key == pg.K_DOWN:
            if self.cursor.line == self.state.viewport_start_line + \
                self.renderer.visible_lines_in_viewport - 1 and \
                self.cursor.line < self.buffer.get_line_count() - 1:
                self.state.viewport_start_line += 1
            self.cursor.move_down(self.buffer)
            action_taken = True
        elif event.unicode:
            if event.unicode.isprintable() or event.unicode == '\t':
                self.renderer.invalidate_line_cache(self.cursor.line)
                if event.unicode == '\t':
                     for _ in range(4): # Simple tab to 4 spaces
                         self.buffer.insert_char(self.cursor.line, self.cursor.col, ' ')
                         self.cursor.col += 1
                else:
                    self.buffer.insert_char(self.cursor.line, self.cursor.col, event.unicode)
                    self.cursor.col += 1
                action_taken = True
        return action_taken
    
    def _scroll_viewport(self, num_lines_to_scroll):
        """Helper to scroll viewport and adjust cursor if it goes out of view.
           Positive num_lines_to_scroll moves view down (text up).
           Negative num_lines_to_scroll moves view up (text down).
        """
        new_viewport_start = self.state.viewport_start_line + num_lines_to_scroll
        
        # Clamp viewport start
        max_start_line = max(0, self.buffer.get_line_count() - self.renderer.visible_lines_in_viewport)
        self.state.viewport_start_line = max(0, min(new_viewport_start, max_start_line))

        if num_lines_to_scroll < 0:
            self.cursor.line = self.state.viewport_start_line
        elif num_lines_to_scroll > 0:
            self.cursor.line = min(self.buffer.get_line_count() - 1,
                                   self.state.viewport_start_line + self.renderer.visible_lines_in_viewport - 1)
        
        self.cursor._clamp_col(self.buffer)
        return True


    def _handle_command_mode(self, event):
        action_taken = True

        if event.key == pg.K_ESCAPE: # 'ESC' - Return to previous mode
            self.state.switch_to_mode(self.state.previous_mode)
        elif event.key == pg.K_RETURN:
            self._execute_command(self.state.command_buffer)
            # Execute might switch mode (e.g. :q) or stay (e.g. bad command)
            # If not quitting, return to previous mode.
            if self.state.mode == EditorMode.COMMAND:
                 self.state.switch_to_mode(self.state.previous_mode)
        elif event.key == pg.K_BACKSPACE:
            if self.state.command_cursor_pos > 0: # If cursor is after ':', and buffer is just ':', clear and exit. (e.g. 'how do i exit vim' shouldn't be a problem here)
                if self.state.command_cursor_pos == 1 and self.state.command_buffer == ":":
                    self.state.switch_to_mode(self.state.previous_mode)
                    return True

                self.state.command_buffer = \
                    self.state.command_buffer[:self.state.command_cursor_pos - 1] + \
                    self.state.command_buffer[self.state.command_cursor_pos:]
                self.state.command_cursor_pos -= 1
        elif event.key == pg.K_LEFT:
            if self.state.command_cursor_pos > 1: # Don't move cursor before ':'
                self.state.command_cursor_pos -= 1
        elif event.key == pg.K_RIGHT:
            if self.state.command_cursor_pos < len(self.state.command_buffer):
                self.state.command_cursor_pos += 1
        elif event.unicode:
            # Ensure cursor isn't trying to type before initial ':' if somehow moved there
            if self.state.command_cursor_pos == 0 and self.state.command_buffer == "":
                self.state.command_buffer = ":"
                self.state.command_cursor_pos = 1

            if event.unicode.isprintable():
                self.state.command_buffer = \
                    self.state.command_buffer[:self.state.command_cursor_pos] + \
                    event.unicode + \
                    self.state.command_buffer[self.state.command_cursor_pos:]
                self.state.command_cursor_pos += 1
        else:
            action_taken = False # Not a recognized key for command input
            
        return action_taken

    def _execute_command(self, command_str):
        print(f"Executing command: {command_str}")
        if not command_str.startswith(":"):
            self.state.command_buffer = f"Error: Not a valid command: {command_str}"
            self.state.switch_to_mode(EditorMode.COMMAND, preserve_command_state=True)
            return

        parts = command_str[1:].strip().split()
        if not parts:
            # Empty command (e.g., just ":") - do nothing, return to normal
            self.state.switch_to_mode(self.state.previous_mode)
            return

        cmd = parts[0]
        args = parts[1:]

        if cmd == 'q':
            if self.buffer.dirty:
                # In real Vim, this errors out
                # TODO, make this error out
                self.state.command_buffer = "Error: Unsaved changes! (use :q! to override)"
                self.state.switch_to_mode(EditorMode.COMMAND, preserve_command_state=True)
            else:
                pg.event.post(pg.event.Event(pg.QUIT))
        elif cmd == 'q!':
            pg.event.post(pg.event.Event(pg.QUIT))
        elif cmd == 'w':
            filepath = args[0] if args else self.buffer.filepath
            if filepath:
                self.buffer.save_to_file(filepath)
                self._update_syntax_highlighting_for_buffer()
                self.state.switch_to_mode(self.state.previous_mode)
            elif self.buffer.filepath: # No arg, but has a current path
                self.buffer.save_to_file()
                self._update_syntax_highlighting_for_buffer()
                self.state.switch_to_mode(self.state.previous_mode)
            else:
                self.state.command_buffer = "Error: No filename given for :w"
                self.state.switch_to_mode(EditorMode.COMMAND, preserve_command_state=True)
        elif cmd == 'wq':
            # Save then quit
            saved_successfully = False
            if self.buffer.filepath:
                saved_successfully = self.buffer.save_to_file()
            elif args: # :wq filename
                saved_successfully = self.buffer.save_to_file(args[0])
            else: # :wq with no current name and no arg
                 self.state.command_buffer = "Error: No filename for :wq"
                 self.state.switch_to_mode(EditorMode.COMMAND, preserve_command_state=True)
                 return
            
            if saved_successfully or not self.buffer.dirty: # Quit if saved or wasn't dirty
                pg.event.post(pg.event.Event(pg.QUIT))
            else: # Save failed, show error
                self.state.command_buffer = "Error: Save failed during :wq"
                self.state.switch_to_mode(EditorMode.COMMAND, preserve_command_state=True)

        elif cmd == 'e':
            if args:
                filepath_to_open = args[0]
                self._reset_buffer_state_for_new_load()
                self.buffer.load_from_file(filepath_to_open)
                self._update_syntax_highlighting_for_buffer()
                self.state.switch_to_mode(self.state.previous_mode) # Return to normal after loading
            else:
                self.state.command_buffer = "Error: No filename given for :e"
                self.state.switch_to_mode(EditorMode.COMMAND, preserve_command_state=True)
        else:
            self.state.command_buffer = f"Error: Unknown command: {cmd}"
            self.state.switch_to_mode(EditorMode.COMMAND, preserve_command_state=True)

    def _handle_operator_pending_mode(self, event):
        action_taken = True
        operator = self.state.active_operator
        start_op_line, start_op_col = self.state.operator_pending_start_cursor_pos
        motion_end_line, motion_end_col = self.cursor.line, self.cursor.col

        second_op_char = ""
        if event.key == pg.K_d and operator == Operator.DELETE: second_op_char = "d"
        elif event.key == pg.K_c and operator == Operator.CHANGE: second_op_char = "c"
        elif event.key == pg.K_y and operator == Operator.YANK: second_op_char = "y"

        if second_op_char and self.state.pending_operator_keystrokes == second_op_char:
            print(f"Executing {operator.name} on line {start_op_line}")
            if operator == Operator.DELETE: # 'dd' - delete current line
                line_content = self.buffer.get_line(start_op_line)
                if line_content is not None: # Yank before deleting
                    self.state.set_register(line_content, type_is_linewise=True)

                if self.buffer.get_line_count() > 0:
                    self.renderer.handle_lines_deleted(delete_idx=start_op_line, num_deleted_lines=1)
                    self.buffer.lines.pop(start_op_line)
                    if not self.buffer.lines: self.buffer.lines.append("")
                    self.buffer._mark_dirty()
                    self.cursor.line = min(start_op_line, self.buffer.get_line_count() - 1)
                    self.cursor.col = 0
            elif operator == Operator.CHANGE: # 'cc' - delete line, then enter insert mode
                line_content = self.buffer.get_line(start_op_line)
                if line_content is not None: # Yank before changing
                    self.state.set_register(line_content, type_is_linewise=True)

                if self.buffer.get_line_count() > 0:
                    self.renderer.handle_lines_deleted(delete_idx=start_op_line, num_deleted_lines=1)
                    self.buffer.lines.pop(start_op_line)
                    self.renderer.handle_lines_inserted(insert_idx=start_op_line, num_inserted_lines=1)
                    self.buffer.lines.insert(start_op_line, "")
                    self.buffer._mark_dirty()
                    self.cursor.line = start_op_line
                    self.cursor.col = 0
                    self.state.switch_to_mode(EditorMode.INSERT)
                    return action_taken
            elif operator == Operator.YANK: # 'yy' - copy line
                line_content = self.buffer.get_line(start_op_line)
                if line_content is not None:
                    self.state.set_register(line_content, type_is_linewise=True)
                print(f"Yanked line: {line_content}")
            
            self.state.reset_operator_state()
            return action_taken
        
        # For later if i decide to support multi-line yanking, putting, difficult for now
        range_start_line, range_start_col = start_op_line, start_op_col
        text_to_operate_on = ""
        is_linewise_motion = False

        end_pos_inclusive = None
        target_range_lines = None

        if event.key == pg.K_j: # 'yj' - yank current line and line below - linewise
            if start_op_line < self.buffer.get_line_count() - 1:
                text_to_operate_on = self._get_text_range(start_op_line, 0, start_op_line + 1, 0, True)
                is_linewise_motion = True
                motion_end_line = start_op_line + 1 
                motion_end_col = 0
            else: # yj on last line, just yanks current line
                text_to_operate_on = self._get_text_range(start_op_line, 0, start_op_line, 0, True)
                is_linewise_motion = True
        elif event.key == pg.K_k: # 'yk' - yank current line and line above - linewise
            if start_op_line > 0:
                text_to_operate_on = self._get_text_range(start_op_line - 1, 0, start_op_line, 0, True)
                is_linewise_motion = True
                motion_end_line = start_op_line -1 
                motion_end_col = 0
            else: # yk on first line
                text_to_operate_on = self._get_text_range(start_op_line, 0, start_op_line, 0, True)
                is_linewise_motion = True
        elif event.key == pg.K_l or event.key == pg.K_SPACE : # 'yl' - yank char under cursor
            text_to_operate_on = self._get_text_range(start_op_line, start_op_col, start_op_line, start_op_col, False)
            motion_end_col = start_op_col
        elif event.key == pg.K_h: # 'yh' - yank char before original cursor, if not BOL
             if start_op_col > 0:
                 text_to_operate_on = self._get_text_range(start_op_line, start_op_col -1, start_op_line, start_op_col -1, False)
                 motion_end_col = start_op_col -1
             else:
                 self.state.reset_operator_state(); return True

        # TODO: Add more motions: w, b, e, $, 0, G, gg, etc.
        # TODO: Add text objects: iw, aw, i", a", etc.

        if text_to_operate_on:
            if operator == Operator.YANK:
                self.state.set_register(text_to_operate_on, is_linewise_motion)
                self.cursor.line = motion_end_line
                self.cursor.col = motion_end_col
            elif operator == Operator.DELETE:
                self.state.set_register(text_to_operate_on, is_linewise_motion) # Delete also yanks
                if is_linewise_motion:
                    start_del_line = min(start_op_line, motion_end_line)
                    end_del_line = max(start_op_line, motion_end_line)
                    num_lines = end_del_line - start_del_line + 1
                    self.renderer.handle_lines_deleted(start_del_line, num_lines)
                    for _ in range(num_lines):
                        if start_del_line < self.buffer.get_line_count():
                             self.buffer.lines.pop(start_del_line)
                    if not self.buffer.lines: self.buffer.lines.append("")
                    self.buffer._mark_dirty()
                    self.cursor.line = min(start_del_line, self.buffer.get_line_count() - 1)
                    self.cursor.col = 0
                else: # Charwise delete (simplified), assuming single char for 'dl', 'dh' for now
                    del_line = start_op_line
                    del_col = motion_end_col
                    self.renderer.invalidate_line_cache(del_line)
                    self.buffer.delete_char_at_cursor(del_line, del_col)
                    self.cursor.line = del_line
                    self.cursor.col = del_col
                    if self.cursor.col >= len(self.buffer.get_line(del_line) or "") and self.cursor.col > 0:
                        self.cursor.col -=1
            elif operator == Operator.CHANGE:
                self.state.set_register(text_to_operate_on, is_linewise_motion) # Change also yanks
                print(f"CHANGE op on: '{text_to_operate_on}' - then insert mode")
                self.cursor.line = start_op_line
                self.cursor.col = start_op_col
                # Perform deletion part first (like DELETE above) then...
                # self.state.switch_to_mode(EditorMode.INSERT)
                # This needs careful implementation of deleting the range.
                
            self.state.reset_operator_state()
            return action_taken
        else:
            if event.key == pg.K_ESCAPE:
                self.state.reset_operator_state()
            action_taken = False

        return action_taken
    
    def _get_text_range(self, start_line, start_col, end_line, end_col, is_linewise):
        """
        Helper to extract text from the buffer given a range.
        Handles inclusive end for charwise, exclusive for linewise (sort of).
        Returns a list of strings (lines) or a single string for charwise.
        """
        yanked_lines = []
        if is_linewise:
            # For linewise, end_line is inclusive
            for i in range(start_line, end_line + 1):
                line_content = self.buffer.get_line(i)
                if line_content is not None:
                    yanked_lines.append(line_content)
            return "\n".join(yanked_lines) # Return as a single string with newlines
        else:
            if start_line != end_line:
                first_line_content = self.buffer.get_line(start_line)
                if first_line_content is not None:
                    s_col = min(start_col, len(first_line_content))
                    yanked_lines.append(first_line_content[s_col:])
                else: # Should not happen if start_line is valid
                    yanked_lines.append("") 
                
                # Middle lines (if any): full lines
                for i in range(start_line + 1, end_line):
                    middle_line_content = self.buffer.get_line(i)
                    if middle_line_content is not None:
                        yanked_lines.append(middle_line_content)
                    else: # Should not happen
                        yanked_lines.append("")
                
                # Last line: from its beginning up to end_col (inclusive)
                last_line_content = self.buffer.get_line(end_line)
                if last_line_content is not None:
                    # end_col is the index of the last character to include
                    e_col_slice_end = min(end_col + 1, len(last_line_content))
                    yanked_lines.append(last_line_content[:e_col_slice_end])
                else: # Should not happen
                    pass # Don't append if last line is somehow None

                # Join with newlines because we crossed line boundaries
                return "\n".join(yanked_lines)
            else: # Single line character-wise
                line_content = self.buffer.get_line(start_line)
                if line_content is not None:
                    s_col, e_col = min(start_col, end_col), max(start_col, end_col)
                    return line_content[s_col : e_col + 1]
                return ""
            
    def _update_syntax_highlighting_for_buffer(self):
        """Updates EditorState's syntax rules based on the current buffer's filepath."""
        if self.buffer.filepath:
            _, ext = os.path.splitext(self.buffer.filepath)
            file_ext_cleaned = ext[1:] if ext.startswith('.') else ext # Remove dot, e.g. ".py" -> "py"
            rules, lang_name = get_rules_for_extension(file_ext_cleaned)
            self.state.set_syntax_highlighting(rules, lang_name)
            if rules: # If rules were found, all lines potentially need re-rendering with new highlighting
                self.renderer.invalidate_all_cache()
        else: # No filepath, disable highlighting
            self.state.set_syntax_highlighting(None, None)
            self.renderer.invalidate_all_cache() # Invalidate to remove old highlighting
