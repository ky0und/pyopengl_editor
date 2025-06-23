class Cursor:
    def __init__(self, line=0, col=0, blink_timer=0, visible=True, blink_rate=500):
        self.line = line
        self.col = col
        self.blink_timer = blink_timer
        self.blink_rate = blink_rate # Miliseconds
        self.visible = True

    def move_right(self, buffer_obj, mode_is_normal=False):
        current_line_text = buffer_obj.get_line(self.line)
        if current_line_text is None: return
        current_line_len = len(current_line_text)

        if mode_is_normal:
            # 'l' in Normal mode: stop at last char if line not empty.
            # If line empty, col stays 0. Max col is len - 1.
            # Vim's 'l' does not move to next line.
            effective_eol = max(0, current_line_len - 1) if current_line_len > 0 else 0
            if self.col < effective_eol:
                self.col += 1
        else: # Insert mode
            if self.col < current_line_len:
                self.col += 1
            # Wrap to start of next line if at the very end
            elif self.col == current_line_len and self.line < buffer_obj.get_line_count() - 1:
                self.line += 1
                self.col = 0
            
    def move_left(self, buffer_obj, mode_is_normal=False):
        if self.col > 0:
            self.col -= 1
        elif not mode_is_normal and self.line > 0: # Vim's 'h' in Normal mode does not wrap
            self.line -= 1
            self.col = len(buffer_obj.get_line(self.line))


    def move_up(self, buffer_obj):
        if self.line > 0:
            self.line -= 1
            current_line_text = buffer_obj.get_line(self.line)
            if current_line_text is not None:
                 self.col = min(self.col, len(current_line_text))
            else:
                 self.col = 0
            
    def move_down(self, buffer_obj):
        if self.line < buffer_obj.get_line_count() - 1:
            self.line += 1
            current_line_text = buffer_obj.get_line(self.line)
            if current_line_text is not None:
                self.col = min(self.col, len(current_line_text))
            else:
                self.col = 0
            
    def set_pos(self, line, col, buffer_obj):
        self.line = max(0, min(line, buffer_obj.get_line_count() -1))
        current_line_text = buffer_obj.get_line(self.line)
        self.col = max(0, min(col, len(current_line_text or "")))

    def move_to_line_start(self, buffer_obj): # '0'
        self.col = 0
        action_taken = True # Assuming this is always an action

    def move_to_first_non_whitespace(self, buffer_obj): # '^'
        current_line_text = buffer_obj.get_line(self.line) or ""
        stripped_line = current_line_text.lstrip()
        self.col = len(current_line_text) - len(stripped_line)
        action_taken = True

    def move_to_line_end(self, buffer_obj, mode_is_normal=False): # '$'
        current_line_text = buffer_obj.get_line(self.line) or ""
        # In Normal mode, '$' goes to the last char. In Insert, it goes after last char.
        # For operator pending, it often means including the last char.
        if mode_is_normal and len(current_line_text) > 0:
            self.col = len(current_line_text) - 1
        else: # Insert mode, or for operator range end
            self.col = len(current_line_text)
        action_taken = True

    def _is_word_char(self, char):
        return char.isalnum() or char == '_'

    def _is_non_blank_char(self, char):
        return not char.isspace()

    def _is_word_char(self, char_code): # char_code is an integer from ord()
        """
        Checks if a character (given by its ordinal value) is a 'word' character.
        For simplicity: not whitespace. Newlines are handled by the motion logic.
        """
        if char_code is None: return False # E.g. trying to get char beyond buffer
        char = chr(char_code)
        return not char.isspace() # Simplest definition: anything not a space/tab. Newlines are special.

    def _get_char_code_at_cursor(self, buffer_obj, line, col):
        """Safely gets the ordinal value of the character at (line, col)."""
        if not (0 <= line < buffer_obj.get_line_count()):
            return None # Line out of bounds
        
        line_text = buffer_obj.get_line(line)
        if line_text is None or not (0 <= col < len(line_text)):
            return None # Column out of bounds or empty line for that col
        
        return ord(line_text[col])

    def _next_pos(self, buffer_obj, current_line, current_col):
        """Gets the next logical position (l, c), crossing lines. Returns None if EOF."""
        line_text = buffer_obj.get_line(current_line)
        if line_text is not None and current_col < len(line_text):
            return current_line, current_col + 1
        elif current_line < buffer_obj.get_line_count() - 1:
            return current_line + 1, 0
        return None # End of buffer

    def _prev_pos(self, buffer_obj, current_line, current_col):
        """Gets the previous logical position (l, c), crossing lines. Returns None if BOF."""
        if current_col > 0:
            return current_line, current_col - 1
        elif current_line > 0:
            prev_line_text = buffer_obj.get_line(current_line - 1) or ""
            return current_line - 1, len(prev_line_text) # Go to EOL (after last char) of prev line
        return None # Beginning of buffer


    def move_word_forward(self, buffer_obj): # 'w'
        """Moves to the start of the next word. Newlines are like spaces."""
        original_line, original_col = self.line, self.col
        
        # If on a word char, skip to the end of it or next separator (space/newline)
        current_char_code = self._get_char_code_at_cursor(buffer_obj, self.line, self.col)
        if current_char_code is not None and self._is_word_char(current_char_code):
            while True:
                next_p = self._next_pos(buffer_obj, self.line, self.col)
                if next_p is None: # EOF
                    self.col = len(buffer_obj.get_line(self.line) or "") # Go to EOL
                    return
                
                self.line, self.col = next_p
                char_code_at_new_pos = self._get_char_code_at_cursor(buffer_obj, self.line, self.col)
                if char_code_at_new_pos is None or not self._is_word_char(char_code_at_new_pos):
                    # Moved onto a space, newline (implicit by col=0 on next line), or EOF
                    break 
        
        # Skip separators until word found
        while True:
            char_code_here = self._get_char_code_at_cursor(buffer_obj, self.line, self.col)
            if char_code_here is not None and self._is_word_char(char_code_here):
                # Found start of the next word
                if self.line == original_line and self.col == original_col : # No actual move
                    next_p_final = self._next_pos(buffer_obj, self.line, self.col)
                    if next_p_final: self.line, self.col = next_p_final # make one more step if possible
                    else: return # Truly at end
                return

            next_p = self._next_pos(buffer_obj, self.line, self.col)
            if next_p is None: # EOF reached while skipping separators
                if self.line != original_line or self.col != original_col:
                     self.col = len(buffer_obj.get_line(self.line) or "") # Ensure at EOL
                else: # No progress, revert.
                     self.line, self.col = original_line, original_col
                return
            self.line, self.col = next_p


    def move_to_word_end(self, buffer_obj): # 'e'
        """Moves to the end of the current/next word. Newlines are like spaces."""
        original_line, original_col = self.line, self.col

        next_p_initial = self._next_pos(buffer_obj, self.line, self.col)
        if next_p_initial:
            temp_line, temp_col = next_p_initial
        else: # At EOF, 'e' does nothing
            return

        # Skip separators to find the start of a word
        while True:
            char_code_at_temp = self._get_char_code_at_cursor(buffer_obj, temp_line, temp_col)
            if char_code_at_temp is not None and self._is_word_char(char_code_at_temp):
                break # Found start of a word

            next_p = self._next_pos(buffer_obj, temp_line, temp_col)
            if next_p is None: # EOF reached while skipping separators
                if self.line != original_line or self.col != original_col:
                     self.line = original_line
                     self.col = len(buffer_obj.get_line(original_line) or "")
                else:
                     self.line, self.col = original_line, original_col
                return
            temp_line, temp_col = next_p
        
        # Skip word chars to find its end.
        self.line, self.col = temp_line, temp_col
        while True:
            next_p = self._next_pos(buffer_obj, self.line, self.col)
            if next_p is None: # Reached EOF, current (self.line, self.col) is the EOW
                return

            char_code_at_next = self._get_char_code_at_cursor(buffer_obj, next_p[0], next_p[1])
            if char_code_at_next is None or not self._is_word_char(char_code_at_next):
                # Next char is a separator or EOF, so current (self.line, self.col) is EOW
                return 
            
            self.line, self.col = next_p # Advance cursor

    def move_word_backward(self, buffer_obj): # 'b'
        """Moves to the start of the current/previous word. Newlines are like spaces."""
        prev_p_initial = self._prev_pos(buffer_obj, self.line, self.col)
        if prev_p_initial:
            self.line, self.col = prev_p_initial
        else: # At (0,0) or BOF, 'b' does nothing
            self.col = 0
            return

        # Skip separators
        while True:
            char_code_here = self._get_char_code_at_cursor(buffer_obj, self.line, self.col)
            if char_code_here is not None and self._is_word_char(char_code_here):
                # Found a word character (this is end of the word we seek start of)
                break
            
            prev_p = self._prev_pos(buffer_obj, self.line, self.col)
            if prev_p is None: # BOF reached while skipping separators
                self.line, self.col = 0, 0
                return
            self.line, self.col = prev_p

        # Move backward to find word start.
        while True:
            prev_p = self._prev_pos(buffer_obj, self.line, self.col)
            if prev_p is None: # Reached BOF, current (self.line, self.col) is start of word
                return

            char_code_at_prev = self._get_char_code_at_cursor(buffer_obj, prev_p[0], prev_p[1])
            if char_code_at_prev is None or not self._is_word_char(char_code_at_prev):
                # Previous char is a separator or BOF, so current (self.line, self.col) is start of word
                return
            
            self.line, self.col = prev_p

    def _clamp_col(self, buffer_obj):
        """Ensures cursor column is valid for the current line."""
        current_line_text = buffer_obj.get_line(self.line) or ""
        self.col = max(0, min(self.col, len(current_line_text)))