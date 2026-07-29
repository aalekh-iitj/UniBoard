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
    """Code editor + console output + annotation overlay.

    The code editor and console sit in a splitter. On top of the splitter
    is a transparent ``PptCanvasView`` annotation overlay so the educator
    can draw over their code and output with the main toolbar's pen /
    highlighter / eraser / shapes / text tools. The overlay is hidden from
    mouse events whenever the Select tool is active so the user can still
    type in the editor normally.
    """

    code_changed = Signal(str, str)  # (code, language)
    annotations_changed = Signal(list)   # list of QGraphicsItem objects

    def __init__(
        self,
        initial_code: str = "",
        initial_lang: str = "Python",
        saved_annotations: list | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._thread: CompilerRunThread | None = None
        self._build_ui(initial_code, initial_lang)
        # Restore any previously saved annotations.
        if saved_annotations:
            self._annot_overlay.load_annotation_items(saved_annotations)
        # Whenever the user draws on the overlay, hand the items up to the
        # main window so it can stash them in the page meta.
        self._annot_overlay.stroke_drawn.connect(self._on_annotations_changed)

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
        toolbar.setObjectName("compilerToolbar")
        toolbar.setStyleSheet(
            f"QFrame#compilerToolbar {{ {_DARK_GLASS_BG} "
            f"border-bottom: 1px solid rgba(99,102,241,0.15); }}"
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

        # Snapshot button (saves the current annotated view as PNG)
        self._snap_btn = QPushButton("📸")
        self._snap_btn.setStyleSheet(_SUBTLE_BTN)
        self._snap_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._snap_btn.setToolTip("Save annotated snapshot (PNG)")
        self._snap_btn.clicked.connect(self._save_snapshot)
        tb_layout.addWidget(self._snap_btn)

        # Clear annotations button
        self._clear_annot_btn = QPushButton("🧹")
        self._clear_annot_btn.setStyleSheet(_SUBTLE_BTN)
        self._clear_annot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_annot_btn.setToolTip("Clear annotations")
        self._clear_annot_btn.clicked.connect(self._clear_annotations)
        tb_layout.addWidget(self._clear_annot_btn)

        # Run button
        self._run_btn = QPushButton("⚡  Run Code")
        self._run_btn.setStyleSheet(_GREEN_BTN)
        self._run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._run_btn.clicked.connect(self.run_code)
        tb_layout.addWidget(self._run_btn)

        root.addWidget(toolbar)

        # — Content area: editor + console + annotation overlay —
        self._content_frame = QFrame(self)
        content_layout = QVBoxLayout(self._content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Splitter: editor | console
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self._content_frame)
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
        content_layout.addWidget(self._splitter, 1)

        # Annotation overlay on top of the editor + console
        self._annot_overlay = PptCanvasView(self._content_frame)
        self._annot_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._annot_overlay.setBackgroundBrush(QColor(0, 0, 0, 0))
        self._annot_overlay.setStyleSheet("background: transparent; border: none;")
        self._annot_overlay.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._annot_overlay.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._annot_overlay.setVisible(True)
        self._annot_overlay.lower()

        root.addWidget(self._content_frame, 1)

    # -- Layout / overlay geometry -------------------------------------------
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_annot_overlay()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._update_annot_overlay()

    def _update_annot_overlay(self) -> None:
        if not self._splitter or not self._annot_overlay:
            return
        geom = self._splitter.geometry()
        self._annot_overlay.setGeometry(geom)
        w, h = geom.width(), geom.height()
        if w > 0 and h > 0:
            scene = self._annot_overlay.scene()
            scene.setSceneRect(0, 0, w, h)
            self._annot_overlay.resetTransform()

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

    # -- Annotations ---------------------------------------------------------
    def _on_annotations_changed(self) -> None:
        try:
            items = self._annot_overlay.get_annotation_items()
            self.annotations_changed.emit(items)
        except Exception:
            pass

    def save_annotations(self) -> list:
        """Detach annotation items from the scene and return them so the
        caller can stash them in the page meta.  Call this *before* the
        widget is destroyed so the items survive.
        """
        items = self._annot_overlay.get_annotation_items()
        for item in items:
            self._annot_overlay.scene().removeItem(item)
        return items

    def load_annotations(self, items: list) -> None:
        if not items:
            return
        self._annot_overlay.load_annotation_items(items)

    def _clear_annotations(self) -> None:
        self._annot_overlay.clear_annotations()
        self._on_annotations_changed()

    def _save_snapshot(self) -> None:
        """Grab a PNG of the editor + console + annotation overlay and save it."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from PySide6.QtCore import QStandardPaths
        from PySide6.QtGui import QPainter
        import os

        try:
            overlay_pix = self._annot_overlay.grab()
            content_pix = self._splitter.grab()
            combined = QPixmap(content_pix.size())
            combined.fill(QColor(0, 0, 0, 0))
            p = QPainter(combined)
            p.drawPixmap(0, 0, content_pix)
            p.drawPixmap(0, 0, overlay_pix)
            p.end()

            default_dir = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DocumentsLocation
            ) or os.path.expanduser("~")
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save annotated snapshot",
                os.path.join(default_dir, "compiler_snapshot.png"),
                "PNG Images (*.png)",
            )
            if not file_path:
                return
            if not file_path.lower().endswith(".png"):
                file_path += ".png"
            if combined.save(file_path, "PNG"):
                QMessageBox.information(
                    self, "Snapshot saved",
                    f"Annotated snapshot saved to:\n{file_path}",
                )
            else:
                QMessageBox.critical(self, "Save failed", "Could not save the snapshot.")
        except Exception as e:
            QMessageBox.critical(self, "Save failed", f"Error saving snapshot:\n{e}")

    # -- Drawing-tool API (proxied to the annotation overlay) ----------------
    def set_tool(self, tool_mode) -> None:
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


# ═══════════════════════════════════════════════════════════════════════════
#  3. BrowserWidget  (real web browser + annotation overlay + snapshot)
# ═══════════════════════════════════════════════════════════════════════════

class BrowserWidget(QWidget):
    """Real embedded web browser with a transparent annotation overlay.

    Layout:
        [ ◀ Back ] [ ▶ Forward ] [ 🔄 Reload ]   [   URL bar …   ] [ Go ] [ 📸 ]

    Underneath sits a ``QWebEngineView`` that loads the live web page.
    On top of it sits a transparent ``PptCanvasView`` annotation overlay
    that the educator can draw on with the main toolbar's pen / highlighter
    / eraser / shapes / text tools. The overlay is hidden from mouse events
    whenever the Select tool is active so the user can still click links,
    scroll, and interact with the page normally.
    """

    url_changed = Signal(str)
    annotations_changed = Signal(list)   # list of QGraphicsItem objects (for page meta)

    def __init__(
        self,
        initial_url: str = "https://www.google.com",
        saved_annotations: list | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._build_ui(initial_url)
        self._web.urlChanged.connect(self._on_url_loaded)
        # Whenever the user draws on the overlay, persist to the page meta.
        self._annot_overlay.stroke_drawn.connect(self._on_annotations_changed)
        # Restore previously saved annotations (if any).
        if saved_annotations:
            self._annot_overlay.load_annotation_items(saved_annotations)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self, initial_url: str) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # — Navigation bar —
        nav = QFrame(self)
        nav.setObjectName("browserNavBar")
        nav.setStyleSheet(
            f"QFrame#browserNavBar {{ {_DARK_GLASS_BG} "
            f"border-bottom: 1px solid rgba(99,102,241,0.15); }}"
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

        self._back_btn = QPushButton("◀")
        self._back_btn.setStyleSheet(nav_btn_style)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setToolTip("Back")
        self._back_btn.clicked.connect(self._web.back)
        nav_layout.addWidget(self._back_btn)

        self._fwd_btn = QPushButton("▶")
        self._fwd_btn.setStyleSheet(nav_btn_style)
        self._fwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fwd_btn.setToolTip("Forward")
        self._fwd_btn.clicked.connect(self._web.forward)
        nav_layout.addWidget(self._fwd_btn)

        self._reload_btn = QPushButton("🔄")
        self._reload_btn.setStyleSheet(nav_btn_style)
        self._reload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reload_btn.setToolTip("Reload page")
        self._reload_btn.clicked.connect(self._web.reload)
        nav_layout.addWidget(self._reload_btn)

        # URL bar
        self._url_bar = QLineEdit()
        self._url_bar.setStyleSheet(_LINE_EDIT_STYLE)
        self._url_bar.setPlaceholderText("Enter URL…")
        self._url_bar.setText(initial_url)
        self._url_bar.returnPressed.connect(self.load_url)
        nav_layout.addWidget(self._url_bar, 1)

        # Go button
        self._go_btn = QPushButton("Go")
        self._go_btn.setStyleSheet(_ACCENT_BTN)
        self._go_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._go_btn.clicked.connect(self.load_url)
        nav_layout.addWidget(self._go_btn)

        # Snapshot button (saves the current annotated view as PNG)
        self._snap_btn = QPushButton("📸")
        self._snap_btn.setStyleSheet(nav_btn_style)
        self._snap_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._snap_btn.setToolTip("Save annotated snapshot (PNG)")
        self._snap_btn.clicked.connect(self._save_snapshot)
        nav_layout.addWidget(self._snap_btn)

        # Clear annotations button
        self._clear_annot_btn = QPushButton("🧹")
        self._clear_annot_btn.setStyleSheet(nav_btn_style)
        self._clear_annot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_annot_btn.setToolTip("Clear annotations")
        self._clear_annot_btn.clicked.connect(self._clear_annotations)
        nav_layout.addWidget(self._clear_annot_btn)

        root.addWidget(nav)

        # — Content area: web view + annotation overlay —
        self._content_frame = QFrame(self)
        content_layout = QVBoxLayout(self._content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._web = QWebEngineView(self._content_frame)
        self._web.setUrl(QUrl(initial_url))
        content_layout.addWidget(self._web)

        # Transparent annotation overlay on top of the web view.
        self._annot_overlay = PptCanvasView(self._content_frame)
        self._annot_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._annot_overlay.setBackgroundBrush(QColor(0, 0, 0, 0))
        self._annot_overlay.setStyleSheet("background: transparent; border: none;")
        self._annot_overlay.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._annot_overlay.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._annot_overlay.setVisible(True)
        self._annot_overlay.lower()

        root.addWidget(self._content_frame, 1)

    # ------------------------------------------------------------------
    # Theme hook
    # ------------------------------------------------------------------
    def set_theme(self, theme_name: str) -> None:
        # Nav bar is themed via the global stylesheet; nothing per-widget to do.
        return

    # ------------------------------------------------------------------
    # Layout / overlay geometry
    # ------------------------------------------------------------------
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_annot_overlay()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._update_annot_overlay()

    def _update_annot_overlay(self) -> None:
        if not self._web or not self._annot_overlay:
            return
        geom = self._web.geometry()
        self._annot_overlay.setGeometry(geom)
        w, h = geom.width(), geom.height()
        if w > 0 and h > 0:
            scene = self._annot_overlay.scene()
            scene.setSceneRect(0, 0, w, h)
            self._annot_overlay.resetTransform()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def load_url(self) -> None:
        url = self._url_bar.text().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self._url_bar.setText(url)
        self._web.setUrl(QUrl(url))

    def _on_url_loaded(self, qurl: QUrl) -> None:
        url_str = qurl.toString()
        self._url_bar.setText(url_str)
        self.url_changed.emit(url_str)

    # ------------------------------------------------------------------
    # Annotations
    # ------------------------------------------------------------------
    def _on_annotations_changed(self) -> None:
        # Hand the current annotation items up to the main window so it can
        # stash them in the page meta.  Items stay in the scene here; the
        # main window just keeps a reference for later restoration.
        try:
            items = self._annot_overlay.get_annotation_items()
            self.annotations_changed.emit(items)
        except Exception:
            pass

    def save_annotations(self) -> list:
        """Detach annotation items from the scene and return them so the
        caller can stash them in the page meta.  Call this *before* the
        widget is destroyed so the items survive.
        """
        items = self._annot_overlay.get_annotation_items()
        for item in items:
            self._annot_overlay.scene().removeItem(item)
        return items

    def load_annotations(self, items: list) -> None:
        """Restore a previously saved set of annotation items."""
        if not items:
            return
        self._annot_overlay.load_annotation_items(items)

    def _clear_annotations(self) -> None:
        self._annot_overlay.clear_annotations()
        self._on_annotations_changed()

    def _save_snapshot(self) -> None:
        """Grab a PNG of the web view + annotation overlay and save it."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from PySide6.QtCore import QStandardPaths
        from PySide6.QtGui import QPainter, QPixmap as _QPixmap
        import os

        try:
            overlay_pix = self._annot_overlay.grab()
            web_pix = self._web.grab()
            combined = _QPixmap(web_pix.size())
            combined.fill(QColor(0, 0, 0, 0))
            p = QPainter(combined)
            p.drawPixmap(0, 0, web_pix)
            p.drawPixmap(0, 0, overlay_pix)
            p.end()

            default_dir = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DocumentsLocation
            ) or os.path.expanduser("~")
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save annotated snapshot",
                os.path.join(default_dir, "browser_snapshot.png"),
                "PNG Images (*.png)",
            )
            if not file_path:
                return
            if not file_path.lower().endswith(".png"):
                file_path += ".png"
            if combined.save(file_path, "PNG"):
                QMessageBox.information(
                    self, "Snapshot saved",
                    f"Annotated snapshot saved to:\n{file_path}",
                )
            else:
                QMessageBox.critical(self, "Save failed", "Could not save the snapshot.")
        except Exception as e:
            QMessageBox.critical(self, "Save failed", f"Error saving snapshot:\n{e}")

    # ------------------------------------------------------------------
    # Drawing-tool API (proxied to the annotation overlay)
    # ------------------------------------------------------------------
    def set_tool(self, tool_mode) -> None:
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


# ═══════════════════════════════════════════════════════════════════════════
#  4. HtmlCanvasWidget  (HTML with annotation overlay)
# ═══════════════════════════════════════════════════════════════════════════

class HtmlCanvasWidget(QWidget):
    """HTML renderer with a transparent annotation overlay and persistent toggle."""

    html_changed = Signal(str)

    def __init__(self, initial_html: str = "", saved_annotations: list | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.persistent = False
        self._build_ui(initial_html)
        # Restore any previously saved annotations.
        if saved_annotations:
            self._annot_overlay.load_annotation_items(saved_annotations)

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

    # -- Annotation persistence (used by main_window on page switch) --------
    def save_annotations(self) -> list:
        items = self._annot_overlay.get_annotation_items()
        for item in items:
            self._annot_overlay.scene().removeItem(item)
        return items

    def load_annotations(self, items: list) -> None:
        if not items:
            return
        self._annot_overlay.load_annotation_items(items)


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
