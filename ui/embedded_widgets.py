from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QPlainTextEdit, QTextEdit, QLineEdit, QSplitter, QLabel, QFrame,
    QCheckBox, QStackedWidget
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, Signal, QUrl, QObject, Slot, Property, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from core.compiler import CodeCompiler
from ui.ppt_canvas import PptCanvasView

from PySide6.QtCore import QThread

import json


# ---------------------------------------------------------------------------
# Shared stylesheet fragments
# ---------------------------------------------------------------------------

# Theme-aware background gradients
_THEME_BG = {
    "Dark Glass": (
        "background: qlineargradient("
        "  x1:0, y1:0, x2:1, y2:1,"
        "  stop:0 rgba(18, 18, 30, 230),"
        "  stop:1 rgba(30, 30, 50, 210)"
        ");"
    ),
    "Light Glass": (
        "background: qlineargradient("
        "  x1:0, y1:0, x2:1, y2:1,"
        "  stop:0 rgba(255, 255, 255, 0.98),"
        "  stop:1 rgba(245, 245, 250, 0.96)"
        ");"
    ),
    "Slate": (
        "background: #1e293b;"
    ),
}

# Default to Dark Glass for backward compatibility
_DARK_GLASS_BG = _THEME_BG["Dark Glass"]


def _get_theme_bg(theme_name: str) -> str:
    """Return the background gradient for the given theme."""
    return _THEME_BG.get(theme_name, _DARK_GLASS_BG)


def _get_theme_editor_style(theme_name: str) -> str:
    """Return editor style matching the theme."""
    if theme_name == "Light Glass":
        return """
            QPlainTextEdit {
                background: rgba(255, 255, 255, 0.95);
                color: #2a2a3a;
                border: 1px solid rgba(0, 0, 0, 0.10);
                border-radius: 8px;
                padding: 10px;
                selection-background-color: rgba(0, 102, 255, 0.25);
                selection-color: #002266;
                font-size: 13px;
            }
            QPlainTextEdit:focus {
                border: 1px solid rgba(0, 102, 255, 0.45);
            }
        """
    elif theme_name == "Slate":
        return """
            QPlainTextEdit {
                background: #1e293b;
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                padding: 10px;
                selection-background-color: rgba(59, 130, 246, 0.40);
                selection-color: #ffffff;
                font-size: 13px;
            }
            QPlainTextEdit:focus {
                border: 1px solid rgba(59, 130, 246, 0.55);
            }
        """
    else:  # Dark Glass
        return """
            QPlainTextEdit {
                background: rgba(10, 10, 18, 0.92);
                color: #e2e8f0;
                border: 1px solid rgba(99, 102, 241, 0.25);
                border-radius: 8px;
                padding: 10px;
                selection-background-color: rgba(99, 102, 241, 0.4);
                selection-color: #ffffff;
                font-size: 13px;
            }
            QPlainTextEdit:focus {
                border: 1px solid rgba(99, 102, 241, 0.55);
            }
        """

_BUTTON_BASE = """
    QPushButton {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {start}, stop:1 {end}
        );
        color: {fg};
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 7px 18px;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {hover_start}, stop:1 {hover_end}
        );
        border: 1px solid rgba(255, 255, 255, 0.18);
    }}
    QPushButton:pressed {{
        background: {pressed};
        border: 1px solid rgba(255, 255, 255, 0.25);
    }}
"""

_ACCENT_BTN = _BUTTON_BASE.format(
    start="rgba(99, 102, 241, 0.85)",
    end="rgba(79, 70, 229, 0.90)",
    fg="#f0f0ff",
    hover_start="rgba(119, 122, 255, 0.95)",
    hover_end="rgba(99, 90, 249, 1.0)",
    pressed="rgba(67, 56, 202, 1.0)",
)

_GREEN_BTN = _BUTTON_BASE.format(
    start="rgba(16, 185, 129, 0.85)",
    end="rgba(5, 150, 105, 0.90)",
    fg="#ecfdf5",
    hover_start="rgba(36, 205, 149, 0.95)",
    hover_end="rgba(16, 170, 125, 1.0)",
    pressed="rgba(4, 120, 87, 1.0)",
)

_SUBTLE_BTN = _BUTTON_BASE.format(
    start="rgba(55, 55, 75, 0.7)",
    end="rgba(40, 40, 60, 0.8)",
    fg="#c4c4d8",
    hover_start="rgba(70, 70, 95, 0.85)",
    hover_end="rgba(55, 55, 75, 0.9)",
    pressed="rgba(35, 35, 55, 1.0)",
)

_EDITOR_STYLE = """
    QPlainTextEdit {
        background: rgba(10, 10, 18, 0.92);
        color: #e2e8f0;
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 8px;
        padding: 10px;
        selection-background-color: rgba(99, 102, 241, 0.4);
        selection-color: #ffffff;
        font-size: 13px;
    }
    QPlainTextEdit:focus {
        border: 1px solid rgba(99, 102, 241, 0.55);
    }
"""

_CONSOLE_STYLE = """
    QTextEdit {
        background: rgba(5, 5, 10, 0.95);
        color: #a3e635;
        border: 1px solid rgba(163, 230, 53, 0.15);
        border-radius: 8px;
        padding: 10px;
        font-size: 13px;
    }
"""

