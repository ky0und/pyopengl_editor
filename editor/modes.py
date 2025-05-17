from enum import Enum, auto

class EditorMode(Enum):
    NORMAL = auto()
    INSERT = auto()
    # VISUAL = auto() # TODO
    COMMAND = auto() # TODO

class EditorState:
    def __init__(self):
        self.mode = EditorMode.NORMAL
        self.viewport_start_line = 0
        
        self.command_buffer = ""
        self.command_cursor_pos = 0
        self.previous_mode = EditorMode.NORMAL

    def switch_to_mode(self, new_mode: EditorMode, preserve_command_state=False):
        current_mode = self.mode
        # print(f"Switching from {current_mode.name} to {new_mode.name} mode")
        
        if new_mode == EditorMode.COMMAND and current_mode != EditorMode.COMMAND:
            self.previous_mode = current_mode # Store mode to return to
            if not preserve_command_state:
                self.command_buffer = ":"
                self.command_cursor_pos = 1
        elif current_mode == EditorMode.COMMAND and new_mode != EditorMode.COMMAND:
            if not preserve_command_state:
                self.command_buffer = ""
                self.command_cursor_pos = 0
        
        self.mode = new_mode

    def clear_command(self):
        self.command_buffer = ""
        self.command_cursor_pos = 0