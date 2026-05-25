from PySide6.QtGui import QShortcut
from PySide6.QtGui import QAction, QColor, QIcon, QFont, QKeySequence
from PySide6.QtPrintSupport import QPrinter
from utils.pdf_export import export_images_to_pdf
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QDockWidget, QToolBar, QToolButton, QLabel, QComboBox, QSpinBox, QColorDialog, QFileDialog, QMessageBox, QInputDialog

import os
import config
from core.page_manager import PageManager
from ui.canvas import WhiteboardCanvas
from ui.sidebar import SidebarWidget
from ui.styles import Themes

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.APP_NAME} - Creative Desktop Whiteboard")
        self.setObjectName("centralWidget")
        
        # 1. Screen size calculation (Set default window to 90% of total screen size)
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.9)
        height = int(screen.height() * 0.9)
        self.resize(width, height)
        
        # Center the window on the screen
        x = int((screen.width() - width) / 2)
        y = int((screen.height() - height) / 2)
        self.move(x, y)
        
        # Initialize Core Page Manager
        self.page_manager = PageManager()
        
        # Central Canvas Widget
        self.canvas = WhiteboardCanvas(self)
        self.setCentralWidget(self.canvas)
        
        # Setup Widgets & Docks (Note: Compiler Right dock removed)
        self.setup_docks()
        self.setup_toolbar()
        
        # Load the default node into the canvas
        if self.page_manager.active_page:
            self.canvas.set_page_node(self.page_manager.active_page)

        # Apply initial theme (default: Dark Glassmorphic)
        self.current_theme = "Dark Glass"
        self.apply_theme(self.current_theme)
        self.create_shortcuts()

    def setup_docks(self):
        # Left Dock: Slide Tree Page Manager
        self.left_dock = QDockWidget("Outline Manager", self)
        self.left_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.sidebar_widget = SidebarWidget(self.page_manager, self)
        self.left_dock.setWidget(self.sidebar_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)

        # Connect Sidebar signals
        self.sidebar_widget.page_selected.connect(self.on_page_selected)
        self.sidebar_widget.delete_page_requested.connect(self.on_delete_page_requested)
        self.sidebar_widget.rename_page_requested.connect(self.on_rename_page_requested)

    def setup_toolbar(self):
        self.toolbar = QToolBar("Main Controls")
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Drawing Modes
        self.tool_actions = {}
        tools = [
            ("Select Mode", config.MODE_SELECT, "📍"),
            ("Pen Draw", config.MODE_PEN, "✏️"),
            ("Highlighter", config.MODE_HIGHLIGHTER, "🖍️"),
            ("Line", config.MODE_LINE, "📏"),
            ("Rectangle", config.MODE_RECT, "⬜"),
            ("Circle", config.MODE_CIRCLE, "⚪"),
            ("Text Box", config.MODE_TEXT, "🔤"),
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

        # Colors Selection
        self.color_btn = QToolButton()
        self.color_btn.setText("🎨 Brush Color")
        self.color_btn.clicked.connect(self.choose_color)
        self.toolbar.addWidget(self.color_btn)

        # Brush Size
        self.toolbar.addWidget(QLabel(" Size: "))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 50)
        self.size_spin.setValue(self.canvas.pen_width)
        self.size_spin.valueChanged.connect(self.change_pen_size)
        self.toolbar.addWidget(self.size_spin)

        self.toolbar.addSeparator()

        # Handwriting recognition toggles
        self.handwriting_btn = QToolButton()
        self.handwriting_btn.setText("✍️ Handwriting: OFF")
        self.handwriting_btn.setCheckable(True)
        self.handwriting_btn.clicked.connect(self.toggle_handwriting)
        self.toolbar.addWidget(self.handwriting_btn)

        # Undo / Redo
        self.undo_btn = QToolButton()
        self.undo_btn.setText("↩️ Undo")
        self.undo_btn.clicked.connect(self.canvas.undo)
        self.toolbar.addWidget(self.undo_btn)

        self.redo_btn = QToolButton()
        self.redo_btn.setText("↪️ Redo")
        self.redo_btn.clicked.connect(self.canvas.redo)
        self.toolbar.addWidget(self.redo_btn)

        self.toolbar.addSeparator()

        # Grid Toggle
        self.grid_btn = QToolButton()
        self.grid_btn.setText("🕸️ Grid: ON")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.clicked.connect(self.toggle_grid)
        self.toolbar.addWidget(self.grid_btn)

        # Theme Selector
        self.toolbar.addWidget(QLabel(" Theme: "))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Glass", "Light Glass", "Slate"])
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        self.toolbar.addWidget(self.theme_combo)
        # PDF Export
        self.pdf_btn = QToolButton()
        self.pdf_btn.setText("📄 Export PDF")
        self.pdf_btn.clicked.connect(self.export_to_pdf)
        self.toolbar.addWidget(self.pdf_btn)

    def set_canvas_tool(self, tool_mode):
        for mode, action in self.tool_actions.items():
            action.setChecked(mode == tool_mode)
        self.canvas.set_tool(tool_mode)

    def choose_color(self):
        color = QColorDialog.getColor(self.canvas.pen_color, self.canvas, "Select draw color")
        if color.isValid():
            self.canvas.pen_color = color
            self.canvas.highlighter_color = QColor(color.red(), color.green(), color.blue(), 100)

    def change_pen_size(self, size):
        self.canvas.pen_width = size
        self.canvas.highlighter_width = size * 4
        self.canvas.eraser_width = size * 5

    def toggle_handwriting(self, checked):
        self.canvas.handwriting_enabled = checked
        if checked:
            self.handwriting_btn.setText("✍️ Handwriting: ON")
            self.handwriting_btn.setStyleSheet("background-color: rgba(0, 255, 100, 0.2); border: 1px solid #00ff66;")
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
        
        # Color mapping overrides for drawing canvas
        if theme_name == "Light Glass":
            self.canvas.canvas_bg_color = QColor("#fafafa")
            self.canvas.grid_color = QColor("#e0e0ea")
            self.canvas.pen_color = QColor("#0066cc")
        elif theme_name == "Slate":
            self.canvas.canvas_bg_color = QColor("#0f172a")
            self.canvas.grid_color = QColor("#1e293b")
            self.canvas.pen_color = QColor("#38bdf8")
        else: # Dark Glass
            self.canvas.canvas_bg_color = QColor("#121214")
            self.canvas.grid_color = QColor("#1b1b1f")
            self.canvas.pen_color = QColor("#00ffcc")
            
        self.canvas.update_background()
        self.canvas.viewport().update()

    # --- Sidebar Signals & Actions ---
    def create_shortcuts(self):
        """Create keyboard shortcuts for common tools and actions."""
        # Shape tools shortcuts
        QShortcut(QKeySequence('R'), self, lambda: self.set_canvas_tool(config.MODE_RECT))
        QShortcut(QKeySequence('C'), self, lambda: self.set_canvas_tool(config.MODE_CIRCLE))
        QShortcut(QKeySequence('L'), self, lambda: self.set_canvas_tool(config.MODE_LINE))
        QShortcut(QKeySequence('E'), self, lambda: self.set_canvas_tool(config.MODE_ERASER))
        # Undo/Redo shortcuts
        QShortcut(QKeySequence('Ctrl+Z'), self, self.canvas.undo)
        QShortcut(QKeySequence('Ctrl+Y'), self, self.canvas.redo)
        # Grid toggle shortcut
        QShortcut(QKeySequence('Ctrl+G'), self, lambda: self.toggle_grid(not self.canvas.grid_visible))
        # Theme cycle shortcut (Ctrl+T)
        QShortcut(QKeySequence('Ctrl+T'), self, self.cycle_theme)

    def cycle_theme(self):
        """Cycle through available themes."""
        themes = ["Dark Glass", "Light Glass", "Slate"]
        try:
            idx = themes.index(self.current_theme)
            next_theme = themes[(idx + 1) % len(themes)]
        except ValueError:
            next_theme = themes[0]
        self.theme_combo.setCurrentText(next_theme)

    def export_to_pdf(self):
        """Export canvas as PDF. User can choose to export the current canvas or all slides."""
        # Choose scope
        scopes = ["Current Canvas", "All Slides"]
        scope, ok = QInputDialog.getItem(self, "Export PDF", "Select export scope:", scopes, 0, False)
        if not ok:
            return
        # Prompt for file path
        file_path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return
        # Prepare temporary directory for images
        temp_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "temp_pdf_images")
        os.makedirs(temp_dir, exist_ok=True)
        image_paths = []
        try:
            if scope == "Current Canvas":
                # Capture current view
                pixmap = self.canvas.grab()
                img_path = os.path.join(temp_dir, "current.png")
                pixmap.save(img_path, "PNG")
                image_paths.append(img_path)
            else:
                # Export all root pages
                original_node = self.canvas.active_node
                for page in self.page_manager.root_pages:
                    # Switch to page
                    self.canvas.set_page_node(page)
                    QApplication.processEvents()
                    pixmap = self.canvas.grab()
                    img_path = os.path.join(temp_dir, f"{page.id}.png")
                    pixmap.save(img_path, "PNG")
                    image_paths.append(img_path)
                # Restore original page
                if original_node:
                    self.canvas.set_page_node(original_node)
                    QApplication.processEvents()
            # Generate PDF using ReportLab
            export_images_to_pdf(image_paths, file_path)
            QMessageBox.information(self, "Export Complete", f"PDF saved to {file_path}")
        finally:
            # Clean up temporary images
            for p in image_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass


    def on_page_selected(self, page_id):
        node = self.page_manager.find_node_by_id(page_id)
        if node:
            # Set active
            self.page_manager.active_page = node
            # Reload page node details to canvas
            self.canvas.set_page_node(node)

    def on_delete_page_requested(self, page_id):
        all_nodes = self.page_manager.get_all_nodes_flat()
        if len(all_nodes) <= 1:
            QMessageBox.warning(self, "Action Prevented", "You must keep at least one page.")
            return

        reply = QMessageBox.question(self, "Delete Slide", "Delete selected topic slide? This will remove all child subtopics as well.", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.page_manager.delete_page(page_id)
            self.sidebar_widget.refresh_tree()
            if self.page_manager.active_page:
                self.canvas.set_page_node(self.page_manager.active_page)

    def on_rename_page_requested(self, page_id, new_title):
        node = self.page_manager.find_node_by_id(page_id)
        if node and new_title.strip():
            node.title = new_title.strip()
            self.sidebar_widget.refresh_tree()
            # If current active page name changes, update the title overlay
            if self.page_manager.active_page == node or (node.parent and self.page_manager.active_page == node.parent):
                self.canvas.refresh_agenda_overlay()
