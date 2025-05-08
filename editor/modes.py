from enum import Enum, auto

class EditorMode(Enum):
    NORMAL = auto()
    INSERT = auto()
    # VISUAL = auto() # TODO
    # COMMAND = auto() # TODO

class EditorState:
    def __init__(self):
        self.mode = EditorMode.NORMAL
        self.viewport_start_line = 0

    def switch_to_mode(self, new_mode: EditorMode):
        print(f"Switching from {self.mode.name} to {new_mode.name} mode")
        self.mode = new_mode