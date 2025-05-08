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