_COMBOBOX_STYLE = """
    QComboBox {
        background: rgba(30, 30, 50, 0.9);
        color: #e2e8f0;
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 500;
        min-width: 130px;
    }
    QComboBox:hover {
        border: 1px solid rgba(99, 102, 241, 0.55);
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border-left: 1px solid rgba(99, 102, 241, 0.2);
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }
    QComboBox::down-arrow {
        image: none;
        border: none;
    }
    QComboBox QAbstractItemView {
        background: rgba(20, 20, 38, 0.97);
        color: #e2e8f0;
        border: 1px solid rgba(99, 102, 241, 0.3);
        selection-background-color: rgba(99, 102, 241, 0.4);
        selection-color: #ffffff;
        border-radius: 6px;
        padding: 4px;
    }
"""

_LINE_EDIT_STYLE = """
    QLineEdit {
        background: rgba(10, 10, 18, 0.9);
        color: #e2e8f0;
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 8px;
        padding: 7px 14px;
        font-size: 13px;
        selection-background-color: rgba(99, 102, 241, 0.4);
    }
    QLineEdit:focus {
        border: 1px solid rgba(99, 102, 241, 0.6);
    }
"""

_SPLITTER_STYLE = """
    QSplitter::handle {
        background: rgba(99, 102, 241, 0.18);
        border-radius: 2px;
    }
    QSplitter::handle:horizontal { width: 3px; }
    QSplitter::handle:vertical   { height: 3px; }
    QSplitter::handle:hover {
        background: rgba(99, 102, 241, 0.45);
    }
"""


# ═══════════════════════════════════════════════════════════════════════════
#  1. HTMLRenderWidget
# ═══════════════════════════════════════════════════════════════════════════

