from enum import Enum, auto

class EditorMode(Enum):
    NORMAL = auto()
    INSERT = auto()
    VISUAL = auto()
    VISUAL_LINE = auto()
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

        # Register for yank/put
        self.default_register = {
            "text": "",
            "type": "char"       # "char" or "line" (influences 'p' behavior), TODO: Change this to an enum later
        }

        self.current_syntax_rules = None
        self.current_language_name = None

        self.visual_mode_anchor = None

    def _clear_visual_selection_state(self):
        self.visual_mode_anchor = None

    def set_register(self, text_content, type_is_linewise):
        self.default_register["text"] = text_content
        self.default_register["type"] = "line" if type_is_linewise else "char"
        print(f"Register set: type='{self.default_register['type']}', content='{text_content[:50]}...'")

    def set_syntax_highlighting(self, rules, language_name=None):
        """Sets the syntax highlighting rules to be used."""
        self.current_syntax_rules = rules
        self.current_language_name = language_name
        if rules:
            print(f"Syntax highlighting enabled for: {language_name or 'Unknown Language'}")
        else:
            print("Syntax highlighting disabled.")

    def get_register_content(self):
        return self.default_register["text"], self.default_register["type"] == "line"

    def switch_to_mode(self, new_mode: EditorMode, preserve_command_state=False, anchor_pos=None):
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
        elif current_mode in [EditorMode.VISUAL, EditorMode.VISUAL_LINE]:
            if new_mode not in [EditorMode.VISUAL, EditorMode.VISUAL_LINE]:
                 self._clear_visual_selection_state()

        # --- State setup based on ENTERING new_mode ---
        if new_mode == EditorMode.COMMAND and current_mode != EditorMode.COMMAND:
            self.previous_mode = current_mode
            if not preserve_command_state:
                self.command_buffer = ":"
                self.command_cursor_pos = 1
        elif new_mode in [EditorMode.VISUAL, EditorMode.VISUAL_LINE]:
            if current_mode not in [EditorMode.VISUAL, EditorMode.VISUAL_LINE]:
                if anchor_pos:
                    self.visual_mode_anchor = anchor_pos
                else:
                    print("Warning: Anchor position not explicitly set for Visual mode entry.")
        
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