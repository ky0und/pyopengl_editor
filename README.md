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
- [ ] </strike> Visual Mode & Mouse Support </strike>
  - [ ] </strike> Visual Mode </strike>
      - [ ] </strike> Enter Visual mode (v) </strike>
      - [ ] </strike> Track selection start and end points (line, col) </strike>
      - [ ] </strike> Highlight selected text (rendering/renderer.py) </strike>
      - [ ] </strike> Apply operators (d, y) to the selection </strike>
  - [ ] </strike> Mouse Input  </strike>
      - [ ] </strike> Click to position cursor: Convert screen coordinates to (line, col) </strike>
      - [ ] </strike> Drag to select text: Update visual selection </strike>  
      - [ ] </strike> Scroll wheel for viewport scrolling </strike>
- [ ] Polish & Advanced Features
  - [x] Status Bar  
  - [x] Command Line UI
  - [ ] Basic Syntax Highlighting
  - [ ] Search 
  - [ ] Text Rendering Optimizations 
  - [ ] Configuration Files 

