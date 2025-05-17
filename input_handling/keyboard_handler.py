import pygame as pg
from editor.modes import EditorMode, EditorState
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

        # --- Global Mode-Independent Keys ---
        if event.key == pg.K_ESCAPE:
            if self.state.mode == EditorMode.INSERT:
                self.state.switch_to_mode(EditorMode.NORMAL)
                current_line_text = self.buffer.get_line(self.cursor.line)
                if self.cursor.col > 0 and self.cursor.col <= len(current_line_text or ""):
                    self.cursor.col -= 1
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

        # --- File Operations (Ctrl+Key) ---
        if mods & pg.KMOD_CTRL:
            if event.key == pg.K_o: # Ctrl + O: Open File
                try:
                    filepath_to_open = input("Enter filepath to open: ")
                    if filepath_to_open:
                        self._reset_buffer_state_for_new_load()
                        self.buffer.load_from_file(filepath_to_open.strip())
                        action_taken = True
                except Exception as e:
                    print(f"Error during file open prompt: {e}")
                return True # Consume Ctrl+O event

            elif event.key == pg.K_s: 
                if mods & pg.KMOD_SHIFT: # Ctrl + S or Ctrl + Shift + S: Save As
                    try:
                        filepath_to_save = input(f"Save As (current: {self.buffer.filepath or 'Unsaved'}): ")
                        if filepath_to_save:
                            self.buffer.save_to_file(filepath_to_save.strip())
                            action_taken = True
                    except Exception as e:
                        print(f"Error during Save As prompt: {e}")
                else: # Ctrl + S or Ctrl + Shift + S: Save As
                    if self.buffer.filepath:
                        self.buffer.save_to_file()
                        action_taken = True
                    else:
                        try:
                            filepath_to_save = input("Save As (new file): ")
                            if filepath_to_save:
                                self.buffer.save_to_file(filepath_to_save.strip())
                                action_taken = True
                        except Exception as e:
                            print(f"Error during Save prompt: {e}")
                return True # Consume Ctrl+S event

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