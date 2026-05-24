from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QGraphicsTextItem,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

import config
from core.page_manager import PageManager
from ui.canvas import WhiteboardCanvas
from ui.code_editor import CodeEditorWidget
from ui.sidebar import SidebarWidget
from ui.styles import Themes


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.APP_NAME} - Whiteboard by Aalekh Rai")
        self.resize(1280, 800)
        self.setObjectName("centralWidget")

        # Initialize Core Page Manager
        self.page_manager = PageManager()

        # Central Canvas Widget
        self.canvas = WhiteboardCanvas(self)
        self.setCentralWidget(self.canvas)

        # Setup Widgets & Docks
        self.setup_docks()
        self.setup_toolbar()

        # Apply initial theme (default: Dark Glassmorphic)
        self.current_theme = "Dark Glass"
        self.apply_theme(self.current_theme)

    def setup_docks(self):
        # 1. Left Dock: Slide Tree Page Manager
        self.left_dock = QDockWidget("Page Outline", self)
        self.left_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.sidebar_widget = SidebarWidget(self.page_manager, self)
        self.left_dock.setWidget(self.sidebar_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)

        # Connect Sidebar signals
        self.sidebar_widget.page_selected.connect(self.on_page_selected)
        self.sidebar_widget.add_page_requested.connect(self.on_add_page_requested)
        self.sidebar_widget.delete_page_requested.connect(self.on_delete_page_requested)
        self.sidebar_widget.rename_page_requested.connect(self.on_rename_page_requested)

        # 2. Right Dock: Code Editor & Compiler
        self.right_dock = QDockWidget("Developer Compiler Sandbox", self)
        self.right_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.code_widget = CodeEditorWidget(self)
        self.right_dock.setWidget(self.code_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)

        # Connect Compiler Signals
        self.code_widget.insert_to_canvas_requested.connect(self.on_insert_code_output)
        self.code_widget.render_html_requested.connect(self.on_render_html_canvas)

    def setup_toolbar(self):
        self.toolbar = QToolBar("UniBoard Main Controls")
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # 1. Drawing Modes (Mutually Exclusive buttons)
        self.tool_actions = {}
        tools = [
            ("Select", config.MODE_SELECT, "📍"),
            ("Pen", config.MODE_PEN, "✏️"),
            ("Highlighter", config.MODE_HIGHLIGHTER, "🖍️"),
            ("Line", config.MODE_LINE, "📏"),
            ("Rectangle", config.MODE_RECT, "⬜"),
            ("Circle", config.MODE_CIRCLE, "⚪"),
            ("Text", config.MODE_TEXT, "🔤"),
            ("Eraser", config.MODE_ERASER, "🧹"),
        ]

        for name, mode, icon_symbol in tools:
            action = QAction(f"{icon_symbol} {name}", self)
            action.setCheckable(True)
            if mode == config.MODE_PEN:
                action.setChecked(True)
            action.triggered.connect(lambda checked, m=mode: self.set_canvas_tool(m))
            self.toolbar.addAction(action)
            self.tool_actions[mode] = action

        self.toolbar.addSeparator()

        # 2. Colors Selection
        self.color_btn = QToolButton()
        self.color_btn.setText("🎨 Color")
        self.color_btn.clicked.connect(self.choose_color)
        self.toolbar.addWidget(self.color_btn)

        # 3. Brush Size selector
        self.toolbar.addWidget(QLabel(" Size: "))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 50)
        self.size_spin.setValue(self.canvas.pen_width)
        self.size_spin.valueChanged.connect(self.change_pen_size)
        self.toolbar.addWidget(self.size_spin)

        self.toolbar.addSeparator()

        # 4. Handwriting Recognition Toggle
        self.handwriting_btn = QToolButton()
        self.handwriting_btn.setText("✍️ Handwriting: OFF")
        self.handwriting_btn.setCheckable(True)
        self.handwriting_btn.clicked.connect(self.toggle_handwriting)
        self.toolbar.addWidget(self.handwriting_btn)

        # 5. Undo / Redo
        self.undo_btn = QToolButton()
        self.undo_btn.setText("↩️ Undo")
        self.undo_btn.clicked.connect(self.canvas.undo)
        self.toolbar.addWidget(self.undo_btn)

        self.redo_btn = QToolButton()
        self.redo_btn.setText("↪️ Redo")
        self.redo_btn.clicked.connect(self.canvas.redo)
        self.toolbar.addWidget(self.redo_btn)

        self.toolbar.addSeparator()

        # 6. Grid Toggle
        self.grid_btn = QToolButton()
        self.grid_btn.setText("🕸️ Grid: ON")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.clicked.connect(self.toggle_grid)
        self.toolbar.addWidget(self.grid_btn)

        # 7. Theme Switcher Combo
        self.toolbar.addWidget(QLabel(" Theme: "))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Glass", "Light Glass", "Slate"])
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        self.toolbar.addWidget(self.theme_combo)

    def set_canvas_tool(self, tool_mode):
        # Uncheck other drawing mode actions
        for mode, action in self.tool_actions.items():
            action.setChecked(mode == tool_mode)

        self.canvas.set_tool(tool_mode)

    def choose_color(self):
        color = QColorDialog.getColor(
            self.canvas.pen_color, self.canvas, "Choose drawing color"
        )
        if color.isValid():
            self.canvas.pen_color = color
            # Auto convert highlighter color to semi-transparent version of same color
            self.canvas.highlighter_color = QColor(
                color.red(), color.green(), color.blue(), 100
            )

    def change_pen_size(self, size):
        self.canvas.pen_width = size
        self.canvas.highlighter_width = size * 4
        self.canvas.eraser_width = size * 5

    def toggle_handwriting(self, checked):
        self.canvas.handwriting_enabled = checked
        if checked:
            self.handwriting_btn.setText("✍️ Handwriting: ON")
            self.handwriting_btn.setStyleSheet(
                "background-color: rgba(0, 255, 100, 0.2); border: 1px solid #00ff66;"
            )
        else:
            self.handwriting_btn.setText("✍️ Handwriting: OFF")
            self.handwriting_btn.setStyleSheet("")

    def toggle_grid(self, checked):
        self.canvas.grid_visible = checked
        self.grid_btn.setText("🕸️ Grid: ON" if checked else "🕸️ Grid: OFF")
        self.canvas.viewport().update()

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        style = Themes.get_style(theme_name)
        self.setStyleSheet(style)

        # Map canvas colors
        if theme_name == "Light Glass":
            self.canvas.canvas_bg_color = QColor("#fafafa")
            self.canvas.grid_color = QColor("#e0e0ea")
            self.canvas.pen_color = QColor("#0066cc")
        elif theme_name == "Slate":
            self.canvas.canvas_bg_color = QColor("#0f172a")
            self.canvas.grid_color = QColor("#1e293b")
            self.canvas.pen_color = QColor("#38bdf8")
        else:  # Dark Glass
            self.canvas.canvas_bg_color = QColor("#121214")
            self.canvas.grid_color = QColor("#1b1b1f")
            self.canvas.pen_color = QColor("#00ffcc")

        self.canvas.update_background()
        self.canvas.viewport().update()

    # --- Page / Slide Management Operations ---
    def on_page_selected(self, page_id):
        # Save meta data of current active page node before switching
        if self.page_manager.active_page:
            self.page_manager.active_page.meta["compiled_code"] = (
                self.code_widget.editor.toPlainText()
            )
            self.page_manager.active_page.meta["compiler_lang"] = (
                self.code_widget.lang_box.currentText()
            )

        # Find target node
        node = self.page_manager.find_node_by_id(page_id)
        if node:
            self.page_manager.active_page = node
            # Set target scene to canvas
            self.canvas.set_page_scene(node.scene)

            # Load stored page editor configurations
            self.code_widget.lang_box.setCurrentText(node.meta["compiler_lang"])
            self.code_widget.editor.setPlainText(node.meta["compiled_code"])

    def on_add_page_requested(self, is_subpage):
        current_active = self.page_manager.active_page
        parent_id = (
            current_active.id
            if (is_subpage and current_active)
            else (
                current_active.parent.id
                if (current_active and current_active.parent)
                else None
            )
        )

        title, ok = QInputDialog.getText(self, "New Page", "Enter topic page title:")
        if ok and title.strip():
            new_node = self.page_manager.create_page(title.strip(), parent_id)
            self.page_manager.active_page = new_node
            self.sidebar_widget.refresh_tree()
            self.canvas.set_page_scene(new_node.scene)

    def on_delete_page_requested(self, page_id):
        # Don't delete if it's the last remaining page
        all_nodes = self.page_manager.get_all_nodes_flat()
        if len(all_nodes) <= 1:
            QMessageBox.warning(
                self, "Operation Denied", "At least one presentation page must remain."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this topic page?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.page_manager.delete_page(page_id)
            self.sidebar_widget.refresh_tree()
            # Set focus to active page
            if self.page_manager.active_page:
                self.canvas.set_page_scene(self.page_manager.active_page.scene)

    def on_rename_page_requested(self, page_id, new_title):
        node = self.page_manager.find_node_by_id(page_id)
        if node and new_title.strip():
            node.title = new_title.strip()
            self.sidebar_widget.refresh_tree()

    # --- Canvas Code integration Actions ---
    def on_insert_code_output(self, text):
        """Creates a movable text item containing execution output on the current canvas."""
        text_item = QGraphicsTextItem(text)
        text_item.setDefaultTextColor(
            QColor("#00ff66" if self.current_theme != "Light Glass" else "#008000")
        )
        text_item.setFont(QFont("Consolas", 12))
        text_item.setPos(50, 100)
        text_item.setFlag(QGraphicsTextItem.ItemIsMovable)
        text_item.setFlag(QGraphicsTextItem.ItemIsSelectable)
        self.canvas.scene().addItem(text_item)
        self.canvas.undo_stack.append(("add", text_item))

    def on_render_html_canvas(self, html_code):
        """Place HTML output details onto canvas (placeholder or raw code widget)."""
        QMessageBox.information(
            self,
            "HTML Snippet Received",
            "HTML layout parsed! Live browser render integration will display in the next stage.",
        )
