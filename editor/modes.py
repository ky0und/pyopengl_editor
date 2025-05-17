from enum import Enum, auto

class EditorMode(Enum):
    NORMAL = auto()
    INSERT = auto()
    # VISUAL = auto() # TODO
    COMMAND = auto()
    OPERATOR_PENDING = auto()

class Operator(Enum):
    NONE = auto()   # pending state
    DELETE = auto() # 'd' - (delete)
    CHANGE = auto() # 'c' - (delete then insert)
    YANK = auto()   # 'y' - (copy)

class EditorState:
    def __init__(self):
        self.mode = EditorMode.NORMAL
        self.viewport_start_line = 0
        
        self.command_buffer = ""
        self.command_cursor_pos = 0
        self.previous_mode = EditorMode.NORMAL
        self.active_operator: Operator = Operator.NONE
        self.operator_pending_start_cursor_pos = None
        self.pending_operator_keystrokes = "" # To capture multi-key operators like 'dd'

    def switch_to_mode(self, new_mode: EditorMode, preserve_command_state=False):
        current_mode = self.mode
        # print(f"Switching from {current_mode.name} to {new_mode.name} mode")
        
        if current_mode == new_mode and not (current_mode == EditorMode.COMMAND and preserve_command_state):
            if current_mode == EditorMode.COMMAND and preserve_command_state:
                 self.mode = new_mode
            return

        if current_mode == EditorMode.COMMAND and not preserve_command_state:
            self.clear_command()
        elif current_mode == EditorMode.OPERATOR_PENDING:
            self._clear_internal_operator_state()

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

    def _clear_internal_operator_state(self):
        """Only clears the variables, does not change mode."""
        self.active_operator = Operator.NONE
        self.operator_pending_start_cursor_pos = None
        self.pending_operator_keystrokes = ""

    def start_operator(self, operator: Operator, cursor_pos):
        if self.mode == EditorMode.OPERATOR_PENDING:
            self._clear_internal_operator_state() 

        self.active_operator = operator
        self.operator_pending_start_cursor_pos = cursor_pos
        self.pending_operator_keystrokes = ""
        self.switch_to_mode(EditorMode.OPERATOR_PENDING)
        print(f"Operator pending: {operator.name} from {cursor_pos}")

    def reset_operator_state(self):
        """Clears operator state and ensures transition to NORMAL mode."""
        self.switch_to_mode(EditorMode.NORMAL)