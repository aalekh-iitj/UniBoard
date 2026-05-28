import os

from PySide6.QtGui import QAction, QColor, QIcon, QFont, QKeySequence, QPixmap, QShortcut
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QToolBar, QToolButton,
    QLabel, QComboBox, QSpinBox, QColorDialog, QFileDialog,
    QMessageBox, QInputDialog, QStackedWidget,
    QPushButton, QWidget
)

import config
from core.page_manager import PageManager
from ui.canvas import WhiteboardCanvas
from ui.sidebar import SidebarWidget
from ui.embedded_widgets import HTMLRenderWidget, CompilerWidget, BrowserWidget
from ui.styles import Themes
from utils.pdf_export import export_images_to_pdf


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.APP_NAME} - Interactive Whiteboard")
        self.setObjectName("centralWidget")

        # Window size: 90% of screen
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.9)
        height = int(screen.height() * 0.9)
        self.resize(width, height)
        x = int((screen.width() - width) / 2)
        y = int((screen.height() - height) / 2)
        self.move(x, y)

        self.is_fullscreen = False
        self._saved_geometry = None

        # Core page manager
        self.page_manager = PageManager()

        # --- Stacked Widget as Central Widget ---
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Canvas (index 0)
        self.canvas = WhiteboardCanvas(self)
        self.stack.addWidget(self.canvas)  # index 0

        # Embedded widget placeholders (indices 1-3)
        self.embedded_html = None
        self.embedded_compiler = None
        self.embedded_browser = None
        self.current_embedded_index = None

        # Sidebar dock
        self.setup_docks()

        # Toolbar
        self.setup_toolbar()

        # Load default page
        if self.page_manager.active_page:
            self.canvas.set_page_node(self.page_manager.active_page)

        # Initial theme
        self.current_theme = "Dark Glass"
        self.apply_theme(self.current_theme)

        # Shortcuts
        self.create_shortcuts()

    def setup_docks(self):
        self.left_dock = QDockWidget("Outline", self)
        self.left_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.sidebar_widget = SidebarWidget(self.page_manager, self)
        self.left_dock.setWidget(self.sidebar_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)

        self.sidebar_widget.page_selected.connect(self.on_page_selected)
        self.sidebar_widget.delete_page_requested.connect(self.on_delete_page_requested)
        self.sidebar_widget.rename_page_requested.connect(self.on_rename_page_requested)

    def setup_toolbar(self):
        self.toolbar = QToolBar("Tools")
        self.toolbar.setIconSize(QSize(20, 20))
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # --- Tool buttons (icon-only with tooltips) ---
        self.tool_actions = {}
        tools = [
            ("Select", config.MODE_SELECT, "V", "Select & Move (V)"),
            ("Pen", config.MODE_PEN, "P", "Pen Draw (P)"),
            ("Highlight", config.MODE_HIGHLIGHTER, "H", "Highlighter (H)"),
            ("Line", config.MODE_LINE, "L", "Line (L)"),
            ("Rect", config.MODE_RECT, "R", "Rectangle (R)"),
            ("Circle", config.MODE_CIRCLE, "C", "Circle (C)"),
            ("Text", config.MODE_TEXT, "T", "Text Box (T)"),
            ("Eraser", config.MODE_ERASER, "E", "Eraser (E)"),
        ]

        for name, mode, icon_char, tooltip in tools:
            action = QAction(icon_char, self)
            action.setCheckable(True)
            action.setToolTip(tooltip)
            action.setStatusTip(tooltip)
            action.setShortcut(QKeySequence())
            font = QFont("Consolas", 12, QFont.Bold)
            action.setFont(font)
            if mode == config.MODE_PEN:
                action.setChecked(True)
            action.triggered.connect(lambda checked, m=mode: self.set_canvas_tool(m))
            self.toolbar.addAction(action)
            self.tool_actions[mode] = action

        self.toolbar.addSeparator()

        # --- Color button ---
        self.color_btn = QToolButton()
        self.color_btn.setToolTip("Brush Color")
        self.color_btn.setFixedSize(28, 28)
        self._update_color_btn_icon(self.canvas.pen_color)
        self.color_btn.clicked.connect(self.choose_color)
        self.toolbar.addWidget(self.color_btn)

        # --- Size spin ---
        size_label = QLabel("Size")
        size_label.setStyleSheet("font-size: 11px; padding: 0 2px;")
        self.toolbar.addWidget(size_label)
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 50)
        self.size_spin.setValue(self.canvas.pen_width)
        self.size_spin.setFixedWidth(45)
        self.size_spin.setToolTip("Brush Size")
        self.size_spin.valueChanged.connect(self.change_pen_size)
        self.toolbar.addWidget(self.size_spin)

        # --- Text size spin ---
        text_label = QLabel("Text")
        text_label.setStyleSheet("font-size: 11px; padding: 0 2px;")
        self.toolbar.addWidget(text_label)
        self.text_size_spin = QSpinBox()
        self.text_size_spin.setRange(8, 72)
        self.text_size_spin.setValue(self.canvas.text_size)
        self.text_size_spin.setFixedWidth(45)
        self.text_size_spin.setToolTip("Text Font Size")
        self.text_size_spin.valueChanged.connect(self.change_text_size)
        self.toolbar.addWidget(self.text_size_spin)

        self.toolbar.addSeparator()

        # --- Handwriting toggle ---
        self.handwriting_btn = QToolButton()
        self.handwriting_btn.setText("HW")
        self.handwriting_btn.setCheckable(True)
        self.handwriting_btn.setToolTip("Toggle Handwriting Recognition")
        self.handwriting_btn.setFixedSize(32, 28)
        self.handwriting_btn.clicked.connect(self.toggle_handwriting)
        self.toolbar.addWidget(self.handwriting_btn)

        # --- Undo / Redo ---
        undo_btn = QToolButton()
        undo_btn.setText("Undo")
        undo_btn.setToolTip("Undo (Ctrl+Z)")
        undo_btn.setFixedSize(42, 28)
        undo_btn.clicked.connect(self.canvas.undo)
        self.toolbar.addWidget(undo_btn)

        redo_btn = QToolButton()
        redo_btn.setText("Redo")
        redo_btn.setToolTip("Redo (Ctrl+Y)")
        redo_btn.setFixedSize(42, 28)
        redo_btn.clicked.connect(self.canvas.redo)
        self.toolbar.addWidget(redo_btn)

        self.toolbar.addSeparator()

        # --- Grid toggle ---
        self.grid_btn = QToolButton()
        self.grid_btn.setText("Grid")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.setToolTip("Toggle Grid (Ctrl+G)")
        self.grid_btn.setFixedSize(38, 28)
        self.grid_btn.clicked.connect(self.toggle_grid)
        self.toolbar.addWidget(self.grid_btn)

        # --- Theme selector ---
        theme_label = QLabel("Theme")
        theme_label.setStyleSheet("font-size: 11px; padding: 0 2px;")
        self.toolbar.addWidget(theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Glass", "Light Glass", "Slate"])
        self.theme_combo.setFixedWidth(95)
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        self.toolbar.addWidget(self.theme_combo)

        self.toolbar.addSeparator()

        # --- Canvas Type Selector ---
        canvas_label = QLabel("Mode")
        canvas_label.setStyleSheet("font-size: 11px; padding: 0 2px;")
        self.toolbar.addWidget(canvas_label)
        self.canvas_type_combo = QComboBox()
        self.canvas_type_combo.addItems(["Canvas", "HTML", "Compiler", "Browser"])
        self.canvas_type_combo.setFixedWidth(80)
        self.canvas_type_combo.currentTextChanged.connect(self.on_canvas_type_changed)
        self.toolbar.addWidget(self.canvas_type_combo)

        self.toolbar.addSeparator()

        # --- PDF Export ---
        pdf_btn = QToolButton()
        pdf_btn.setText("PDF")
        pdf_btn.setToolTip("Export as PDF")
        pdf_btn.setFixedSize(34, 28)
        pdf_btn.clicked.connect(self.export_to_pdf)
        self.toolbar.addWidget(pdf_btn)

        # --- Fullscreen toggle ---
        self.fullscreen_btn = QToolButton()
        self.fullscreen_btn.setText("FS")
        self.fullscreen_btn.setToolTip("Toggle Fullscreen (F11)")
        self.fullscreen_btn.setFixedSize(30, 28)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.toolbar.addWidget(self.fullscreen_btn)

    def _update_color_btn_icon(self, color):
        pixmap = QPixmap(20, 20)
        pixmap.fill(color)
        self.color_btn.setIcon(QIcon(pixmap))

    def set_canvas_tool(self, tool_mode):
        for mode, action in self.tool_actions.items():
            action.setChecked(mode == tool_mode)
        self.canvas.set_tool(tool_mode)

    def choose_color(self):
        color = QColorDialog.getColor(self.canvas.pen_color, self, "Select draw color")
        if color.isValid():
            self.canvas.pen_color = color
            self.canvas.highlighter_color = QColor(color.red(), color.green(), color.blue(), 100)
            self._update_color_btn_icon(color)

    def change_pen_size(self, size):
        self.canvas.pen_width = size
        self.canvas.highlighter_width = max(size * 4, 8)
        self.canvas.eraser_width = max(size * 5, 10)

    def change_text_size(self, size):
        self.canvas.text_size = size

    def toggle_handwriting(self, checked):
        self.canvas.handwriting_enabled = checked
        if checked:
            self.handwriting_btn.setStyleSheet("background-color: rgba(0, 255, 100, 0.25); border: 1px solid #00ff66; border-radius: 4px; color: #00ff66; font-weight: bold;")
        else:
            self.handwriting_btn.setStyleSheet("")

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
            self.fullscreen_btn.setToolTip("Toggle Fullscreen (F11)")
        else:
            self._saved_geometry = self.geometry()
            self.showFullScreen()
            self.is_fullscreen = True
            self.fullscreen_btn.setToolTip("Exit Fullscreen (F11)")

    # --- Canvas Type Switching ---
    def on_canvas_type_changed(self, type_text):
        type_map = {
            "Canvas": config.CANVAS_PLAIN,
            "HTML": config.CANVAS_HTML,
            "Compiler": config.CANVAS_COMPILER,
            "Browser": config.CANVAS_BROWSER,
        }
        mode = type_map.get(type_text, config.CANVAS_PLAIN)

        if not self.page_manager.active_page:
            return

        self.page_manager.active_page.meta["canvas_type"] = mode
        self.canvas.current_canvas_type = mode

        if mode == config.CANVAS_PLAIN:
            self.stack.setCurrentWidget(self.canvas)
            self.canvas.update_overlay_visibility()
            self._cleanup_embedded_widgets()
        else:
            self._show_embedded_widget(mode)

        self.canvas_type_combo.blockSignals(True)
        self.canvas_type_combo.setCurrentText(type_text)
        self.canvas_type_combo.blockSignals(False)

    def _show_embedded_widget(self, mode):
        page = self.page_manager.active_page
        if not page:
            return

        self._cleanup_embedded_widgets()

        if mode == config.CANVAS_HTML:
            self.embedded_html = HTMLRenderWidget(page.meta.get("html_code", ""))
            self.embedded_html.html_changed.connect(lambda html: page.meta.update({"html_code": html}))
            self.stack.addWidget(self.embedded_html)
            self.current_embedded_index = self.stack.indexOf(self.embedded_html)
            self.stack.setCurrentIndex(self.current_embedded_index)

        elif mode == config.CANVAS_COMPILER:
            self.embedded_compiler = CompilerWidget(
                page.meta.get("compiled_code", ""),
                page.meta.get("compiler_lang", "Python")
            )
            self.embedded_compiler.code_changed.connect(
                lambda code, lang: page.meta.update({"compiled_code": code, "compiler_lang": lang})
            )
            self.stack.addWidget(self.embedded_compiler)
            self.current_embedded_index = self.stack.indexOf(self.embedded_compiler)
            self.stack.setCurrentIndex(self.current_embedded_index)

        elif mode == config.CANVAS_BROWSER:
            self.embedded_browser = BrowserWidget(page.meta.get("live_url", "https://www.google.com"))
            self.embedded_browser.url_changed.connect(lambda url: page.meta.update({"live_url": url}))
            self.stack.addWidget(self.embedded_browser)
            self.current_embedded_index = self.stack.indexOf(self.embedded_browser)
            self.stack.setCurrentIndex(self.current_embedded_index)

    def _cleanup_embedded_widgets(self):
        for attr in ['embedded_html', 'embedded_compiler', 'embedded_browser']:
            widget = getattr(self, attr, None)
            if widget:
                idx = self.stack.indexOf(widget)
                if idx >= 0:
                    self.stack.removeWidget(widget)
                widget.deleteLater()
                setattr(self, attr, None)
        self.current_embedded_index = None

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        style = Themes.get_style(theme_name)
        self.setStyleSheet(style)

        if theme_name == "Light Glass":
            self.canvas.canvas_bg_color = QColor("#fafafa")
            self.canvas.grid_color = QColor("#e0e0ea")
            self.canvas.pen_color = QColor("#0066cc")
        elif theme_name == "Slate":
            self.canvas.canvas_bg_color = QColor("#0f172a")
            self.canvas.grid_color = QColor("#1e293b")
            self.canvas.pen_color = QColor("#38bdf8")
        else:
            self.canvas.canvas_bg_color = QColor("#121214")
            self.canvas.grid_color = QColor("#1b1b1f")
            self.canvas.pen_color = QColor("#00ffcc")

        self.canvas.update_background()
        self.canvas.viewport().update()
        self._update_color_btn_icon(self.canvas.pen_color)

    def create_shortcuts(self):
        QShortcut(QKeySequence('V'), self, lambda: self.set_canvas_tool(config.MODE_SELECT))
        QShortcut(QKeySequence('P'), self, lambda: self.set_canvas_tool(config.MODE_PEN))
        QShortcut(QKeySequence('H'), self, lambda: self.set_canvas_tool(config.MODE_HIGHLIGHTER))
        QShortcut(QKeySequence('L'), self, lambda: self.set_canvas_tool(config.MODE_LINE))
        QShortcut(QKeySequence('R'), self, lambda: self.set_canvas_tool(config.MODE_RECT))
        QShortcut(QKeySequence('C'), self, lambda: self.set_canvas_tool(config.MODE_CIRCLE))
        QShortcut(QKeySequence('T'), self, lambda: self.set_canvas_tool(config.MODE_TEXT))
        QShortcut(QKeySequence('E'), self, lambda: self.set_canvas_tool(config.MODE_ERASER))
        QShortcut(QKeySequence('Ctrl+Z'), self, self.canvas.undo)
        QShortcut(QKeySequence('Ctrl+Y'), self, self.canvas.redo)
        QShortcut(QKeySequence('Ctrl+G'), self, lambda: self.toggle_grid())
        QShortcut(QKeySequence('Ctrl+T'), self, self.cycle_theme)
        QShortcut(QKeySequence('F11'), self, self.toggle_fullscreen)
        QShortcut(QKeySequence('Ctrl+E'), self, self.export_to_pdf)

    def cycle_theme(self):
        themes = ["Dark Glass", "Light Glass", "Slate"]
        try:
            idx = themes.index(self.current_theme)
            next_theme = themes[(idx + 1) % len(themes)]
        except ValueError:
            next_theme = themes[0]
        self.theme_combo.setCurrentText(next_theme)

    def export_to_pdf(self):
        scopes = ["Current Canvas", "All Slides"]
        scope, ok = QInputDialog.getItem(self, "Export PDF", "Select export scope:", scopes, 0, False)
        if not ok:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return

        temp_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "temp_pdf_images")
        os.makedirs(temp_dir, exist_ok=True)
        image_paths = []

        try:
            if scope == "Current Canvas":
                # Show canvas for capture
                self.stack.setCurrentWidget(self.canvas)
                QApplication.processEvents()
                pixmap = self.canvas.grab()
                img_path = os.path.join(temp_dir, "current.png")
                pixmap.save(img_path, "PNG")
                image_paths.append(img_path)
            else:
                original_index = self.stack.currentIndex()
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

                # Restore
                if self.page_manager.active_page:
                    self.canvas.set_page_node(self.page_manager.active_page)
                    active_type = self.page_manager.active_page.meta.get("canvas_type", config.CANVAS_PLAIN)
                    if active_type != config.CANVAS_PLAIN:
                        self._show_embedded_widget(active_type)
                    else:
                        self.stack.setCurrentWidget(self.canvas)
                    QApplication.processEvents()

            export_images_to_pdf(image_paths, file_path)
            QMessageBox.information(self, "Export Complete", f"PDF saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{str(e)}")
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

    # --- Sidebar Signals ---
    def on_page_selected(self, page_id):
        node = self.page_manager.find_node_by_id(page_id)
        if node:
            self.page_manager.active_page = node
            self.canvas.set_page_node(node)

            canvas_type = node.meta.get("canvas_type", config.CANVAS_PLAIN)
            type_reverse = {
                config.CANVAS_PLAIN: "Canvas",
                config.CANVAS_HTML: "HTML",
                config.CANVAS_COMPILER: "Compiler",
                config.CANVAS_BROWSER: "Browser",
            }
            self.canvas_type_combo.blockSignals(True)
            self.canvas_type_combo.setCurrentText(type_reverse.get(canvas_type, "Canvas"))
            self.canvas_type_combo.blockSignals(False)

            if canvas_type == config.CANVAS_PLAIN:
                self.stack.setCurrentWidget(self.canvas)
                self._cleanup_embedded_widgets()
            else:
                self._show_embedded_widget(canvas_type)

    def on_delete_page_requested(self, page_id):
        all_nodes = self.page_manager.get_all_nodes_flat()
        if len(all_nodes) <= 1:
            QMessageBox.warning(self, "Action Prevented", "You must keep at least one page.")
            return

        reply = QMessageBox.question(
            self, "Delete Slide",
            "Delete selected slide? This will remove all subtopics as well.",
            QMessageBox.Yes | QMessageBox.No
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
