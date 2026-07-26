"""
UniBoard Main Window – Icon-based toolbar, QStackedWidget for canvas types,
proper shortcuts, PDF export, fullscreen toggle.
"""
import os
import time
import threading

import numpy as np
import cv2

from PySide6.QtGui import (
    QAction, QColor, QFont, QKeySequence, QPixmap, QIcon,
    QShortcut, QPainter, QPen
)
from PySide6.QtCore import Qt, QSize, QRect, QRectF, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QToolBar, QToolButton,
    QLabel, QComboBox, QSpinBox, QColorDialog, QFileDialog,
    QMessageBox, QInputDialog, QStackedWidget, QWidget, QHBoxLayout,
    QSizePolicy, QFrame
)

import config
from core.page_manager import PageManager
from ui.canvas import WhiteboardCanvas
from ui.sidebar import SidebarWidget
from ui.embedded_widgets import CompilerWidget, BrowserWidget, HtmlCanvasWidget
from ui.ppt_canvas import PptCanvasWidget
from ui.pdf_canvas import PdfCanvasWidget
from ui.styles import Themes
from utils.pdf_export import export_images_to_pdf


# ---------------------------------------------------------------------------
# Helper: Create a colored icon from a Unicode symbol
# ---------------------------------------------------------------------------
def _make_icon(symbol: str, size: int = 28, color: str = "#d1d1d6") -> QIcon:
    """Render a Unicode symbol onto a QPixmap with a subtle glow effect.

    Uses anti-aliased text with a translucent shadow layer so the icon
    reads clearly against any toolbar background.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    font_size = int(size * 0.58)
    f = QFont("Segoe UI Symbol", font_size)
    f.setStyleStrategy(QFont.PreferAntialias)
    painter.setFont(f)

    # Subtle offset shadow / glow
    shadow = QColor(color)
    shadow.setAlpha(55)
    painter.setPen(QPen(shadow, 1.2))
    painter.drawText(QRectF(1.2, 1.8, size, size), Qt.AlignCenter, symbol)

    # Main foreground
    painter.setPen(QPen(QColor(color), 1.2))
    painter.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, symbol)
    painter.end()
    return QIcon(pixmap)


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.APP_NAME} — Interactive Whiteboard")
        self.setObjectName("centralWidget")

        # ---- Window sizing: 90% of screen, centered ----
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.9)
        height = int(screen.height() * 0.9)
        self.resize(width, height)
        self.move(
            int((screen.width() - width) / 2),
            int((screen.height() - height) / 2),
        )

        self.is_fullscreen = False
        self._saved_geometry = None

        # ---- Core ----
        self.page_manager = PageManager()

        # ---- Pre-initialize Qt WebEngine process ----
        # The first QWebEngineView creation triggers a heavy one-time
        # initialization (spawning the QtWebEngineProcess).  By creating
        # a hidden dummy view here we move that cost to startup so the
        # first switch to an HTML / Browser canvas feels instant.
        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            self._dummy_web = QWebEngineView(self)
            self._dummy_web.hide()
        except Exception:
            self._dummy_web = None

        # ---- Stacked central widget ----
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.canvas = WhiteboardCanvas(self)
        self.stack.addWidget(self.canvas)  # index 0 = plain canvas

        self.embedded_html = None
        self.embedded_compiler = None
        self.embedded_browser = None
        self.embedded_ppt = None
        self.embedded_pdf = None
        self.current_embedded_index = None

        # ---- Docks & Toolbar ----
        self.setup_docks()
        self.setup_toolbar()

        # ---- Connect canvas signals ----
        self.canvas.new_canvas_requested.connect(self.add_new_canvas)

        # ---- Load default page ----
        if self.page_manager.active_page:
            self.canvas.set_page_node(self.page_manager.active_page)

        # ---- Theme ----
        self.current_theme = "Dark Glass"
        self.apply_theme(self.current_theme)

        # ---- Shortcuts ----
        self.create_shortcuts()

    # ==================================================================
    # Dock (Outline Sidebar)
    # ==================================================================
    def setup_docks(self):
        self.left_dock = QDockWidget("Outline", self)
        self.left_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.sidebar_widget = SidebarWidget(self.page_manager, self)
        self.left_dock.setWidget(self.sidebar_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)
        # Left pane is hidden – topic/subtopic management moved to the canvas itself
        self.left_dock.hide()
        self.left_dock.setVisible(False)

        self.sidebar_widget.page_selected.connect(self.on_page_selected)
        self.sidebar_widget.delete_page_requested.connect(self.on_delete_page_requested)
        self.sidebar_widget.rename_page_requested.connect(self.on_rename_page_requested)

    # ==================================================================
    # Toolbar – icon-based, single row
    # ==================================================================
    def setup_toolbar(self):
        tb = QToolBar("Tools")
        tb.setIconSize(QSize(24, 24))
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.addToolBar(Qt.TopToolBarArea, tb)
        self.toolbar = tb

        # ── Drawing tools ──────────────────────────────────────────────
        self.tool_actions = {}
        tools = [
            ("Select & Move",  config.MODE_SELECT,      "🖱",  "V"),
            ("Pen Draw",       config.MODE_PEN,          "✏",   "P"),
            ("Highlighter",    config.MODE_HIGHLIGHTER,  "🖍",  "H"),
            ("Line",           config.MODE_LINE,         "╱",   "L"),
            ("Rectangle",      config.MODE_RECT,         "▭",   "R"),
            ("Circle / Ellipse", config.MODE_CIRCLE,     "◯",   "C"),
            ("Text Box",       config.MODE_TEXT,          "T",   "T"),
            ("Eraser",         config.MODE_ERASER,        "⌫",  "E"),
        ]

        for tooltip, mode, symbol, shortcut_key in tools:
            btn = QToolButton()
            btn.setIcon(_make_icon(symbol, 28, "#e0e0e8"))
            btn.setCheckable(True)
            btn.setToolTip(f"{tooltip}  ({shortcut_key})")
            btn.setFixedSize(36, 32)
            if mode == config.MODE_PEN:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, m=mode: self.set_canvas_tool(m))
            tb.addWidget(btn)
            self.tool_actions[mode] = btn

        tb.addSeparator()

        # ── Color picker ───────────────────────────────────────────────
        self.color_btn = QToolButton()
        self.color_btn.setToolTip("Brush Color")
        self.color_btn.setFixedSize(32, 32)
        self._update_color_swatch(self.canvas.pen_color)
        self.color_btn.clicked.connect(self.choose_color)
        tb.addWidget(self.color_btn)

        # ── Brush size (prominent, clearly visible) ────────────────────
        self.brush_box = QFrame()
        self.brush_box.setObjectName("sizeBoxBrush")
        self.brush_box.setStyleSheet("""
            QFrame#sizeBoxBrush {
                background-color: rgba(0, 255, 204, 0.10);
                border: 2px solid rgba(0, 255, 204, 0.55);
                border-radius: 8px;
            }
            QFrame#sizeBoxBrush:hover {
                background-color: rgba(0, 255, 204, 0.18);
                border: 2px solid rgba(0, 255, 204, 0.85);
            }
        """)
        brush_layout = QHBoxLayout(self.brush_box)
        brush_layout.setContentsMargins(6, 2, 6, 2)
        brush_layout.setSpacing(6)

        brush_icon = QLabel("◉")
        brush_icon.setStyleSheet(
            "color: #00ffcc; font-size: 18px; font-weight: bold; background: transparent; border: none;"
        )
        brush_icon.setToolTip("Brush / Stroke Size")
        brush_layout.addWidget(brush_icon)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 50)
        self.size_spin.setValue(self.canvas.pen_width)
        self.size_spin.setFixedWidth(60)
        self.size_spin.setMinimumHeight(28)
        self.size_spin.setToolTip("Brush / Stroke Size  (1-50 px)")
        self.size_spin.setStyleSheet("""
            QSpinBox {
                background-color: rgba(0, 0, 0, 0.45);
                border: 1px solid rgba(0, 255, 204, 0.4);
                border-radius: 4px;
                color: #00ffcc;
                font-size: 14px;
                font-weight: bold;
                padding: 2px 4px;
            }
            QSpinBox:hover { border: 1px solid rgba(0, 255, 204, 0.7); }
            QSpinBox:focus { border: 1px solid #00ffcc; }
        """)
        self.size_spin.valueChanged.connect(self.change_pen_size)
        brush_layout.addWidget(self.size_spin)
        tb.addWidget(self.brush_box)

        # ── Text size (prominent, clearly visible) ─────────────────────
        self.text_box = QFrame()
        self.text_box.setObjectName("sizeBoxText")
        self.text_box.setStyleSheet("""
            QFrame#sizeBoxText {
                background-color: rgba(168, 85, 247, 0.10);
                border: 2px solid rgba(168, 85, 247, 0.55);
                border-radius: 8px;
            }
            QFrame#sizeBoxText:hover {
                background-color: rgba(168, 85, 247, 0.18);
                border: 2px solid rgba(168, 85, 247, 0.85);
            }
        """)
        text_layout = QHBoxLayout(self.text_box)
        text_layout.setContentsMargins(6, 2, 6, 2)
        text_layout.setSpacing(6)

        text_icon = QLabel("A")
        text_icon.setStyleSheet(
            "color: #c4b5fd; font-size: 18px; font-weight: bold; background: transparent; border: none; font-family: 'Segoe UI';"
        )
        text_icon.setToolTip("Text Font Size")
        text_layout.addWidget(text_icon)

        self.text_spin = QSpinBox()
        self.text_spin.setRange(8, 72)
        self.text_spin.setValue(self.canvas.text_size)
        self.text_spin.setFixedWidth(60)
        self.text_spin.setMinimumHeight(28)
        self.text_spin.setToolTip("Text Font Size  (8-72 pt)")
        self.text_spin.setStyleSheet("""
            QSpinBox {
                background-color: rgba(0, 0, 0, 0.45);
                border: 1px solid rgba(168, 85, 247, 0.4);
                border-radius: 4px;
                color: #c4b5fd;
                font-size: 14px;
                font-weight: bold;
                padding: 2px 4px;
            }
            QSpinBox:hover { border: 1px solid rgba(168, 85, 247, 0.7); }
            QSpinBox:focus { border: 1px solid #c4b5fd; }
        """)
        self.text_spin.valueChanged.connect(self.change_text_size)
        text_layout.addWidget(self.text_spin)
        tb.addWidget(self.text_box)

        tb.addSeparator()

        # ── Handwriting toggle ─────────────────────────────────────────
        self.hw_btn = QToolButton()
        self.hw_btn.setIcon(_make_icon("✍", 28, "#d1d1d6"))
        self.hw_btn.setCheckable(True)
        self.hw_btn.setToolTip("Handwriting Recognition")
        self.hw_btn.setFixedSize(36, 32)
        self.hw_btn.clicked.connect(self.toggle_handwriting)
        tb.addWidget(self.hw_btn)

        # ── Undo / Redo ───────────────────────────────────────────────
        undo_btn = QToolButton()
        undo_btn.setIcon(_make_icon("↩", 28, "#d1d1d6"))
        undo_btn.setToolTip("Undo  (Ctrl+Z)")
        undo_btn.setFixedSize(36, 32)
        undo_btn.clicked.connect(self._undo_active)
        tb.addWidget(undo_btn)

        redo_btn = QToolButton()
        redo_btn.setIcon(_make_icon("↪", 28, "#d1d1d6"))
        redo_btn.setToolTip("Redo  (Ctrl+Y)")
        redo_btn.setFixedSize(36, 32)
        redo_btn.clicked.connect(self._redo_active)
        tb.addWidget(redo_btn)

        tb.addSeparator()

        # ── Grid toggle ───────────────────────────────────────────────
        self.grid_btn = QToolButton()
        self.grid_btn.setIcon(_make_icon("▦", 28, "#d1d1d6"))
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.setToolTip("Toggle Grid  (Ctrl+G)")
        self.grid_btn.setFixedSize(36, 32)
        self.grid_btn.clicked.connect(self.toggle_grid)
        tb.addWidget(self.grid_btn)

        # ── Theme combo ────────────────────────────────────────────────
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Glass", "Light Glass", "Slate"])
        self.theme_combo.setFixedWidth(145)
        self.theme_combo.setToolTip("Theme")
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        tb.addWidget(self.theme_combo)

        # ── Canvas mode combo ──────────────────────────────────────────
        self.canvas_type_combo = QComboBox()
        self.canvas_type_combo.addItems(["Canvas", "HTML", "Compiler", "Browser", "Presentation", "PDF"])
        self.canvas_type_combo.setFixedWidth(145)
        self.canvas_type_combo.setToolTip("Canvas Type")
        self.canvas_type_combo.currentTextChanged.connect(self.on_canvas_type_changed)
        tb.addWidget(self.canvas_type_combo)

        tb.addSeparator()

        # ── PDF export ─────────────────────────────────────────────────
        pdf_btn = QToolButton()
        pdf_btn.setIcon(_make_icon("📕", 28, "#f87171"))
        pdf_btn.setToolTip("Export to PDF  (Ctrl+E)")
        pdf_btn.setFixedSize(36, 32)
        pdf_btn.clicked.connect(self.export_to_pdf)
        tb.addWidget(pdf_btn)

        # ── Fullscreen ─────────────────────────────────────────────────
        self.fs_btn = QToolButton()
        self.fs_btn.setIcon(_make_icon("⛶", 28, "#d1d1d6"))
        self.fs_btn.setToolTip("Fullscreen  (F11)")
        self.fs_btn.setFixedSize(36, 32)
        self.fs_btn.clicked.connect(self.toggle_fullscreen)
        tb.addWidget(self.fs_btn)

        # ── Screen Recording ────────────────────────────────────────────
        self.rec_btn = QToolButton()
        self.rec_btn.setIcon(_make_icon("⬤", 28, "#d1d1d6"))
        self.rec_btn.setToolTip("Start Recording  (Ctrl+R)")
        self.rec_btn.setFixedSize(36, 32)
        self.rec_btn.setCheckable(True)
        self.rec_btn.clicked.connect(self.toggle_recording)
        tb.addWidget(self.rec_btn)

        # Recording state
        self._recording = False
        self._recorder = None

    # ==================================================================
    # Toolbar Helpers
    # ==================================================================
    def _update_color_swatch(self, color: QColor):
        """Paint a small color swatch as the icon of the color button."""
        px = QPixmap(24, 24)
        px.fill(QColor(0, 0, 0, 0))
        p = QPainter(px)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(color)
        p.setPen(QPen(QColor(255, 255, 255, 80), 1))
        p.drawRoundedRect(2, 2, 20, 20, 4, 4)
        p.end()
        self.color_btn.setIcon(QIcon(px))

    def set_canvas_tool(self, tool_mode):
        for mode, btn in self.tool_actions.items():
            btn.setChecked(mode == tool_mode)
        target = self._get_active_target()
        target.set_tool(tool_mode)

    def _update_size_controls_style(self):
        """Refresh brush/text box borders & icons to match current pen color."""
        c = self.canvas.pen_color
        cname = c.name()
        # Brush box border = pen color
        self.brush_box.setStyleSheet(f"""
            QFrame#sizeBoxBrush {{
                background-color: rgba({c.red()}, {c.green()}, {c.blue()}, 25);
                border: 2px solid {cname};
                border-radius: 8px;
            }}
            QFrame#sizeBoxBrush:hover {{
                background-color: rgba({c.red()}, {c.green()}, {c.blue()}, 50);
                border: 2px solid {cname};
            }}
        """)
        self.size_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: rgba(0, 0, 0, 0.45);
                border: 1px solid {cname};
                border-radius: 4px;
                color: {cname};
                font-size: 14px;
                font-weight: bold;
                padding: 2px 4px;
            }}
            QSpinBox:hover {{ border: 1px solid {cname}; }}
            QSpinBox:focus {{ border: 1px solid {cname}; }}
        """)
        # Text box border = pen color
        self.text_box.setStyleSheet(f"""
            QFrame#sizeBoxText {{
                background-color: rgba({c.red()}, {c.green()}, {c.blue()}, 25);
                border: 2px solid {cname};
                border-radius: 8px;
            }}
            QFrame#sizeBoxText:hover {{
                background-color: rgba({c.red()}, {c.green()}, {c.blue()}, 50);
                border: 2px solid {cname};
            }}
        """)
        self.text_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: rgba(0, 0, 0, 0.45);
                border: 1px solid {cname};
                border-radius: 4px;
                color: {cname};
                font-size: 14px;
                font-weight: bold;
                padding: 2px 4px;
            }}
            QSpinBox:hover {{ border: 1px solid {cname}; }}
            QSpinBox:focus {{ border: 1px solid {cname}; }}
        """)

    def choose_color(self):
        target = self._get_active_target()
        color = QColorDialog.getColor(target.pen_color, self, "Select Color")
        if color.isValid():
            target.pen_color = color
            if hasattr(target, 'highlighter_color'):
                target.highlighter_color = QColor(
                    color.red(), color.green(), color.blue(), 100
                )
            self._update_color_swatch(color)
            self._update_size_controls_style()

    def _get_active_target(self):
        current = self.stack.currentWidget()
        if current is self.canvas:
            return self.canvas
        for attr in ("embedded_html", "embedded_ppt", "embedded_pdf"):
            widget = getattr(self, attr, None)
            if widget is not None and current is widget:
                return widget
        return self.canvas

    def change_pen_size(self, size):
        target = self._get_active_target()
        target.pen_width = size
        if hasattr(target, 'highlighter_width'):
            target.highlighter_width = max(size * 4, 8)
        if hasattr(target, 'eraser_width'):
            target.eraser_width = max(size * 5, 10)

    def change_text_size(self, size):
        target = self._get_active_target()
        target.text_size = size

    def toggle_handwriting(self, checked=None):
        if checked is None:
            checked = not self.canvas.handwriting_enabled
            self.hw_btn.setChecked(checked)
        self.canvas.handwriting_enabled = checked
        if checked:
            self.hw_btn.setStyleSheet(
                "background-color: rgba(0,255,100,0.2); border:1px solid #00ff66; border-radius:6px;"
            )
        else:
            self.hw_btn.setStyleSheet("")

    def toggle_grid(self, checked=None):
        if checked is None:
            checked = not self.canvas.grid_visible
        self.canvas.grid_visible = checked
        self.grid_btn.setChecked(checked)
        self.canvas.viewport().update()

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.showNormal()
            if self._saved_geometry:
                self.setGeometry(self._saved_geometry)
            self.is_fullscreen = False
        else:
            self._saved_geometry = self.geometry()
            self.showFullScreen()
            self.is_fullscreen = True

    # ==================================================================
    # Screen Recording
    # ==================================================================
    def toggle_recording(self):
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Recording",
            f"uniboard_recording_{int(time.time())}.avi",
            "AVI Files (*.avi)"
        )
        if not output_path:
            self.rec_btn.setChecked(False)
            return

        self._recorder = ScreenRecorder(output_path)
        self._recorder.set_window(self)
        self._recorder.start()
        self._recording = True
        self.rec_btn.setIcon(_make_icon("⬤", 28, "#f87171"))
        self.rec_btn.setToolTip("Stop Recording")

    def _stop_recording(self):
        if self._recorder:
            self._recorder.stop()
            self._recorder = None
        self._recording = False
        self.rec_btn.setIcon(_make_icon("⬤", 28, "#d1d1d6"))
        self.rec_btn.setToolTip("Start Recording  (Ctrl+R)")
        self.rec_btn.setChecked(False)
        QMessageBox.information(self, "Recording Saved", "Recording saved successfully!")

    # ==================================================================
    # Canvas Type Switching (QStackedWidget)
    # ==================================================================
    def on_canvas_type_changed(self, type_text):
        type_map = {
            "Canvas":       config.CANVAS_PLAIN,
            "HTML":         config.CANVAS_HTML,
            "Compiler":     config.CANVAS_COMPILER,
            "Browser":      config.CANVAS_BROWSER,
            "Presentation": config.CANVAS_PPT,
            "PDF":          config.CANVAS_PDF,
        }
        mode = type_map.get(type_text, config.CANVAS_PLAIN)

        if not self.page_manager.active_page:
            return

        self.page_manager.active_page.meta["canvas_type"] = mode
        self.canvas.current_canvas_type = mode

        if mode == config.CANVAS_PLAIN:
            self.stack.setCurrentWidget(self.canvas)
            self.canvas.update_overlay_visibility()
            self._cleanup_embedded()
        else:
            self._show_embedded(mode)

        self.canvas_type_combo.blockSignals(True)
        self.canvas_type_combo.setCurrentText(type_text)
        self.canvas_type_combo.blockSignals(False)

    def _show_embedded(self, mode):
        page = self.page_manager.active_page
        if not page:
            return

        self._cleanup_embedded()

        if mode == config.CANVAS_HTML:
            self.embedded_html = HtmlCanvasWidget(page.meta.get("html_code", ""))
            self.embedded_html.html_changed.connect(
                lambda html: page.meta.update({"html_code": html})
            )
            self.stack.addWidget(self.embedded_html)
            self.stack.setCurrentWidget(self.embedded_html)

        elif mode == config.CANVAS_COMPILER:
            self.embedded_compiler = CompilerWidget(
                page.meta.get("compiled_code", ""),
                page.meta.get("compiler_lang", "Python"),
            )
            self.embedded_compiler.code_changed.connect(
                lambda code, lang: page.meta.update(
                    {"compiled_code": code, "compiler_lang": lang}
                )
            )
            self.stack.addWidget(self.embedded_compiler)
            self.stack.setCurrentWidget(self.embedded_compiler)

        elif mode == config.CANVAS_BROWSER:
            self.embedded_browser = BrowserWidget(
                page.meta.get("live_url", "https://www.google.com")
            )
            self.embedded_browser.url_changed.connect(
                lambda url: page.meta.update({"live_url": url})
            )
            self.stack.addWidget(self.embedded_browser)
            self.stack.setCurrentWidget(self.embedded_browser)

        elif mode == config.CANVAS_PPT:
            ppt_path = page.meta.get("ppt_path", "")
            self.embedded_ppt = PptCanvasWidget()
            if ppt_path and os.path.exists(ppt_path):
                self.embedded_ppt._load_ppt(ppt_path)
            self.stack.addWidget(self.embedded_ppt)
            self.stack.setCurrentWidget(self.embedded_ppt)

        elif mode == config.CANVAS_PDF:
            pdf_path = page.meta.get("pdf_path", "")
            self.embedded_pdf = PdfCanvasWidget()
            if pdf_path and os.path.exists(pdf_path):
                self.embedded_pdf._load_pdf(pdf_path)
            self.stack.addWidget(self.embedded_pdf)
            self.stack.setCurrentWidget(self.embedded_pdf)

    def _cleanup_embedded(self):
        for attr in ("embedded_html", "embedded_compiler", "embedded_browser", "embedded_ppt", "embedded_pdf"):
            widget = getattr(self, attr, None)
            if widget:
                idx = self.stack.indexOf(widget)
                if idx >= 0:
                    self.stack.removeWidget(widget)
                widget.deleteLater()
                setattr(self, attr, None)

    # ==================================================================
    # Theme
    # ==================================================================
    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        self.setStyleSheet(Themes.get_style(theme_name))

        if theme_name == "Light Glass":
            self.canvas.canvas_bg_color = QColor("#f5f5fa")
            self.canvas.grid_color = QColor("#dddde5")
            self.canvas.pen_color = QColor("#1e3a8a")
        elif theme_name == "Slate":
            self.canvas.canvas_bg_color = QColor("#0f172a")
            self.canvas.grid_color = QColor("#1e293b")
            self.canvas.pen_color = QColor("#38bdf8")
        else:  # Dark Glass
            self.canvas.canvas_bg_color = QColor("#0d0d11")
            self.canvas.grid_color = QColor("#1a1a22")
            self.canvas.pen_color = QColor("#00ffcc")

        self.canvas.update_background()
        self.canvas.viewport().update()
        self.canvas.refresh_all_text_colors()
        self._update_color_swatch(self.canvas.pen_color)
        self._update_size_controls_style()

    # ==================================================================
    # Shortcuts
    # ==================================================================
    def create_shortcuts(self):
        QShortcut(QKeySequence("V"), self, lambda: self.set_canvas_tool(config.MODE_SELECT))
        QShortcut(QKeySequence("P"), self, lambda: self.set_canvas_tool(config.MODE_PEN))
        QShortcut(QKeySequence("H"), self, lambda: self.set_canvas_tool(config.MODE_HIGHLIGHTER))
        QShortcut(QKeySequence("L"), self, lambda: self.set_canvas_tool(config.MODE_LINE))
        QShortcut(QKeySequence("R"), self, lambda: self.set_canvas_tool(config.MODE_RECT))
        QShortcut(QKeySequence("C"), self, lambda: self.set_canvas_tool(config.MODE_CIRCLE))
        QShortcut(QKeySequence("T"), self, lambda: self.set_canvas_tool(config.MODE_TEXT))
        QShortcut(QKeySequence("E"), self, lambda: self.set_canvas_tool(config.MODE_ERASER))
        QShortcut(QKeySequence("Ctrl+Z"), self, self._undo_active)
        QShortcut(QKeySequence("Ctrl+Y"), self, self._redo_active)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self._redo_active)
        QShortcut(QKeySequence("Ctrl+G"), self, lambda: self.toggle_grid())
        QShortcut(QKeySequence("Ctrl+T"), self, self.cycle_theme)
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Ctrl+E"), self, self.export_to_pdf)
        QShortcut(QKeySequence("Ctrl+H"), self, lambda: self.toggle_handwriting())
        QShortcut(QKeySequence("Ctrl+R"), self, self.toggle_recording)

    def cycle_theme(self):
        themes = ["Dark Glass", "Light Glass", "Slate"]
        try:
            idx = themes.index(self.current_theme)
            nxt = themes[(idx + 1) % len(themes)]
        except ValueError:
            nxt = themes[0]
        self.theme_combo.setCurrentText(nxt)

    def _undo_active(self):
        self._get_active_target().undo()

    def _redo_active(self):
        self._get_active_target().redo()

    # ==================================================================
    # PDF Export
    # ==================================================================
    def export_to_pdf(self):
        scopes = ["Current Canvas", "All Slides"]
        scope, ok = QInputDialog.getItem(
            self, "Export PDF", "Select export scope:", scopes, 0, False
        )
        if not ok:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "", "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        temp_dir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "temp_pdf_images"
        )
        os.makedirs(temp_dir, exist_ok=True)
        image_paths = []

        try:
            if scope == "Current Canvas":
                self.stack.setCurrentWidget(self.canvas)
                QApplication.processEvents()
                pixmap = self.canvas.grab()
                img_path = os.path.join(temp_dir, "current.png")
                pixmap.save(img_path, "PNG")
                image_paths.append(img_path)
            else:
                for page in self.page_manager.root_pages:
                    old_type = page.meta.get("canvas_type", config.CANVAS_PLAIN)
                    page.meta["canvas_type"] = config.CANVAS_PLAIN
                    self.canvas.set_page_node(page)
                    self.stack.setCurrentWidget(self.canvas)
                    QApplication.processEvents()
                    pixmap = self.canvas.grab()
                    img_path = os.path.join(temp_dir, f"{page.id}.png")
                    pixmap.save(img_path, "PNG")
                    image_paths.append(img_path)
                    page.meta["canvas_type"] = old_type

                # Restore active page
                if self.page_manager.active_page:
                    self.canvas.set_page_node(self.page_manager.active_page)
                    active_type = self.page_manager.active_page.meta.get(
                        "canvas_type", config.CANVAS_PLAIN
                    )
                    if active_type != config.CANVAS_PLAIN:
                        self._show_embedded(active_type)
                    else:
                        self.stack.setCurrentWidget(self.canvas)
                    QApplication.processEvents()

            export_images_to_pdf(image_paths, file_path)
            QMessageBox.information(
                self, "Export Complete", f"PDF saved to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Export Error", f"Failed to export PDF:\n{str(e)}"
            )
        finally:
            for p in image_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass

    # ==================================================================
    # Sidebar Signal Handlers
    # ==================================================================
    def on_page_selected(self, page_id):
        node = self.page_manager.find_node_by_id(page_id)
        if not node:
            return

        self.page_manager.active_page = node
        self.canvas.set_page_node(node)

        canvas_type = node.meta.get("canvas_type", config.CANVAS_PLAIN)
        reverse_map = {
            config.CANVAS_PLAIN:    "Canvas",
            config.CANVAS_HTML:     "HTML",
            config.CANVAS_COMPILER: "Compiler",
            config.CANVAS_BROWSER:  "Browser",
            config.CANVAS_PPT:      "Presentation",
            config.CANVAS_PDF:      "PDF",
        }

        self.canvas_type_combo.blockSignals(True)
        self.canvas_type_combo.setCurrentText(reverse_map.get(canvas_type, "Canvas"))
        self.canvas_type_combo.blockSignals(False)

        if canvas_type == config.CANVAS_PLAIN:
            self.stack.setCurrentWidget(self.canvas)
            self._cleanup_embedded()
        else:
            self._show_embedded(canvas_type)

    def on_delete_page_requested(self, page_id):
        all_nodes = self.page_manager.get_all_nodes_flat()
        if len(all_nodes) <= 1:
            QMessageBox.warning(
                self, "Cannot Delete", "You must keep at least one page."
            )
            return

        reply = QMessageBox.question(
            self,
            "Delete Slide",
            "Delete this slide and all its subtopics?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.page_manager.delete_page(page_id)
            self.sidebar_widget.refresh_tree()
            if self.page_manager.active_page:
                self.on_page_selected(self.page_manager.active_page.id)

    def on_rename_page_requested(self, page_id, new_title):
        node = self.page_manager.find_node_by_id(page_id)
        if node and new_title.strip():
            node.title = new_title.strip()
            if self.page_manager.active_page == node:
                self.canvas.refresh_agenda_overlay()

    def add_new_canvas(self):
        """Create a new blank page/canvas and switch to it."""
        title, ok = QInputDialog.getText(
            self, "New Canvas", "Enter canvas title:"
        )
        if not ok or not title.strip():
            return
        try:
            new_node = self.page_manager.create_page(title.strip())
        except ValueError as e:
            QMessageBox.warning(self, "Limit Exceeded", str(e))
            return
        self.page_manager.active_page = new_node
        self.canvas.set_page_node(new_node)
        self.stack.setCurrentWidget(self.canvas)
        self._cleanup_embedded()
        # Make sure the plain-canvas overlays are shown
        self.canvas.update_overlay_visibility()


# ---------------------------------------------------------------------------
# Screen Recorder – captures the main window at a fixed FPS and writes to AVI
# ---------------------------------------------------------------------------
class ScreenRecorder:
    """Records the main window's content to an AVI video file using OpenCV."""

    def __init__(self, output_path: str, fps: int = 15):
        self.output_path = output_path
        self.fps = fps
        self._running = False
        self._thread = None
        self._writer = None
        self._window = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self._writer:
            self._writer.release()
            self._writer = None

    def set_window(self, window):
        """Provide the QMainWindow to capture."""
        self._window = window

    def _run(self):
        import time as _time
        if self._window is None:
            return

        # Determine the capture area (the central widget / stack)
        widget = self._window.stack
        geom = widget.geometry()
        w = geom.width()
        h = geom.height()

        # Use a four-character codec – 'XVID' is widely supported
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self._writer = cv2.VideoWriter(self.output_path, fourcc, self.fps, (w, h))

        interval = 1.0 / self.fps
        while self._running:
            # Grab the widget content via Qt's grab()
            pixmap = widget.grab()
            img = pixmap.toImage()
            if img.isNull():
                _time.sleep(interval)
                continue

            # Convert QImage → numpy array (BGR for OpenCV)
            img = img.convertToFormat(img.Format_RGBA8888)
            h, w = img.height(), img.width()
            ptr = img.bits()
            ptr.setsize(h * w * 4)
            arr = np.array(ptr, dtype=np.uint8).reshape(h, w, 4)
            frame = arr[:, :, :3][:, :, ::-1]  # RGBA → BGR

            self._writer.write(frame)
            _time.sleep(interval)
