import pygame as pg
from editor.modes import EditorMode, EditorState, Operator
from editor.buffer import Buffer
from editor.cursor import Cursor
from rendering.renderer import EditorRenderer

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

    # Following https://vim.rtorr.com/
    def _handle_normal_mode(self, event):
        action_taken = False
        mods = pg.key.get_mods()

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
        # TODO Add other normal mode commands here (x, dd, yy, p etc.)

        return action_taken

    # Following https://vim.rtorr.com/
    def _handle_insert_mode(self, event):
        action_taken = False
        if event.key == pg.K_RETURN:
            self.renderer.invalidate_line_cache(self.cursor.line)
            self.renderer.handle_lines_inserted(insert_idx=self.cursor.line + 1, num_inserted_lines=1)
            self.buffer.split_line(self.cursor.line, self.cursor.col)
            self.cursor.line += 1
            self.cursor.col = 0
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
                self.state.switch_to_mode(self.state.previous_mode)
            elif self.buffer.filepath: # No arg, but has a current path
                self.buffer.save_to_file()
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
        start_pos = self.state.operator_pending_start_cursor_pos
        
        second_op_char = ""
        if event.key == pg.K_d and operator == Operator.DELETE: second_op_char = "d"
        elif event.key == pg.K_c and operator == Operator.CHANGE: second_op_char = "c"
        elif event.key == pg.K_y and operator == Operator.YANK: second_op_char = "y"

        if second_op_char and self.state.pending_operator_keystrokes == second_op_char:
            print(f"Executing {operator.name} on line {start_pos[0]}")
            if operator == Operator.DELETE: # 'dd' - delete current line
                if self.buffer.get_line_count() > 0:
                    self.renderer.handle_lines_deleted(delete_idx=start_pos[0], num_deleted_lines=1)
                    # TODO: Store deleted line for 'p' command (yank)
                    self.buffer.lines.pop(start_pos[0])
                    if not self.buffer.lines: self.buffer.lines.append("")
                    self.buffer._mark_dirty()
                    self.cursor.line = min(start_pos[0], self.buffer.get_line_count() - 1)
                    self.cursor.col = 0
            elif operator == Operator.CHANGE: # 'cc' - delete line, then enter insert mode
                if self.buffer.get_line_count() > 0:
                    self.renderer.handle_lines_deleted(delete_idx=start_pos[0], num_deleted_lines=1)
                    self.buffer.lines.pop(start_pos[0])
                    self.renderer.handle_lines_inserted(insert_idx=start_pos[0], num_inserted_lines=1)
                    self.buffer.lines.insert(start_pos[0], "")
                    self.buffer._mark_dirty()
                    self.cursor.line = start_pos[0]
                    self.cursor.col = 0
                    self.state.switch_to_mode(EditorMode.INSERT)
                    return action_taken
            elif operator == Operator.YANK: # 'yy' - copy line
                # TODO: Implement yanking (copying) the line
                line_content = self.buffer.get_line(start_pos[0])
                print(f"Yanked line: {line_content}")
            
            self.state.reset_operator_state()
            return action_taken
        
        end_pos_inclusive = None
        target_range_lines = None

        if event.key == pg.K_j: # 'dj' - delete current and next line
            if start_pos[0] < self.buffer.get_line_count() - 1:
                target_range_lines = (start_pos[0], start_pos[0] + 1)
            else: # dj on last line, just current line
                target_range_lines = (start_pos[0], start_pos[0])
        elif event.key == pg.K_k: # 'dk' - delete current and previous line
            if start_pos[0] > 0:
                target_range_lines = (start_pos[0] - 1, start_pos[0])
            else: # dk on first line, just current line
                target_range_lines = (start_pos[0], start_pos[0])
        elif event.key == pg.K_l or event.key == pg.K_SPACE: # 'dl' - delete char under cursor
            current_line_text = self.buffer.get_line(start_pos[0])
            if current_line_text is not None and start_pos[1] < len(current_line_text):
                end_pos_inclusive = (start_pos[0], start_pos[1])
            else: # At EOL or empty line, operator cancels
                self.state.reset_operator_state(); return True
        elif event.key == pg.K_h: # 'dh' - delete char before cursor
            if start_pos[1] > 0:
                end_pos_inclusive = (start_pos[0], start_pos[1] -1)
            else: # At BOL, operator cancels
                self.state.reset_operator_state(); return True

        # TODO: Add more motions: w, b, e, $, 0, G, gg, etc.
        # TODO: Add text objects: iw, aw, i", a", etc.

        if target_range_lines: # Line-wise operation
            print(f"Executing {operator.name} on lines {target_range_lines[0]} to {target_range_lines[1]}")
            num_lines_to_op = target_range_lines[1] - target_range_lines[0] + 1
            first_line_to_op = target_range_lines[0]
            
            if operator == Operator.DELETE:
                self.renderer.handle_lines_deleted(delete_idx=first_line_to_op, num_deleted_lines=num_lines_to_op)
                for _ in range(num_lines_to_op):
                    if first_line_to_op < self.buffer.get_line_count():
                        self.buffer.lines.pop(first_line_to_op)
                if not self.buffer.lines: self.buffer.lines.append("")
                self.buffer._mark_dirty()
                self.cursor.line = min(first_line_to_op, self.buffer.get_line_count() - 1)
                self.cursor.col = 0
            # TODO: Add CHANGE and YANK for line ranges later
            self.state.reset_operator_state()
        elif end_pos_inclusive: # Character-wise operation
            print(f"Executing {operator.name} from {start_pos} to char at {end_pos_inclusive}")
            # For 'dl' or 'dh' on a single char:
            op_line, op_col = end_pos_inclusive[0], end_pos_inclusive[1]
            if operator == Operator.DELETE:
                self.renderer.invalidate_line_cache(op_line)
                deleted = self.buffer.delete_char_at_cursor(op_line, op_col)
                if deleted:
                    self.buffer._mark_dirty()
                    self.cursor.line = op_line
                    self.cursor.col = op_col
                    if self.cursor.col >= len(self.buffer.get_line(op_line) or "") and self.cursor.col > 0 :
                        self.cursor.col -=1
            # TODO: Add CHANGE and YANK for char ranges later
            self.state.reset_operator_state()
        else:
            # Not a recognized motion for the operator, or an incomplete sequence
            if event.key in [pg.K_d, pg.K_c, pg.K_y] or event.key == pg.K_ESCAPE:
                 self.state.reset_operator_state()
                 action_taken = True
            else: # Unrecognized motion key
                 print(f"Unknown motion key {pg.key.name(event.key)} for operator {operator.name}")
                 action_taken = False

        return action_taken