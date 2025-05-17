import os

class Buffer:
    def __init__(self, initial_content=None, filepath=None):
        self.lines = [""]
        self.filepath = filepath
        self.dirty = False

        if filepath:
            self.load_from_file(filepath)
        elif initial_content:
            self.lines = initial_content.splitlines()
            if not self.lines:
                self.lines = [""]
            self._mark_dirty() # Needs saving

    def get_line(self, line_num):
        if 0 <= line_num < len(self.lines):
            return self.lines[line_num]
        return None

    def get_line_count(self):
        return len(self.lines)
    
    def _mark_dirty(self):
        """Helper method for marking buffer needs saving"""
        if not self.dirty:
            self.dirty = True

    def insert_char(self, line_num, col, char):
        if 0 <= line_num < len(self.lines):
            line = self.lines[line_num]
            self.lines[line_num] = line[:col] + char + line[col:]
            self._mark_dirty()

    def delete_char(self, line_num, col):
        """Deletes the character before (line_num, col), returns true if deleted anything"""
        if 0 <= line_num < len(self.lines):
            line = self.lines[line_num]
            if col > 0 and len(line) > 0:
                self.lines[line_num] = line[:col-1] + line[col:]
                self._mark_dirty()
                return True # Deletion occurred
            elif col == 0 and line_num > 0: # Backspace at start of line
                self.lines[line_num-1] += self.lines.pop(line_num)
                self._mark_dirty()
                return True # Deletion occurred
        return False

    def delete_char_at_cursor(self, line_num, col):
        """Deletes the character at (line_num, col), not before it."""
        if 0 <= line_num < len(self.lines):
            line = self.lines[line_num]
            if 0 <= col < len(line):
                self.lines[line_num] = line[:col] + line[col+1:]
                self._mark_dirty()
                return True # Deletion occurred
        return False

    def split_line(self, line_num, col):
        if 0 <= line_num < len(self.lines):
            line = self.lines[line_num]
            self.lines.insert(line_num + 1, line[col:])
            self.lines[line_num] = line[:col]
            self._mark_dirty()

    def get_content_as_string(self):
        return "\n".join(self.lines)

    def load_from_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.lines = [line.rstrip('\n\r') for line in f.readlines()]
            if not self.lines:
                self.lines = [""]
            self.filepath = filepath
            self.dirty = False
            print(f"File '{filepath}' loaded.")
            return True
        except FileNotFoundError:
            print(f"Error: File not found '{filepath}'. Creating new buffer.")
            self.lines = [""]
            self.filepath = filepath # Still set filepath for a potential first save
            self.dirty = False
            return False
        except Exception as e:
            print(f"Error loading file '{filepath}': {e}")
            # self.lines = ["Error loading file."]
            # self.filepath = None
            # self.dirty = False
            return False
        
    def save_to_file(self, filepath=None):
        target_path = filepath if filepath else self.filepath
        if not target_path:
            print("Error: No filepath specified for saving.")
            return False
        try:
            # Ensure directory exists
            dir_name = os.path.dirname(target_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name)

            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(self.get_content_as_string())
                if self.lines and (self.lines[-1] or len(self.lines) > 1):
                     f.write('\n')

            self.filepath = target_path
            self.dirty = False
            print(f"File saved to '{target_path}'.")
            return True
        except Exception as e:
            print(f"Error saving file '{target_path}': {e}")
            return False