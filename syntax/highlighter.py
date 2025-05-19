import re

# Token types
TOKEN_TYPE_DEFAULT = "default"
TOKEN_TYPE_KEYWORD = "keyword"                  # def, class, if, for, return, import, from, etc.
TOKEN_TYPE_OPERATOR = "operator"                # +, -, *, /, =, <, >, etc. (currently not distinct)
TOKEN_TYPE_BRACE = "brace"                      # (), [], {} (currently not distinct)
TOKEN_TYPE_COMMENT = "comment"                  # # ...
TOKEN_TYPE_STRING = "string"                    # "...", '...'
TOKEN_TYPE_FSTRING_BG = "fstring_bg"            # Background or special color for f-string content
TOKEN_TYPE_FSTRING_INTERP = "fstring_interp"    # {} inside f-strings
TOKEN_TYPE_NUMBER = "number"                    # 123, 45.6, 0xFF
TOKEN_TYPE_FUNCTION_CALL = "function_call"      # foo()
TOKEN_TYPE_FUNCTION_DEF = "function_def"        # Name in 'def foo():'
TOKEN_TYPE_CLASS_DEF = "class_def"              # Name in 'class MyClass:'
TOKEN_TYPE_DECORATOR = "decorator"              # @my_decorator
TOKEN_TYPE_BUILTIN = "builtin"                  # print, len, str, int, list, dict, etc.
TOKEN_TYPE_MAGIC_METHOD = "magic_method"        # __init__, __str__
TOKEN_TYPE_SELF_PARAM = "self_param"            # 'self' or 'cls' as first arg in method

SYNTAX_COLORS = {
    TOKEN_TYPE_DEFAULT: (220, 220, 220),      # Default text (Often light grey/off-white)
    TOKEN_TYPE_KEYWORD: (197, 134, 192),      # Keywords
    "keyword.control": (197, 134, 192),       # if, for, while, return (Magenta-ish)
    "keyword.modifier": (86, 156, 214),       # import, from, as (Blue-ish)
    "keyword.declaration": (197, 134, 192),   # def, class (Magenta-ish)
    TOKEN_TYPE_OPERATOR: (180, 180, 180),     # Operators (Often same as default or slightly dimmer)
    TOKEN_TYPE_BRACE: (220, 220, 220),        # Braces (Often same as default)
    TOKEN_TYPE_COMMENT: (106, 153, 85),       # Comments (Green)
    TOKEN_TYPE_STRING: (206, 145, 120),       # Strings (Orange/Brown) - VSCode uses CE9178
    TOKEN_TYPE_FSTRING_BG: (206, 145, 120),   # Base f-string color (same as string)
    TOKEN_TYPE_FSTRING_INTERP: (86, 156, 214),# {} in f-string (Blue, like variables)
    TOKEN_TYPE_NUMBER: (181, 206, 168),       # Numbers (Light Green/Teal)
    TOKEN_TYPE_FUNCTION_CALL: (220, 220, 170),# Function calls (Yellow-ish) - VSCode uses DDDD9A
    TOKEN_TYPE_FUNCTION_DEF: (220, 220, 170), # Function definition names (Yellow-ish)
    TOKEN_TYPE_CLASS_DEF: (78, 201, 176),     # Class definition names (Teal/Turquoise)
    TOKEN_TYPE_DECORATOR: (220, 220, 170),    # Decorators (Yellow-ish, like functions)
    TOKEN_TYPE_BUILTIN: (86, 156, 214),       # Built-in functions/types (Blue)
    TOKEN_TYPE_MAGIC_METHOD: (220, 220, 170), # __methods__ (Yellow-ish, like functions)
    TOKEN_TYPE_SELF_PARAM: (86, 156, 214),    # 'self', 'cls' (Blue, like variables/builtins)
}

# My personal overrides, remove this later
SYNTAX_COLORS[TOKEN_TYPE_KEYWORD] = SYNTAX_COLORS["keyword.control"] # Default keyword color
SYNTAX_COLORS[TOKEN_TYPE_DEFAULT] = (212, 212, 212) # Common VSCode default text
SYNTAX_COLORS[TOKEN_TYPE_OPERATOR] = SYNTAX_COLORS[TOKEN_TYPE_DEFAULT] # Operators often default
SYNTAX_COLORS[TOKEN_TYPE_BRACE] = SYNTAX_COLORS[TOKEN_TYPE_DEFAULT] # Braces often default

# Python Built-ins (a selection)
PYTHON_BUILTINS = {
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes', 'callable',
    'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir', 'divmod',
    'enumerate', 'eval', 'exec', 'filter', 'float', 'format', 'frozenset', 'getattr',
    'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
    'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview', 'min',
    'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property', 'range',
    'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod',
    'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip', '__import__'
}
# Python "Magic" methods start and end with double underscores
CONTROL_FLOW_KEYWORDS = r'\b(if|elif|else|for|while|try|except|finally|return|yield|pass|break|continue|with|async|await)\b'
IMPORT_KEYWORDS = r'\b(import|from|as)\b'
DECLARATION_KEYWORDS = r'\b(def|class|lambda)\b'
OPERATOR_KEYWORDS = r'\b(in|is|not|and|or)\b' # logical/membership operators
CONSTANT_KEYWORDS = r'\b(True|False|None)\b' # language constants
OTHER_KEYWORDS = r'\b(global|nonlocal|assert|del)\b'

