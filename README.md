# PyOpenGL Text Editor

## Project Overview

It's a vim-like editor but for windows and uses pygame with PyOpenGL 

<video width="320" height="240" controls>
  <source src="./assets/showcase.mp4" type="video/mp4">
</video>


### Core Editor
*   **Modal Editing:**
    *   **NORMAL Mode:** For navigation and commands.
    *   **INSERT Mode:** For text input.
    *   **VISUAL Mode (Character & Line):** For selecting text.
    *   **COMMAND Mode:** For Ex-style commands.
    *   **OPERATOR-PENDING Mode:** For Vim-like `operator + motion` commands.
*   **Buffer Management:**
    *   In-memory text buffer (list of strings).
    *   Tracking of "dirty" (unsaved) state.
*   **Cursor System:**
    *   Line and column-based cursor.
    *   Blinking cursor.

### Rendering (PyOpenGL)
*   All UI elements (text, cursor, status bar, command line, line numbers, selection highlight) are rendered using PyOpenGL.
*   Text rendering using `pygame.freetype` to generate glyphs, which are then managed as OpenGL textures.
*   Line-based texture caching for efficient re-rendering of unchanged lines.
*   **Syntax Highlighting:**
    *   Basic, regex-based highlighting for Python files (`.py`).
    *   Support for keywords, comments, strings, numbers, function/class definitions, decorators, built-ins.
    *   Highlighting is applied conditionally based on file extension.
*   **Visual Feedback:**
    *   Line numbers.
    *   Status bar displaying current mode, filename, dirty status, and active operator.
    *   Command line interface for Ex commands.
    *   Visual selection highlighting (background color for selected region).

### Input & Navigation

Described in KEYBINDINGS.md

## Installation and Running

This editor is built using Python and relies on a few key libraries for graphics and font handling.

### Dependencies

The project requires the following Python packages:

*   `PyOpenGL`: For OpenGL graphics rendering.
*   `pygame`: Used for window creation, event handling, and loading fonts via `pygame.freetype`.

### Setup Instructions

1.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```

2.  **Install Dependencies:**

    Install the dependencies using pip:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ensure Assets:**
    Make sure you have a font file in the `assets/fonts/` directory. The project currently defaults to looking for `Consolas.ttf`. You can change the `FONT_PATH` variable in `main.py` if you wish to use a different TrueType Font (`.ttf`).


4. **Running the Editor:**

Once the setup is complete, you can run the editor from the project's root directory using:

```bash
python main.py
```

5. **Testing the highlighting:** 

Open `syntaxtest.py` or any `.py` file in the editor to see how highlighting works with python files.


