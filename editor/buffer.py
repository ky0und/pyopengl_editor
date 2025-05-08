class Buffer:
    def __init__(self, initial_content=None):
        if initial_content:
            self.lines = initial_content.splitlines()
        else:
            self.lines = [""] # Start with one empty line

    def get_line(self, line_num):
        if 0 <= line_num < len(self.lines):
            return self.lines[line_num]
        return None

    def get_line_count(self):
        return len(self.lines)

    def insert_char(self, line_num, col, char):
        if 0 <= line_num < len(self.lines):
            line = self.lines[line_num]
            self.lines[line_num] = line[:col] + char + line[col:]

    def delete_char(self, line_num, col):
        """Deletes the character before (line_num, col)"""
        if 0 <= line_num < len(self.lines):
            line = self.lines[line_num]
            if col > 0 and len(line) > 0:
                self.lines[line_num] = line[:col-1] + line[col:]
                return True # Deletion occurred
            elif col == 0 and line_num > 0: # Backspace at start of line
                prev_line_len = len(self.lines[line_num-1])
                self.lines[line_num-1] += self.lines.pop(line_num)
                return True # Line merged
        return False

    def delete_char_at_cursor(self, line_num, col):
        """Deletes the character at (line_num, col), not before it."""
        if 0 <= line_num < len(self.lines):
            line = self.lines[line_num]
            if 0 <= col < len(line):
                self.lines[line_num] = line[:col] + line[col+1:]
                return True # Deletion occurred
        return False

    def split_line(self, line_num, col):
        if 0 <= line_num < len(self.lines):
            line = self.lines[line_num]
            self.lines.insert(line_num + 1, line[col:])
            self.lines[line_num] = line[:col]