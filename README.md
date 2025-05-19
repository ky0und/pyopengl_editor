# pyopengl_editor
A programming editor made with pyOpenGL


### TODO

- [x] Getting Text on Screen
  - [x] Window Setup  
  - [x] Font Loading & Basic Text Rendering  
  - [x] Basic Buffer  
  - [x] Simplest Input  
  - [x] Basic Cursor 
- [x] Core Editing & Modes
  - [x] Implement Modes  
  - [x] Keyboard Handler per Mode 
      - [x] Abstract the input system to input_handling/keyboard_handler.py
  - [x] Cursor Movement Logic 
  - [x] File Operations (can be considered done as of now)
  - [x] Viewport & Basic Scrolling  
- [ ] Vim-like Operations
  - [x] Operators 
  - [ ] Undo/Redo 
  - [x] Yank & Put
      - [ ] Support multi-line motions 
  - [ ] More Normal Mode Movements
- [ ] ~~ Visual Mode & Mouse Support ~~
  - [ ] ~~ Visual Mode ~~
      - [ ] ~~ Enter Visual mode (v) ~~
      - [ ] ~~ Track selection start and end points (line, col) ~~
      - [ ] ~~ Highlight selected text (rendering/renderer.py) ~~
      - [ ] ~~ Apply operators (d, y) to the selection ~~
  - [ ] ~~ Mouse Input  ~~
      - [ ] ~~ Click to position cursor: Convert screen coordinates to (line, col) ~~
      - [ ] ~~ Drag to select text: Update visual selection ~~  
      - [ ] ~~ Scroll wheel for viewport scrolling ~~
- [ ] Polish & Advanced Features
  - [x] Status Bar  
  - [x] Command Line UI
  - [ ] Basic Syntax Highlighting
  - [ ] Search 
  - [ ] Text Rendering Optimizations 
  - [ ] Configuration Files 

