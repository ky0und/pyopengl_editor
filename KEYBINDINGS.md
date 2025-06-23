# PyOpenGL Vim-Like Editor - Keyboard Operations Documentation

This document outlines the keyboard operations currently implemented in the editor.

## Editor Modes

The editor operates in several distinct modes:

*   **NORMAL Mode:** Default mode for navigation, executing commands, and entering other modes.
*   **INSERT Mode:** Used for typing and inserting text directly into the buffer.
*   **VISUAL Mode (`v`):** Character-wise selection of text.
*   **VISUAL LINE Mode (`V`):** Linewise selection of text.
*   **COMMAND Mode (`:`):** Used for entering Ex-like commands (e.g., for file operations, quitting).
*   **OPERATOR-PENDING Mode:** A temporary mode entered after an operator key (like `d`, `c`, `y`) is pressed in NORMAL mode, waiting for a motion or text object.

---

## Global Operations

*   **`Esc`**:
    *   From **INSERT Mode**: Switches to **NORMAL Mode**. Cursor moves left if possible.
    *   From **COMMAND Mode**: Cancels command input, returns to previous mode (usually NORMAL).
    *   From **OPERATOR-PENDING Mode**: Cancels operator, returns to **NORMAL Mode**.
    *   From **VISUAL / VISUAL LINE Mode**: Exits Visual mode, returns to **NORMAL Mode**.

---

## NORMAL Mode Operations

### Mode Switching & Entry

*   **`i`**: Enter **INSERT Mode** before the current cursor position.
*   **`a`**: Enter **INSERT Mode** after the current cursor position (append).
*   **`o`**: Open a new line below the current line and enter **INSERT Mode**.
*   **`O`** (Shift + `o`): Open a new line above the current line and enter **INSERT Mode**.
*   **`:`** (Shift + `;`): Enter **COMMAND Mode**.
*   **`v`**: Enter **VISUAL Mode** (character-wise selection). Anchor set at current cursor.
*   **`V`** (Shift + `v`): Enter **VISUAL LINE Mode** (linewise selection). Anchor set at current cursor.

### Cursor Movement

*   **`h`**: Move cursor one character left (does not wrap).
*   **`l`**: Move cursor one character right (stops at last character, does not wrap).
*   **`k`**: Move cursor one line up. Viewport may scroll if cursor at top edge.
*   **`j`**: Move cursor one line down. Viewport may scroll if cursor at bottom edge.
*   **`0`** (zero or Shift + `)` on some layouts): Move cursor to the beginning of the current line (column 0).
*   **`^`** (Shift + `6`): Move cursor to the first non-whitespace character on the current line.
*   **`$`** (Shift + `4`): Move cursor to the end of the current line (last character).
*   **`w`**: Move cursor forward to the start of the next word (treats newlines as whitespace).
*   **`b`**: Move cursor backward to the start of the previous/current word (treats newlines as whitespace).
*   **`e`**: Move cursor forward to the end of the current/next word (treats newlines as whitespace).
*   **`PageUp`**: Scroll viewport up by approximately one page. Cursor moves to top of new view. (Only in Insert Mode).
*   **`PageDown`**: Scroll viewport down by approximately one page. Cursor moves to bottom of new view. (Only in Insert Mode).
*   **`Ctrl + b`**: Scroll viewport up by approximately one page (Vim-like). Cursor moves to top of new view.
*   **`Ctrl + f`**: Scroll viewport down by approximately one page (Vim-like). Cursor moves to bottom of new view.

### Editing (Operators & Direct Commands)

*   **`x`**: Delete the character under the cursor.
*   **`d`**: Initiate **DELETE** operator. Enters **OPERATOR-PENDING Mode**.
    *   **`dd`**: Delete current line (text yanked).
    *   **`dj`**: Delete current and next line (text yanked).
    *   **`dk`**: Delete current and previous line (text yanked).
    *   **`dl`**: Delete character under cursor (text yanked).
    *   **`dh`**: Delete character to the left (text yanked).
*   **`c`**: Initiate **CHANGE** operator. Enters **OPERATOR-PENDING Mode**.
    *   **`cc`**: Delete current line, then enter **INSERT Mode** (text yanked).
*   **`y`**: Initiate **YANK** (copy) operator. Enters **OPERATOR-PENDING Mode**.
    *   **`yy`**: Yank current line.
    *   **`yj`**: Yank current and next line (text yanked).
    *   **`yk`**: Yank current and previous line (text yanked).
    *   **`yl`**: Yank character under cursor (text yanked).
    *   **`yh`**: Yank character to the left (text yanked).

### Yank and Put (Copy/Paste)

*   **`p`**: Put (paste) after cursor:
    *   Linewise: Below current line. Cursor to start of first pasted line.
    *   Charwise: After cursor character. Cursor to end of pasted text. Handles multi-line charwise pastes.
*   **`P`** (Shift + `p`): Put (paste) before cursor:
    *   Linewise: Above current line. Cursor to start of first pasted line.
    *   Charwise: Before cursor character. Cursor to start of pasted text. Handles multi-line charwise pastes.

---

## INSERT Mode Operations

### Text Input

*   **Printable Characters**: Insert character at cursor.
*   **`Tab`**: Insert 4 spaces.

### Editing

*   **`Enter` / `Return`**: Split line at cursor.
*   **`Backspace`**: Delete character left of cursor, or merge with previous line if at BOL.
*   **`Delete`**: Delete character *after* (or at) cursor, or merge with next line if at EOL.

### Navigation

*   **`Arrow Left`**: Move cursor left (wraps to previous line).
*   **`Arrow Right`**: Move cursor right (wraps to next line).
*   **`Arrow Up`**: Move cursor up. Viewport may scroll.
*   **`Arrow Down`**: Move cursor down. Viewport may scroll.
*   **`PageUp`**: Scroll viewport up. Cursor to top of new view.
*   **`PageDown`**: Scroll viewport down. Cursor to bottom of new view.

---

## VISUAL Mode & VISUAL LINE Mode Operations

*   Entered from NORMAL mode using `v` (character-wise) or `V` (linewise).
*   **`Esc`**: Exit Visual mode, return to NORMAL Mode.

### Selection Movement

*   Uses NORMAL mode movement keys to extend the selection:
    *   **`h`, `l`, `k`, `j`**
    *   **`w`, `b`, `e`**
    *   **`PageUp`, `PageDown`**

### Operators on Selection

*   Once text is selected, pressing an operator key applies it to the selection and returns to NORMAL mode.
*   **`d`**: Delete the selected text (text is also yanked).
*   **`c`**: Delete the selected text and enter **INSERT Mode** at the start of the selection area (text is also yanked).
*   **`y`**: Yank (copy) the selected text into the default register.

---

## COMMAND Mode Operations

*   Entered by typing **`:`** in NORMAL mode.

### Editing Command Line

*   **Printable Characters**: Append to command.
*   **`Backspace`**: Delete char in command. Exits if command was just `:`.
*   **`Arrow Left` / `Arrow Right`**: Move command cursor.
*   **`Esc`**: Exit COMMAND Mode.
*   **`Enter` / `Return`**: Execute command.

### Supported Commands

*   **`:e <filename>`**: Edit (open) file.
*   **`:w`**: Write to current file.
*   **`:w <filename>`**: Write to specified file.
*   **`:q`**: Quit (errors if buffer is dirty).
*   **`:q!`**: Force quit.
*   **`:wq`**: Write and quit.
*   **(Unknown commands display an error)**

---
