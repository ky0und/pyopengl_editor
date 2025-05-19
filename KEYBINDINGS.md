# PyOpenGL Vim-Like Editor - Keyboard Operations Documentation

This document outlines the keyboard operations currently implemented in the editor.

## Editor Modes

The editor operates in several distinct modes:

*   **NORMAL Mode:** Default mode for navigation, executing commands, and entering other modes.
*   **INSERT Mode:** Used for typing and inserting text directly into the buffer.
*   **COMMAND Mode:** Used for entering Ex-like commands (e.g., for file operations, quitting).
*   **OPERATOR-PENDING Mode:** A temporary mode entered after an operator key (like `d`, `c`, `y`) is pressed, waiting for a motion or text object.

---

## Global Operations (Available in specific modes as noted)

*   **`Esc`**:
    *   From **INSERT Mode**: Switches to **NORMAL Mode**. The cursor typically moves one position to the left if not at the beginning of the line.
    *   From **COMMAND Mode**: Cancels the current command input and returns to the previous mode (usually NORMAL).
    *   From **OPERATOR-PENDING Mode**: Cancels the pending operator and returns to **NORMAL Mode**.

---

## NORMAL Mode Operations

### Entering Other Modes

*   **`i`**: Enter **INSERT Mode** before the current cursor position.
*   **`a`**: Enter **INSERT Mode** after the current cursor position (append).
*   **`o`**: Open a new line below the current line and enter **INSERT Mode**.
*   **`O`** (Shift + `o`): Open a new line above the current line and enter **INSERT Mode**.
*   **`:`** (Shift + `;`): Enter **COMMAND Mode**. The command line appears at the bottom, pre-filled with `:`.

### Cursor Movement

*   **`h`**: Move cursor one character to the left (does not wrap to previous line).
*   **`l`**: Move cursor one character to the right (stops at the last character of the line, does not wrap).
*   **`k`**: Move cursor one line up.
*   **`j`**: Move cursor one line down.

### Editing (Operators & Direct Commands)

*   **`x`**: Delete the character under the cursor (similar to `dl`).
*   **`d`**: Initiate **DELETE** operator. Enters **OPERATOR-PENDING Mode**.
    *   **`dd`**: Delete the current line (text is also yanked to default register).
    *   **`dj`**: Delete the current line and the line below (rudimentary).
    *   **`dk`**: Delete the current line and the line above (rudimentary).
    *   **`dl`**: Delete character under the cursor (like `x`).
    *   **`dh`**: Delete character to the left of the cursor (rudimentary).
*   **`c`**: Initiate **CHANGE** operator. Enters **OPERATOR-PENDING Mode**.
    *   **`cc`**: Delete the current line, then enter **INSERT Mode** on the (now empty) line (text is also yanked).
    *   *(Other `c` + motion combinations are placeholders)*
*   **`y`**: Initiate **YANK** (copy) operator. Enters **OPERATOR-PENDING Mode**.
    *   **`yy`** (or `Y`): Yank the current line into the default register.
    *   **`yj`**: Yank the current line and the line below (rudimentary, linewise).
    *   **`yk`**: Yank the current line and the line above (rudimentary, linewise).
    *   **`yl`**: Yank the character under the cursor (rudimentary, charwise).
    *   **`yh`**: Yank the character to the left of the cursor (rudimentary, charwise).

### Yank and Put (Copy/Paste)

*   **(Yank operations are listed above under operator `y`)**
*   **`p`**: Put (paste) the content of the default register:
    *   If register contains linewise text: Puts the line(s) *below* the current line. Cursor moves to the start of the first pasted line.
    *   If register contains charwise text: Puts the text *after* the current cursor position. Cursor moves to the end of the pasted text.
*   **`P`** (Shift + `p`): Put (paste) the content of the default register:
    *   If register contains linewise text: Puts the line(s) *above* the current line. Cursor moves to the start of the first pasted line.
    *   If register contains charwise text: Puts the text *before* the current cursor position. Cursor moves to the start of the pasted text.

---

## INSERT Mode Operations

### Text Input

*   **Printable Characters**: Insert the character at the cursor position.
*   **`Tab`**: Inserts 4 spaces (currently hardcoded).

### Editing

*   **`Enter` / `Return`**: Split the current line at the cursor position, moving the text after the cursor to a new line below.
*   **`Backspace`**:
    *   If cursor is not at the beginning of a line: Deletes the character to the left of the cursor.
    *   If cursor is at the beginning of a line (and not the first line): Merges the current line with the previous line.

### Navigation (Arrow Keys)

*   **`Arrow Left`**: Move cursor one character left (can wrap to end of previous line).
*   **`Arrow Right`**: Move cursor one character right (can wrap to start of next line).
*   **`Arrow Up`**: Move cursor one line up.
*   **`Arrow Down`**: Move cursor one line down.

---

## COMMAND Mode Operations

*   Entered by typing **`:`** in NORMAL mode.
*   Command line appears at the bottom of the screen.

### Editing the Command Line

*   **Printable Characters**: Append to the command buffer at the command cursor.
*   **`Backspace`**: Delete character before the command cursor. If command buffer is just `:` and backspace is pressed, exits COMMAND mode.
*   **`Arrow Left`**: Move command cursor left (stops after the initial `:`).
*   **`Arrow Right`**: Move command cursor right.
*   **`Esc`**: Exit COMMAND Mode and return to the previous mode, clearing the command buffer.
*   **`Enter` / `Return`**: Execute the command in the command buffer.

### Supported Commands

*   **`:e <filename>`**: Open (edit) the specified file. Clears current buffer, loads new file.
    *   Example: `:e myfile.txt`
*   **`:w`**: Write (save) the current buffer to its associated filename. If no filename is associated, it shows an error.
*   **`:w <filename>`**: Write (save) the current buffer to the specified `<filename>`. Updates the buffer's associated filename.
    *   Example: `:w newfile.txt`
*   **`:q`**: Quit the editor.
    *   If the buffer has unsaved changes (`dirty`), an error message is displayed, and the editor does not quit.
*   **`:q!`**: Force quit the editor, discarding any unsaved changes.
*   **`:wq`**: Write (save) the current buffer and then quit.
    *   If no filename is associated and no filename is provided, an error is displayed.
    *   Example: `:wq` (saves to current file then quits)
    *   Example: `:wq myfile.txt` (saves to `myfile.txt` then quits)
*   **(Unknown commands)**: Display an error message in the command line.

---

This documentation reflects the state of implemented features. More commands and functionalities will be added in subsequent development phases.