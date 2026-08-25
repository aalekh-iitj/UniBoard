# UniBoard - Modern Interactive Whiteboard & Screen Annotation App by AALEKH RAI

UniBoard is a premium, feature-rich Python-based desktop application designed for presenters, educators, developers, and creators. It combines classical digital whiteboard drawing capabilities with modern screen overlays, live web rendering, interactive code compilers, and generative AI features.

---

## Technical Stack & Architecture

- **Core Runtime**: Python 3.14 (fully compatible)
- **GUI & Rendering Framework**: **PySide6** (Qt 6 for Python)
  - Uses `QtWidgets` and `QGraphicsView`/`QGraphicsScene` for high-performance 2D drawing.
  - Uses `QWebEngineView` (Chromium-based) for HTML/Code rendering and live web browsing.
- **Styling**: Modern dark glassmorphic CSS (Qt Style Sheets) with a dynamic theme switcher (Dark Glass, Light Glass, Slate).
- **Core Features**:
  1. **Dual Modes**: Standard Canvas mode & Overlay Annotation mode (floating transparent controls on top of Windows/Screen).
  2. **Page Tree Manager**: Hierarchical nested pages (parent-child slides) that can be reordered, inserted, or deleted.
  3. **Infinite Canvas**: Interactive zoom (scroll wheel) and panning (middle mouse/hand tool) with grid layouts.
  4. **Whiteboard Canvas Tools**: Brush, highlighter, eraser, lines, rectangles, circles, text blocks, undo/redo stack.
  5. **HTML Sandbox**: Render arbitrary HTML/CSS snippets inside the page with paint annotation overlay capability.
  6. **Embedded Web Browser**: Full live web browsing within canvas pages, allowing drawing annotations directly over active web pages.
  7. **Isolated Code Compiler**: An editor supporting multiple languages (Python, JavaScript, etc.) executing in isolated, timeout-guarded subprocesses.
  8. **Real-time Handwriting-to-Text**: Converts handwritten strokes into typography text in real time using stroke coordinate capture.
  9. **AI Page Planner**: Automatically drafts and builds slide decks/topics using Gemini API given a topic and duration.
  10. **Multimodal Q&A / RAG**: Talk to your canvas, ask questions based on PDF/TXT uploads, or query drawn sketches using Gemini Vision API.
  11. **Extra Essentials**: Canvas recording, structured PDF export, and interactive canvas widgets (timers/stopwatches).

---

## File Structure

The project is structured modularly:

```
whiteBoard-Uniboard/
├── README.md               # Project documentation (this file)
├── requirements.txt        # PIP dependencies
├── main.py                 # Application launcher
├── config.py               # Constants, layout rules, and active themes
├── ui/
│   ├── __init__.py
│   ├── main_window.py      # Core layout containing docks and main window logic
│   ├── canvas.py           # Custom drawing canvas (QGraphicsView/QGraphicsScene)
│   ├── overlay.py          # Screen annotation transparent overlay window
│   ├── web_view.py         # Embedded Chromium view with drawing overlay toggle
│   ├── code_editor.py      # Multi-language code editor & runtime panel
│   ├── sidebar.py          # Slide tree navigation & properties panel
│   ├── ai_sidebar.py       # Sidebar dock for slide generation and Q&A chat
│   └── styles.py           # Style definitions for glassmorphic and other themes
├── core/
│   ├── __init__.py
│   ├── page_manager.py     # Slide/Page model representing hierarchical canvas states
│   ├── compiler.py         # Subprocess runner for runtime code isolation
│   ├── handwriting.py      # Stroke-to-text recognition client
│   ├── recorder.py         # Canvas video recorder utility
│   └── ai_engine.py        # Gemini client for planning, Vision analysis, and RAG
└── assets/                 # App icons and graphics
```

---

## Installation & Setup

1. **Clone/Create the Workspace**
2. **Install Dependencies**
   Ensure Python 3.14 or 3.x is installed. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: `google-genai` is the official modern Gemini API client. `opencv-python-headless` is used for screen recording.)*

3. **Install LibreOffice (required for PPTX rendering)**
   Slides are rendered with 100% fidelity via LibreOffice headless:
   - Windows: https://www.libreoffice.org/download/download/
   - macOS:   `brew install --cask libreoffice`
   - Linux:   `sudo apt install libreoffice-impress`

4. **Run the Application**
   ```bash
   python main.py
   ```

---

## Building a Distribution Installer

Produces a size-optimized bundle (unused Qt modules and non-English locale
data excluded) plus an LZMA2-compressed setup executable:

```powershell
# Bundle only:
.\build.ps1

# Bundle + Inno Setup installer (requires Inno Setup 6):
.\build.ps1 -Installer
```

Outputs:
- `dist\UniBoard\` — portable application folder
- `installer_output\UniBoard_Setup.exe` — single-file installer

---

## Engine Details

### 1. Real-time Handwriting Recognition
UniBoard uses stroke coordinate analysis. As you draw, mouse trackpoints `[[x1, y1, t1], [x2, y2, t2], ...]` are captured.
- When drawing finishes (inactivity window of ~800ms), these coordinates are packed and analyzed.
- The app offers two recognition backend engines:
  1. **Google Input Tools IME (Default)**: Free, ultra-fast API that decodes stroke gestures with zero configuration.
  2. **Gemini Vision OCR**: Takes a bounding-box crop of the drawn stroke area and runs visual analysis for complex cursive text or math.

### 2. Isolated Code Execution Runtime
To compile and execute Python/JS safely:
- Runs code using an isolated subprocess (`subprocess.Popen`) with strict parameters:
  - Execution timeout (default 5 seconds to prevent infinite loops).
  - Empty/restricted environment variable mappings.
  - Execution takes place in a dedicated `sandbox/` directory inside the project directory.

### 3. Dynamic Theme System
Custom Stylesheets (QSS) implement the visual layers:
- **Dark Glassmorphic**: semi-transparent floating panels with backdrop filters, glowing borders (`rgba(255, 255, 255, 0.08)`), and neon highlights.
- **Light Glassmorphic**: sleek frost-white panels.
- **Slate**: dark, minimal, solid-color theme.