PYTHON_SYNTAX_RULES = [
    # 1. Comments (highest priority)
    (TOKEN_TYPE_COMMENT, re.compile(r'#.*')),

    # 2. Decorators (before function/class defs)
    (TOKEN_TYPE_DECORATOR, re.compile(r'@\w+(\.\w+)*')), # Matches @decorator or @module.decorator

    # 3. Strings
    (TOKEN_TYPE_FSTRING_BG, re.compile(r'[fF][rR]?"""(?:.|\n)*?"""')), # Triple-quoted f-string
    (TOKEN_TYPE_FSTRING_BG, re.compile(r'[fF][rR]?"(?:\\.|[^"\\])*"')),  # Double-quoted f-string
    (TOKEN_TYPE_FSTRING_BG, re.compile(r'[fF][rR]?\'\'\'(?:.|\n)*?\'\'\'')), # Triple-quoted f-string
    (TOKEN_TYPE_FSTRING_BG, re.compile(r'[fF][rR]?\'(?:\\.|[^"\'])*\'')),  # Single-quoted f-string
    
    (TOKEN_TYPE_STRING, re.compile(r'[rR]?"""(?:.|\n)*?"""')), # Raw Triple-quoted
    (TOKEN_TYPE_STRING, re.compile(r'[rR]?"(?:\\.|[^"\\])*"')),  # Raw Double-quoted
    (TOKEN_TYPE_STRING, re.compile(r'[rR]?\'\'\'(?:.|\n)*?\'\'\'')), # Raw Triple-quoted
    (TOKEN_TYPE_STRING, re.compile(r'[rR]?\'(?:\\.|[^"\'])*\'')),  # Raw Single-quoted

    # 4. Keywords (split into categories for potential different styling)
    ("keyword.declaration", re.compile(DECLARATION_KEYWORDS)),
    ("keyword.control", re.compile(CONTROL_FLOW_KEYWORDS)),
    ("keyword.modifier", re.compile(IMPORT_KEYWORDS)),
    (TOKEN_TYPE_KEYWORD, re.compile(OPERATOR_KEYWORDS)), # General keyword for now
    (TOKEN_TYPE_KEYWORD, re.compile(CONSTANT_KEYWORDS)), # General keyword for now
    (TOKEN_TYPE_KEYWORD, re.compile(OTHER_KEYWORDS)),    # General keyword for now

    # 5. Function and Class Definitions
    (TOKEN_TYPE_FUNCTION_DEF, re.compile(r'\b([a-zA-Z_]\w*)\s*(?=\()')), # An identifier followed by (
    (TOKEN_TYPE_CLASS_DEF, re.compile(r'\b([A-Z]\w*)\b(?=\s*[:\(])')),   # CapWord identifier before : or (

    # 6. Magic Methods and self/cls
    (TOKEN_TYPE_MAGIC_METHOD, re.compile(r'\b__\w+__\b')),
    (TOKEN_TYPE_SELF_PARAM, re.compile(r'\b(self|cls)\b(?=\s*[,):])')),


    # 7. Built-ins
    (TOKEN_TYPE_BUILTIN, re.compile(r'\b(' + '|'.join(PYTHON_BUILTINS) + r')\b')),

    # 8. Function Calls (general identifier followed by '()')
    (TOKEN_TYPE_FUNCTION_CALL, re.compile(r'\b([a-zA-Z_]\w*)\s*(?=\()')),

    # 9. Numbers
    (TOKEN_TYPE_NUMBER, re.compile(r'\b0[xX][0-9a-fA-F]+\b')), # Hex
    (TOKEN_TYPE_NUMBER, re.compile(r'\b0[oO][0-7]+\b')),     # Octal
    (TOKEN_TYPE_NUMBER, re.compile(r'\b0[bB][01]+\b')),      # Binary
    (TOKEN_TYPE_NUMBER, re.compile(r'\b\d+\.?\d*([eE][-+]?\d+)?\b')), # Decimal, float, scientific
    
    # Operators and Braces (could be TOKEN_TYPE_DEFAULT if not styled distinctly)
    # (TOKEN_TYPE_OPERATOR, re.compile(r'[+\-*/%=<>&|^~]')),
    # (TOKEN_TYPE_BRACE, re.compile(r'[(){}\[\]]')),
]


def highlight_line(line_text, rules):
    """
    Applies syntax rules to a line of text and returns a list of (token_type, text_segment) tuples.
    This is a simple greedy approach; order of rules matters.
    """
    if not line_text:
        return [(TOKEN_TYPE_DEFAULT, "")]

    tokens = []
    current_pos = 0
    line_len = len(line_text)

    while current_pos < line_len:
        best_match_this_iteration = None # (match_object, token_type)

        # Find the best (earliest starting, then longest) match from current_pos
        for token_type, pattern in rules:
            match = pattern.search(line_text, current_pos) # Search from current_pos onwards
            if match:
                if best_match_this_iteration is None:
                    best_match_this_iteration = (match, token_type)
                else:
                    # If this match starts earlier, it's better
                    if match.start() < best_match_this_iteration[0].start():
                        best_match_this_iteration = (match, token_type)
                    # If it starts at the same place, prefer longer match
                    elif match.start() == best_match_this_iteration[0].start() and \
                         match.end() > best_match_this_iteration[0].end():
                        best_match_this_iteration = (match, token_type)
        
        if best_match_this_iteration:
            match, token_type = best_match_this_iteration
            match_start, match_end = match.span()

            # If there's a gap between current_pos and this match_start, it's default text
            if match_start > current_pos:
                tokens.append((TOKEN_TYPE_DEFAULT, line_text[current_pos:match_start]))
            
            # Add the matched token
            tokens.append((token_type, match.group(0)))
            current_pos = match_end
        else:
            # No more rule matches found for the rest of the line
            if current_pos < line_len:
                tokens.append((TOKEN_TYPE_DEFAULT, line_text[current_pos:]))
            current_pos = line_len
            
    if not tokens: # Should only happen if line_text was empty and was handled, or if it's all spaces
        return [(TOKEN_TYPE_DEFAULT, line_text)]
    return tokens