class HTMLRenderWidget(QWidget):
    """Live HTML editor & renderer with a toggleable editor panel."""

    html_changed = Signal(str)

    def __init__(self, initial_html: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self._build_ui(initial_html)

    def set_theme(self, theme_name: str):
        """Update styles to match the selected theme."""
        bg = _get_theme_bg(theme_name)
        self._editor_panel.setStyleSheet(
            f"QFrame {{ {bg} border-left: 1px solid rgba(99,102,241,0.18); }}"
        )
        self._editor.setStyleSheet(_get_theme_editor_style(theme_name))

    # -- UI construction -----------------------------------------------------

    def _build_ui(self, initial_html: str) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Splitter: web view | editor panel
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.setStyleSheet(_SPLITTER_STYLE)
        self._splitter.setHandleWidth(3)

        # — Web view —
        self._web = QWebEngineView(self)
        self._web.setHtml(initial_html or _placeholder_html("HTML Renderer"))
        self._splitter.addWidget(self._web)

        # — Editor panel —
        self._editor_panel = QFrame(self)
        self._editor_panel.setStyleSheet(
            f"QFrame {{ {_DARK_GLASS_BG} border-left: 1px solid rgba(99,102,241,0.18); }}"
        )
        ep_layout = QVBoxLayout(self._editor_panel)
        ep_layout.setContentsMargins(14, 14, 14, 14)
        ep_layout.setSpacing(10)

        # Header
        header = QLabel("✦ HTML Editor")
        header.setStyleSheet(
            "color: #c7d2fe; font-size: 15px; font-weight: 700; padding: 2px 0;"
        )
        ep_layout.addWidget(header)

        # Code editor
        self._editor = QPlainTextEdit()
        self._editor.setFont(QFont("Consolas", 12))
        self._editor.setStyleSheet(_EDITOR_STYLE)
        self._editor.setPlainText(initial_html)
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        ep_layout.addWidget(self._editor, 1)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._render_btn = QPushButton("▶  Render HTML")
        self._render_btn.setStyleSheet(_ACCENT_BTN)
        self._render_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._render_btn.clicked.connect(self.apply_html)
        btn_row.addWidget(self._render_btn)

        self._hide_btn = QPushButton("✕  Hide Editor")
        self._hide_btn.setStyleSheet(_SUBTLE_BTN)
        self._hide_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hide_btn.clicked.connect(self.toggle_editor)
        btn_row.addWidget(self._hide_btn)

        btn_row.addStretch()
        ep_layout.addLayout(btn_row)

        self._splitter.addWidget(self._editor_panel)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 2)

        root.addWidget(self._splitter)

        # — Floating edit toggle button (overlaid on web view) —
        self._toggle_btn = QPushButton("✏️ Edit HTML", self)
        self._toggle_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(99, 102, 241, 0.82);
                color: #f0f0ff;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
                padding: 8px 18px;
                font-weight: 700;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(119, 122, 255, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.25);
            }
            """
        )
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self.toggle_editor)
        self._toggle_btn.raise_()

        # Editor hidden by default (presentation mode)
        self._editor_panel.setVisible(False)

    # -- Geometry helpers ----------------------------------------------------

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reposition_toggle_btn()

    def _reposition_toggle_btn(self) -> None:
        btn = self._toggle_btn
        margin = 16
        btn.adjustSize()
        btn.move(self.width() - btn.width() - margin, margin)

    # -- Public API ----------------------------------------------------------

    def toggle_editor(self) -> None:
        visible = self._editor_panel.isVisible()
        self._editor_panel.setVisible(not visible)
        self._toggle_btn.setText("✏️ Edit HTML" if visible else "✏️ Hide Editor")

    def apply_html(self) -> None:
        html = self._editor.toPlainText()
        self._web.setHtml(html)
        self.html_changed.emit(html)

    def set_html(self, html_code: str) -> None:
        self._editor.setPlainText(html_code)
        self._web.setHtml(html_code)


# ═══════════════════════════════════════════════════════════════════════════
#  2. CompilerWidget  (+ module-level thread)
# ═══════════════════════════════════════════════════════════════════════════

class CompilerRunThread(QThread):
    """Background thread for code execution — defined at module level so
    PySide6 can register the Signal correctly."""

    finished = Signal(str, str, int)

    def __init__(self, code: str, lang: str, parent=None):
        super().__init__(parent)
        self.code = code
        self.lang = lang

    def run(self) -> None:
        stdout, stderr, returncode = CodeCompiler.run_code(self.code, self.lang)
        self.finished.emit(stdout, stderr, returncode)


class CompilerWidget(QWidget):
    """Code editor + console output with background compilation."""

    code_changed = Signal(str, str)  # (code, language)

    def __init__(
        self,
        initial_code: str = "",
        initial_lang: str = "Python",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._thread: CompilerRunThread | None = None
        self._build_ui(initial_code, initial_lang)

    def set_theme(self, theme_name: str):
        """Update styles to match the selected theme."""
        bg = _get_theme_bg(theme_name)
        self._splitter.setStyleSheet(_SPLITTER_STYLE)
        self._editor.setStyleSheet(_get_theme_editor_style(theme_name))
        self._console.setStyleSheet(_CONSOLE_STYLE)

    # -- UI construction -----------------------------------------------------

    def _build_ui(self, initial_code: str, initial_lang: str) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # — Toolbar —
        toolbar = QFrame(self)
        toolbar.setStyleSheet(
            f"QFrame {{ {_DARK_GLASS_BG} border-bottom: 1px solid rgba(99,102,241,0.15); }}"
        )
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(14, 10, 14, 10)
        tb_layout.setSpacing(10)

        # Language selector
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(["Python", "JavaScript"])
        self._lang_combo.setCurrentText(initial_lang)
        self._lang_combo.setStyleSheet(_COMBOBOX_STYLE)
        self._lang_combo.currentTextChanged.connect(self._on_lang_changed)
        tb_layout.addWidget(self._lang_combo)

        tb_layout.addStretch()

        # Run button
        self._run_btn = QPushButton("⚡  Run Code")
        self._run_btn.setStyleSheet(_GREEN_BTN)
        self._run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._run_btn.clicked.connect(self.run_code)
        tb_layout.addWidget(self._run_btn)

        root.addWidget(toolbar)

        # — Splitter: editor | console —
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.setStyleSheet(_SPLITTER_STYLE)
        self._splitter.setHandleWidth(3)

        # Code editor
        self._editor = QPlainTextEdit()
        self._editor.setFont(QFont("Consolas", 12))
        self._editor.setStyleSheet(_EDITOR_STYLE)
        self._editor.setPlainText(initial_code)
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._editor.setTabStopDistance(32.0)
        self._editor.textChanged.connect(self._emit_code_changed)
        self._splitter.addWidget(self._editor)

        # Console output
        self._console = QTextEdit()
        self._console.setReadOnly(True)
        self._console.setFont(QFont("Consolas", 12))
        self._console.setStyleSheet(_CONSOLE_STYLE)
        self._console.setPlaceholderText("Console output will appear here…")
        self._splitter.addWidget(self._console)

        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 2)
        root.addWidget(self._splitter, 1)

    # -- Slots ---------------------------------------------------------------

    def _on_lang_changed(self, lang: str) -> None:
        self._emit_code_changed()

    def _emit_code_changed(self) -> None:
        self.code_changed.emit(
            self._editor.toPlainText(),
            self._lang_combo.currentText(),
        )

    def run_code(self) -> None:
        code = self._editor.toPlainText()
        lang = self._lang_combo.currentText()

        self._console.clear()
        self._console.setTextColor(QColor("#94a3b8"))
        self._console.append(f"⏳ Running {lang}…\n")
        self._run_btn.setEnabled(False)

        self._thread = CompilerRunThread(code, lang, self)
        self._thread.finished.connect(self._on_run_finished)
        self._thread.start()

    def _on_run_finished(self, stdout: str, stderr: str, returncode: int) -> None:
        self._console.clear()

        if stdout:
            self._console.setTextColor(QColor("#4ade80"))  # green
            self._console.append(stdout)

        if stderr:
            self._console.setTextColor(QColor("#f87171"))  # red
            self._console.append(stderr)

        # Status footer
        if returncode == 0:
            self._console.setTextColor(QColor("#4ade80"))
            self._console.append("\n✔ Process exited with code 0")
        else:
            self._console.setTextColor(QColor("#f87171"))
            self._console.append(f"\n✘ Process exited with code {returncode}")

        self._run_btn.setEnabled(True)
        self._thread = None

    # -- Public API ----------------------------------------------------------

    def set_content(self, code: str, lang: str) -> None:
        self._editor.setPlainText(code)
        idx = self._lang_combo.findText(lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)

    # -- Drawing-tool compatibility properties (no-ops) -----------------------
    # The compiler is a code editor; it doesn't use drawing tools.
    # These properties exist so the main toolbar can call them without crashing.

    @property
    def pen_color(self):
        return QColor("#00ffcc")

    @pen_color.setter
    def pen_color(self, value):
        pass

    @property
    def pen_width(self):
        return 3

    @pen_width.setter
    def pen_width(self, value):
        pass

    @property
    def text_size(self):
        return 16

    @text_size.setter
    def text_size(self, value):
        pass

    @property
    def highlighter_color(self):
        return QColor(255, 255, 0, 100)

    @highlighter_color.setter
    def highlighter_color(self, value):
        pass

    @property
    def highlighter_width(self):
        return 15

    @highlighter_width.setter
    def highlighter_width(self, value):
        pass

    @property
    def eraser_width(self):
        return 24

    @eraser_width.setter
    def eraser_width(self, value):
        pass

    def set_tool(self, tool_mode):
        pass

    def undo(self):
        pass

    def redo(self):
        pass


# ═══════════════════════════════════════════════════════════════════════════
#  3. HtmlCanvasWidget  (HTML5 <canvas>-based drawing tool, Browser pattern)
# ═══════════════════════════════════════════════════════════════════════════

# Self-contained HTML5 page that renders an interactive <canvas> surface.
# It exposes a small JS API (setTool, setColor, setWidth, clearCanvas,
# loadCanvas, getCanvasDataURL) and talks back to Python through a
# QWebChannel bridge named "bridge".
_HTML5_CANVAS_PAGE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>HTML5 Canvas</title>
<style>
  html, body {
    margin: 0; padding: 0; height: 100%; width: 100%;
    background: #0d0d11; overflow: hidden;
    font-family: 'Segoe UI', system-ui, sans-serif;
  }
  #canvas {
    display: block; cursor: crosshair;
    background: #0d0d11;
    touch-action: none;
  }
  #statusBar {
    position: fixed; left: 12px; bottom: 10px;
    color: #6366f1; font-size: 12px; font-weight: 500;
    background: rgba(20, 20, 38, 0.65);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 6px;
    padding: 4px 10px;
    pointer-events: none;
    user-select: none;
  }
</style>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
</head>
<body>
<canvas id="canvas"></canvas>
<div id="statusBar">HTML5 Canvas — ready</div>
<script>
(function () {
  'use strict';

  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');
  const statusBar = document.getElementById('statusBar');

  // Persistent state for the canvas
  let tool = 'pen';
  let color = '#00ffcc';
  let width = 3;
  let isDrawing = false;
  let lastX = 0, lastY = 0;
  let bridge = null;
  let suppressSave = false;  // when true, don't push a snapshot (e.g. during load)

  function setStatus(text) { if (statusBar) statusBar.textContent = text; }

  function resizeCanvas() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    if (canvas.width === w && canvas.height === h) return;
    // Preserve the current drawing across resizes.
    const snapshot = canvas.toDataURL();
    canvas.width = w;
    canvas.height = h;
    if (snapshot && snapshot.length > 100) {
      const img = new Image();
      img.onload = function () { ctx.drawImage(img, 0, 0); };
      img.src = snapshot;
    }
  }

  function getPos(e) {
    const r = canvas.getBoundingClientRect();
    const t = (e.touches && e.touches.length) ? e.touches[0] : e;
    return [t.clientX - r.left, t.clientY - r.top];
  }

  function strokeSettings() {
    if (tool === 'eraser') {
      return {
        style: '#0d0d11',
        lineWidth: Math.max(width * 4, 12)
      };
    }
    if (tool === 'highlighter') {
      // Parse hex (#rrggbb) into rgba with low alpha
      let c = color;
      if (c.startsWith('#') && c.length === 7) {
        const r = parseInt(c.substr(1, 2), 16);
        const g = parseInt(c.substr(3, 2), 16);
        const b = parseInt(c.substr(5, 2), 16);
        c = 'rgba(' + r + ',' + g + ',' + b + ',0.35)';
      }
      return { style: c, lineWidth: Math.max(width * 4, 12) };
    }
    return { style: color, lineWidth: width };
  }

  function startDraw(e) {
    e.preventDefault();
    isDrawing = true;
    const p = getPos(e);
    lastX = p[0]; lastY = p[1];
  }

  function continueDraw(e) {
    if (!isDrawing) return;
    e.preventDefault();
    const p = getPos(e);
    const s = strokeSettings();
    ctx.save();
    ctx.strokeStyle = s.style;
    ctx.lineWidth = s.lineWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(p[0], p[1]);
    ctx.stroke();
    ctx.restore();
    lastX = p[0]; lastY = p[1];
  }

  function endDraw() {
    if (!isDrawing) return;
    isDrawing = false;
    if (bridge && !suppressSave) {
      try { bridge.saveCanvas(canvas.toDataURL()); } catch (e) {}
    }
  }

  // ---- Public API (called from Python via runJavaScript) ------------------

  window.setTool = function (t) {
    tool = String(t || 'pen');
    setStatus('Tool: ' + tool);
  };
  window.setColor = function (c) {
    color = String(c || '#00ffcc');
    setStatus('Color: ' + color);
  };
  window.setWidth = function (w) {
    width = Math.max(1, parseInt(w, 10) || 3);
    setStatus('Width: ' + width);
  };
  window.clearCanvas = function () {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (bridge) {
      try { bridge.saveCanvas(canvas.toDataURL()); } catch (e) {}
    }
  };
  window.loadCanvas = function (dataUrl) {
    if (!dataUrl) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }
    const img = new Image();
    img.onload = function () {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
    };
    img.onerror = function () {
      // Bad data URL — silently ignore.
    };
    img.src = dataUrl;
  };
  window.getCanvasDataURL = function () {
    return canvas.toDataURL();
  };
  window.applySnapshot = function (dataUrl) {
    // Used by the "Go" / Save button — keeps the canvas as-is and just
    // pushes a new history entry for the current state.
    if (bridge) {
      try { bridge.saveCanvas(dataUrl || canvas.toDataURL()); } catch (e) {}
    }
  };

  // ---- Event wiring -------------------------------------------------------

  canvas.addEventListener('mousedown', startDraw);
  canvas.addEventListener('mousemove', continueDraw);
  canvas.addEventListener('mouseup', endDraw);
  canvas.addEventListener('mouseleave', endDraw);
  canvas.addEventListener('touchstart', startDraw, { passive: false });
  canvas.addEventListener('touchmove', continueDraw, { passive: false });
  canvas.addEventListener('touchend', endDraw);
  window.addEventListener('resize', resizeCanvas);

  // ---- QWebChannel bootstrap ---------------------------------------------
  if (typeof QWebChannel !== 'undefined') {
    new QWebChannel(qt.webChannelTransport, function (channel) {
      bridge = channel.objects.bridge;
      // Tell Python we're ready (it will push initial state if any).
      if (bridge && bridge.notifyReady) {
        try { bridge.notifyReady(); } catch (e) {}
      }
    });
  } else {
    setStatus('QWebChannel not available');
  }

  resizeCanvas();
})();
</script>
</body>
</html>
"""


