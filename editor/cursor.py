class Cursor:
    def __init__(self, line=0, col=0, blink_timer=0, visible=True, blink_rate=500):
        self.line = line
        self.col = col
        self.blink_timer = blink_timer
        self.blink_rate = blink_rate #miliseconds
        self.visible = True

    def move_right(self, buffer_obj):
        current_line_len = len(buffer_obj.get_line(self.line))
        if self.col < current_line_len:
            self.col += 1
        elif self.line < buffer_obj.get_line_count() - 1: # Move to start of next line
            self.line += 1
            self.col = 0
            
    def move_left(self, buffer_obj):
        if self.col > 0:
            self.col -= 1
        elif self.line > 0: # Move to end of previous line
            self.line -= 1
            self.col = len(buffer_obj.get_line(self.line))

    def move_up(self, buffer_obj):
        if self.line > 0:
            self.line -= 1
            self.col = min(self.col, len(buffer_obj.get_line(self.line)))
            
    def move_down(self, buffer_obj):
        if self.line < buffer_obj.get_line_count() - 1:
            self.line += 1
            self.col = min(self.col, len(buffer_obj.get_line(self.line)))
            
    def set_pos(self, line, col, buffer_obj):
        self.line = max(0, min(line, buffer_obj.get_line_count() -1))
        # Ensure col is within the bounds of the new line
        self.col = max(0, min(col, len(buffer_obj.get_line(self.line) or "")))

