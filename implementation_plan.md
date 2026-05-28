# UniBoard Comprehensive Overhaul

Complete rewrite of the UniBoard whiteboard application to fix all bugs, improve the UI dramatically, and make every feature fully functional.

## Problems Identified

### Critical Bugs
1. **Import errors** – `QShortcut` imported from wrong module, missing `QApplication` import, `QWidget` missing
2. **Embedded widgets not loading** – HTML, Compiler, Browser canvas types create widgets inside QGraphicsScene via proxy, which makes them hard to interact with and causes rendering issues
3. **Text size not working** – `size_spin` only changes pen width, doesn't affect text size
4. **Shapes not resizable** – Shapes are drawn but cannot be resized after creation
5. **Ctrl+Z and shortcuts not working** – `QShortcut` was imported from wrong module
6. **Outline not editable** – Double-click editing exists but behavior is inconsistent

### UI Problems
1. **Toolbar overflow** – Grid and theme controls hidden behind triple-dot overflow button
2. **Slide count message shown** – Unnecessary "55 slides" info displayed
3. **Agenda overlay shown on non-plain canvas** – Logic exists but UI coupling is fragile
4. **Embedded widgets render inside QGraphicsScene** – They appear as proxied widgets in the scene which makes interaction buggy

## Proposed Changes

### 1. Main Window ([main_window.py](file:///c:/Users/AALEKH%20RAI/OneDrive/Desktop/whiteBoard-Uniboard/ui/main_window.py))

**Complete rewrite** with:
- Proper consolidated imports (all PySide6 classes in correct modules)
- 90% screen size with maximize/fullscreen toggle button
- **Compact single-row toolbar** with icon-only tool buttons + tooltips (no text overflow)
- Grouped toolbar: `[Tools | Colors+Size | Undo/Redo | Grid+Theme | Export | Fullscreen]`
- PDF export using ReportLab
- All keyboard shortcuts properly registered
- Text size properly connected to canvas

### 2. Canvas ([canvas.py](file:///c:/Users/AALEKH%20RAI/OneDrive/Desktop/whiteBoard-Uniboard/ui/canvas.py))

**Major refactor**:
- Use `QStackedWidget` approach: when user switches canvas type, swap between plain QGraphicsView and a full-window embedded widget (HTML/Compiler/Browser) — **NOT** proxied inside the scene
- Shapes: make items selectable + movable after creation, support resize handles
- Text: use `pen_width` (or a separate text size setting) to control font size
- Proper undo/redo that works reliably
- Clean overlay positioning
- Hide agenda + title on non-plain canvases

### 3. Embedded Widgets ([embedded_widgets.py](file:///c:/Users/AALEKH%20RAI/OneDrive/Desktop/whiteBoard-Uniboard/ui/embedded_widgets.py))

- Fix to work as **standalone top-level widgets** (not proxied in QGraphicsScene)
- Improve styling with glassmorphic theme consistency
- Ensure HTML render, Compiler, and Browser all load and function correctly

### 4. Styles ([styles.py](file:///c:/Users/AALEKH%20RAI/OneDrive/Desktop/whiteBoard-Uniboard/ui/styles.py))

- Add `QComboBox` and `QSpinBox` styling to all themes
- Add `QMenuBar` styling
- Improve overall visual polish

### 5. Sidebar ([sidebar.py](file:///c:/Users/AALEKH%20RAI/OneDrive/Desktop/whiteBoard-Uniboard/ui/sidebar.py))

- Ensure double-click rename works properly
- Better visual styling

---

## Key Design Decision: Canvas Type Switching

**Approach**: Use a `QStackedWidget` as the central widget. Stack index 0 = plain whiteboard canvas (QGraphicsView). When switching to HTML/Compiler/Browser, we set the stacked widget index to show the embedded widget directly (not as a proxy inside the graphics scene). This solves all interaction bugs with embedded widgets.

The canvas type selector buttons remain as an overlay on the canvas view AND as part of the stacked widget navigation.

---

## Verification Plan

### Automated Tests
- Run `py main.py` and verify no import errors
- Switch between all 4 canvas types and verify each loads
- Draw shapes, text, lines on plain canvas
- Test Ctrl+Z undo, Ctrl+Y redo
- Test PDF export
- Test code execution in compiler widget

### Manual Verification
- Verify toolbar fits in single row
- Verify theme switching works
- Verify outline editing in sidebar