class HtmlCanvasBridge(QObject):
    """Bridge object exposed to the HTML5 <canvas> JavaScript via QWebChannel.

    Python → JS is done with ``runJavaScript()``; JS → Python is done through
    the ``@Slot`` methods on this object. We also expose a couple of
    properties (color, width, tool) so the JS side can read them if needed.
    """

    # JS → Python signals
    canvas_saved = Signal(str)         # data URL of the canvas state
    ready = Signal()                   # JS side finished bootstrapping

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._color = "#00ffcc"
        self._width = 3
        self._tool = "pen"

    # -- Properties (read-only from JS side) --------------------------------

    @Property(str)
    def color(self) -> str:
        return self._color

    @Property(int)
    def width(self) -> int:
        return self._width

    @Property(str)
    def tool(self) -> str:
        return self._tool

    # -- Slots (JS → Python) ------------------------------------------------

    @Slot(str)
    def saveCanvas(self, data_url: str) -> None:
        self.canvas_saved.emit(data_url)

    @Slot()
    def notifyReady(self) -> None:
        self.ready.emit()


class Html5CanvasWidget(QWidget):
    """Browser-pattern widget whose main content is an HTML5 <canvas>.

    Header layout mirrors the old BrowserWidget:
        [ ⬅ Undo ] [ ➡ Redo ] [ 🔄 Clear ]   [   canvas title …   ] [ Save ]

    The "URL bar" doubles as a canvas title (purely metadata, free-form text).
    The main area is a ``QWebEngineView`` hosting an HTML5 page that draws
    onto a real ``<canvas>`` element with the pen / eraser / highlighter
    tools. State is synced to the page through ``runJavaScript`` and
    received back as a data URL via the ``HtmlCanvasBridge``.
    """

    canvas_changed = Signal(str)   # data URL of the latest canvas state
    title_changed = Signal(str)    # canvas title (the "URL bar" text)

    _MAX_HISTORY = 30              # undo / redo depth cap

    def __init__(
        self,
        initial_state: str = "",
        initial_title: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bridge = HtmlCanvasBridge(self)
        self._undo_stack: list[str] = []
        self._redo_stack: list[str] = []
        self._current_state: str = initial_state or ""
        self._title: str = initial_title or ""
        self._js_ready: bool = False
        self._pending_state: str = initial_state or ""
        self._suppress_history: bool = False

        self._build_ui()

        # Bridge wiring
        self._bridge.canvas_saved.connect(self._on_canvas_saved)
        self._bridge.ready.connect(self._on_js_ready)
        self._channel = QWebChannel(self)
        self._channel.registerObject("bridge", self._bridge)
        self._web.page().setWebChannel(self._channel)
        self._web.loadFinished.connect(self._on_load_finished)

        # Load the HTML5 canvas page (qrc:/ lets us resolve the
        # qwebchannel.js script shipped with Qt).
        self._web.setHtml(_HTML5_CANVAS_PAGE, QUrl("qrc:///"))

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # — Navigation bar (mirrors old BrowserWidget chrome) —
        nav = QFrame(self)
        nav.setStyleSheet(
            f"QFrame {{ {_DARK_GLASS_BG} border-bottom: 1px solid rgba(99,102,241,0.15); }}"
        )
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(10, 8, 10, 8)
        nav_layout.setSpacing(6)

        nav_btn_style = """
            QPushButton {
                background: rgba(40, 40, 60, 0.8);
                color: #c4c4d8;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 8px;
                font-size: 15px;
                min-width: 38px;
                max-width: 38px;
                min-height: 34px;
                max-height: 34px;
            }
            QPushButton:hover {
                background: rgba(60, 60, 85, 0.9);
                color: #e2e8f0;
                border: 1px solid rgba(99, 102, 241, 0.35);
            }
            QPushButton:pressed {
                background: rgba(30, 30, 50, 1.0);
            }
        """

        self._back_btn = QPushButton("⬅")
        self._back_btn.setStyleSheet(nav_btn_style)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setToolTip("Undo last stroke")
        self._back_btn.clicked.connect(self._undo)
        nav_layout.addWidget(self._back_btn)

        self._fwd_btn = QPushButton("➡")
        self._fwd_btn.setStyleSheet(nav_btn_style)
        self._fwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fwd_btn.setToolTip("Redo stroke")
        self._fwd_btn.clicked.connect(self._redo)
        nav_layout.addWidget(self._fwd_btn)

        self._reload_btn = QPushButton("🧹")
        self._reload_btn.setStyleSheet(nav_btn_style)
        self._reload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reload_btn.setToolTip("Clear canvas")
        self._reload_btn.clicked.connect(self._clear)
        nav_layout.addWidget(self._reload_btn)

        # "URL" bar — repurposed as a canvas title input
        self._url_bar = QLineEdit()
        self._url_bar.setStyleSheet(_LINE_EDIT_STYLE)
        self._url_bar.setPlaceholderText("Canvas title…")
        self._url_bar.setText(self._title)
        self._url_bar.returnPressed.connect(self._on_title_entered)
        nav_layout.addWidget(self._url_bar, 1)

        # "Go" → Save snapshot
        self._go_btn = QPushButton("Save")
        self._go_btn.setStyleSheet(_ACCENT_BTN)
        self._go_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._go_btn.setToolTip("Save current canvas snapshot")
        self._go_btn.clicked.connect(self._save_snapshot)
        nav_layout.addWidget(self._go_btn)

        root.addWidget(nav)

        # — HTML5 <canvas> surface —
        self._web = QWebEngineView(self)
        root.addWidget(self._web, 1)

    # ------------------------------------------------------------------
    # Theme hook (kept for API parity with the other embedded widgets)
    # ------------------------------------------------------------------
    def set_theme(self, theme_name: str) -> None:
        """Theme changes are picked up automatically via the QSS; this hook
        exists so the main window can call it without checking capability.
        """
        return

    # ------------------------------------------------------------------
    # JS bridge helpers
    # ------------------------------------------------------------------
    def _run_js(self, code: str) -> None:
        if self._web and self._web.page():
            self._web.page().runJavaScript(code)

    def _sync_tool_state(self) -> None:
        """Push the current tool / color / width from Python to JS."""
        self._run_js(f"setTool({json.dumps(self._bridge._tool)});")
        self._run_js(f"setColor({json.dumps(self._bridge._color)});")
        self._run_js(f"setWidth({int(self._bridge._width)});")

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            return
        # The page itself wires up QWebChannel; we just wait for the
        # ``ready`` signal before pushing initial state.

    def _on_js_ready(self) -> None:
        self._js_ready = True
        self._sync_tool_state()
        if self._pending_state:
            self._suppress_history = True
            try:
                self._run_js(f"loadCanvas({json.dumps(self._pending_state)});")
            finally:
                self._suppress_history = False
            # Seed the history with the loaded state so undo/redo has a
            # sensible starting point.
            self._undo_stack.append(self._pending_state)
            self._current_state = self._pending_state
            self._pending_state = ""

    # ------------------------------------------------------------------
    # Slots: stroke → history
    # ------------------------------------------------------------------
    def _on_canvas_saved(self, data_url: str) -> None:
        if self._suppress_history:
            return
        # Avoid duplicate consecutive entries (e.g. when reloading a
        # snapshot that matches the current state).
        if self._undo_stack and self._undo_stack[-1] == data_url:
            self._current_state = data_url
            return
        self._undo_stack.append(data_url)
        if len(self._undo_stack) > self._MAX_HISTORY:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._current_state = data_url
        self.canvas_changed.emit(data_url)

    # ------------------------------------------------------------------
    # Nav-bar actions
    # ------------------------------------------------------------------
    def _undo(self) -> None:
        if len(self._undo_stack) <= 1:
            return
        self._redo_stack.append(self._undo_stack.pop())
        state = self._undo_stack[-1]
        self._current_state = state
        self._suppress_history = True
        try:
            self._run_js(f"loadCanvas({json.dumps(state)});")
        finally:
            self._suppress_history = False
        self.canvas_changed.emit(state)

    def _redo(self) -> None:
        if not self._redo_stack:
            return
        state = self._redo_stack.pop()
        self._undo_stack.append(state)
        self._current_state = state
        self._suppress_history = True
        try:
            self._run_js(f"loadCanvas({json.dumps(state)});")
        finally:
            self._suppress_history = False
        self.canvas_changed.emit(state)

    def _clear(self) -> None:
        self._suppress_history = True
        try:
            self._run_js("clearCanvas();")
        finally:
            self._suppress_history = False
        # The JS side will emit a saveCanvas with the empty data URL
        # which we want to record as a normal history step.

    def _save_snapshot(self) -> None:
        """Push a new history entry from the current canvas state and
        give the user a quick visual confirmation.
        """
        self._run_js("applySnapshot('');")
        # Briefly flash the button text as confirmation.
        original = self._go_btn.text()
        self._go_btn.setText("✓")
        QTimer.singleShot(
            800,
            lambda: self._go_btn.setText(original) if self._go_btn else None,
        )

    def _on_title_entered(self) -> None:
        self._title = self._url_bar.text().strip()
        self.title_changed.emit(self._title)

    # ------------------------------------------------------------------
    # Public API used by the main toolbar
    # ------------------------------------------------------------------
    # Integer tool-mode mapping (from `config`) → JS tool name.
    _INT_TO_TOOL = {
        0: "select",        # MODE_SELECT (no-op for the canvas)
        1: "pen",           # MODE_PEN
        2: "highlighter",   # MODE_HIGHLIGHTER
        3: "eraser",        # MODE_ERASER
        4: "text",          # MODE_TEXT (no-op for the canvas)
        5: "line",          # MODE_LINE (no-op)
        6: "rect",          # MODE_RECT (no-op)
        7: "circle",        # MODE_CIRCLE (no-op)
    }

    def set_tool(self, tool) -> None:
        """Switch the active drawing tool. Accepts either the integer
        ``MODE_*`` constants from ``config`` or a JS tool name
        (``'pen' | 'eraser' | 'highlighter' | 'select' | 'text'``).
        """
        if isinstance(tool, int):
            tool = self._INT_TO_TOOL.get(tool, "pen")
        if tool in ("select", "text", "line", "rect", "circle"):
            # The HTML5 canvas only meaningfully supports pen/eraser/highlighter.
            # Treat the rest as no-ops so the toolbar doesn't crash.
            self._bridge._tool = "pen"
            self._run_js(f"setTool({json.dumps('pen')});")
            return
        tool = str(tool or "pen")
        self._bridge._tool = tool
        self._run_js(f"setTool({json.dumps(tool)});")

    def set_color(self, color) -> None:
        # Accept QColor too — the main toolbar sometimes passes one.
        c = color.name() if hasattr(color, "name") else str(color)
        self._bridge._color = c
        self._run_js(f"setColor({json.dumps(c)});")

    def set_width(self, width: int) -> None:
        width = max(1, int(width))
        self._bridge._width = width
        self._run_js(f"setWidth({width});")

    # ------------------------------------------------------------------
    # Attribute-style API for compatibility with the main toolbar
    # (which uses ``target.pen_color = color`` etc. via _get_active_target).
    # ------------------------------------------------------------------
    @property
    def pen_color(self):
        from PySide6.QtGui import QColor
        return QColor(self._bridge._color)

    @pen_color.setter
    def pen_color(self, value):
        self.set_color(value)

    @property
    def pen_width(self) -> int:
        return self._bridge._width

    @pen_width.setter
    def pen_width(self, value: int):
        self.set_width(value)

    # Attributes the main toolbar touches for the plain canvas — keep them
    # as harmless no-ops so ``target.text_size = ...`` etc. don't crash.
    @property
    def text_size(self) -> int:
        return 16

    @text_size.setter
    def text_size(self, value: int) -> None:
        # Not applicable to the HTML5 canvas — silently accept.
        return

    @property
    def highlighter_color(self):
        from PySide6.QtGui import QColor
        return QColor(self._bridge._color)

    @highlighter_color.setter
    def highlighter_color(self, value) -> None:
        return

    @property
    def highlighter_width(self) -> int:
        return self._bridge._width

    @highlighter_width.setter
    def highlighter_width(self, value: int) -> None:
        return

    @property
    def eraser_width(self) -> int:
        return self._bridge._width

    @eraser_width.setter
    def eraser_width(self, value: int) -> None:
        return

    def undo(self) -> None:
        self._undo()

    def redo(self) -> None:
        self._redo()

    def get_state(self) -> str:
        """Return the latest canvas state (data URL)."""
        return self._current_state

    def set_state(self, data_url: str) -> None:
        """Replace the canvas with a previously saved state."""
        if not data_url:
            return
        self._current_state = data_url
        if not self._js_ready:
            # Page not bootstrapped yet — defer until ready.
            self._pending_state = data_url
            return
        self._suppress_history = True
        try:
            self._run_js(f"loadCanvas({json.dumps(data_url)});")
        finally:
            self._suppress_history = False
        # Reset history around the freshly loaded state.
        self._undo_stack = [data_url]
        self._redo_stack.clear()

    def get_title(self) -> str:
        return self._title

    def set_title(self, title: str) -> None:
        self._title = title or ""
        if self._url_bar:
            self._url_bar.setText(self._title)


# ═══════════════════════════════════════════════════════════════════════════
#  4. HtmlCanvasWidget  (HTML with annotation overlay)
# ═══════════════════════════════════════════════════════════════════════════

class HtmlCanvasWidget(QWidget):
    """HTML renderer with a transparent annotation overlay and persistent toggle."""

    html_changed = Signal(str)

    def __init__(self, initial_html: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.persistent = False
        self._build_ui(initial_html)

    def set_theme(self, theme_name: str):
        """Update styles to match the selected theme."""
        bg = _get_theme_bg(theme_name)
        # The toolbar style is set via f-string with _DARK_GLASS_BG in _build_ui
        # We need to update it here
        # The toolbar is the first QFrame child
        for child in self.findChildren(QFrame):
            obj_name = child.objectName()
            if obj_name == "htmlAnnotToolbar":
                child.setStyleSheet(
                    f"QFrame {{ {bg} border-bottom: 1px solid rgba(99,102,241,0.15); }}"
                )
            elif child.parent() is self and child != self._content_frame:
                # Editor panel
                child.setStyleSheet(
                    f"QFrame {{ {bg} border-top: 1px solid rgba(99,102,241,0.18); }}"
                )
        self._editor.setStyleSheet(_get_theme_editor_style(theme_name))

    def _build_ui(self, initial_html: str) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar with persistent checkbox
        toolbar = QFrame(self)
        toolbar.setObjectName("htmlAnnotToolbar")
        toolbar.setStyleSheet(
            f"QFrame {{ {_DARK_GLASS_BG} border-bottom: 1px solid rgba(99,102,241,0.15); }}"
        )
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(14, 8, 14, 8)
        tb_layout.setSpacing(10)

        self._persist_cb = QCheckBox("Persistent Annotations")
        self._persist_cb.setStyleSheet("""
            QCheckBox {
                color: #c4c4d8;
                font-size: 13px;
                font-weight: 500;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border: 2px solid rgba(99, 102, 241, 0.5);
                border-radius: 3px;
                background: rgba(10, 10, 18, 0.6);
            }
            QCheckBox::indicator:checked {
                background: rgba(99, 102, 241, 0.8);
                border: 2px solid rgba(99, 102, 241, 0.9);
            }
            QCheckBox::indicator:hover {
                border: 2px solid rgba(99, 102, 241, 0.8);
            }
        """)
        tb_layout.addWidget(self._persist_cb)

        tb_layout.addStretch()

        self._edit_toggle_btn = QPushButton("✏️ Edit HTML")
        self._edit_toggle_btn.setStyleSheet(_SUBTLE_BTN)
        self._edit_toggle_btn.setCursor(Qt.PointingHandCursor)
        self._edit_toggle_btn.clicked.connect(self._toggle_editor)
        tb_layout.addWidget(self._edit_toggle_btn)

        root.addWidget(toolbar)

        # Content area: web view with annotation overlay
        self._content_frame = QFrame(self)
        content_layout = QVBoxLayout(self._content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._web = QWebEngineView(self._content_frame)
        self._web.setHtml(initial_html or _placeholder_html("HTML Canvas"))
        content_layout.addWidget(self._web)

        # Annotation overlay on top of web view (child of content frame, positioned manually)
        self._annot_overlay = PptCanvasView(self._content_frame)
        self._annot_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._annot_overlay.setBackgroundBrush(QColor(0, 0, 0, 0))
        self._annot_overlay.setStyleSheet("background: transparent; border: none;")
        self._annot_overlay.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._annot_overlay.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._annot_overlay.setVisible(True)

        root.addWidget(self._content_frame, 1)

        # Editor panel (hidden by default)
        self._editor_panel = QFrame(self)
        self._editor_panel.setStyleSheet(
            f"QFrame {{ {_DARK_GLASS_BG} border-top: 1px solid rgba(99,102,241,0.18); }}"
        )
        ep_layout = QVBoxLayout(self._editor_panel)
        ep_layout.setContentsMargins(14, 14, 14, 14)
        ep_layout.setSpacing(10)

        header = QLabel("✦ HTML Editor")
        header.setStyleSheet("color: #c7d2fe; font-size: 15px; font-weight: 700; padding: 2px 0;")
        ep_layout.addWidget(header)

        self._editor = QPlainTextEdit()
        self._editor.setFont(QFont("Consolas", 12))
        self._editor.setStyleSheet(_EDITOR_STYLE)
        self._editor.setPlainText(initial_html)
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        ep_layout.addWidget(self._editor, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        render_btn = QPushButton("▶  Render HTML")
        render_btn.setStyleSheet(_ACCENT_BTN)
        render_btn.setCursor(Qt.PointingHandCursor)
        render_btn.clicked.connect(self._apply_html)
        btn_row.addWidget(render_btn)
        btn_row.addStretch()
        ep_layout.addLayout(btn_row)

        self._editor_panel.setVisible(False)
        root.addWidget(self._editor_panel)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_annot_overlay()

    def showEvent(self, event):
        super().showEvent(event)
        self._update_annot_overlay()

    def _update_annot_overlay(self):
        """Position the annotation overlay over the web view and set its
        scene rect so annotations are visible and at correct positions."""
        geom = self._web.geometry()
        self._annot_overlay.setGeometry(geom)
        w = geom.width()
        h = geom.height()
        if w > 0 and h > 0:
            scene = self._annot_overlay.scene()
            scene.setSceneRect(0, 0, w, h)
            self._annot_overlay.resetTransform()

    def _toggle_editor(self):
        visible = not self._editor_panel.isVisible()
        self._editor_panel.setVisible(visible)

    def _apply_html(self):
        html = self._editor.toPlainText()
        self._web.setHtml(html)
        self.html_changed.emit(html)

    def set_html(self, html_code: str) -> None:
        self._editor.setPlainText(html_code)
        if not self._persist_cb.isChecked():
            self._annot_overlay.clear_annotations()
        self._web.setHtml(html_code)

    def set_tool(self, tool_mode):
        is_drawing = tool_mode != 0  # MODE_SELECT = 0
        self._annot_overlay.set_tool(tool_mode)
        self._annot_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, not is_drawing)
        if is_drawing:
            self._annot_overlay.raise_()
            self._update_annot_overlay()
        else:
            self._annot_overlay.lower()

    @property
    def pen_color(self):
        return self._annot_overlay.pen_color

    @pen_color.setter
    def pen_color(self, color):
        self._annot_overlay.pen_color = color
        self._annot_overlay.highlighter_color = QColor(
            color.red(), color.green(), color.blue(), 100
        )

    @property
    def pen_width(self):
        return self._annot_overlay.pen_width

    @pen_width.setter
    def pen_width(self, width):
        self._annot_overlay.pen_width = width
        self._annot_overlay.highlighter_width = max(width * 4, 8)
        self._annot_overlay.eraser_width = max(width * 5, 10)

    @property
    def text_size(self):
        return self._annot_overlay.text_size

    @text_size.setter
    def text_size(self, size):
        self._annot_overlay.text_size = size

    @property
    def highlighter_color(self):
        return self._annot_overlay.highlighter_color

    @highlighter_color.setter
    def highlighter_color(self, color):
        self._annot_overlay.highlighter_color = color

    @property
    def highlighter_width(self):
        return self._annot_overlay.highlighter_width

    @highlighter_width.setter
    def highlighter_width(self, width):
        self._annot_overlay.highlighter_width = width

    @property
    def eraser_width(self):
        return self._annot_overlay.eraser_width

    @eraser_width.setter
    def eraser_width(self, width):
        self._annot_overlay.eraser_width = width

    def undo(self):
        self._annot_overlay.undo()

    def redo(self):
        self._annot_overlay.redo()

    def is_persistent(self):
        return self._persist_cb.isChecked()


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _placeholder_html(title: str) -> str:
    """Return a minimal dark placeholder page."""
    return f"""<!DOCTYPE html>
<html>
<head><style>
  body {{
    margin: 0; height: 100vh;
    display: flex; align-items: center; justify-content: center;
    background: #0f0f1a; color: #6366f1;
    font-family: 'Segoe UI', system-ui, sans-serif;
  }}
  h1 {{ font-weight: 300; font-size: 28px; opacity: .65; }}
</style></head>
<body><h1>{title}</h1></body>
</html>"""
