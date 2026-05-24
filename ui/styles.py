class Themes:
    DARK_GLASS = """
        /* Dark Glassmorphic Theme */
        QMainWindow {
            background-color: #121214;
        }
        
        QWidget#centralWidget {
            background-color: #121214;
        }

        QDockWidget {
            titlebar-close-icon: url(close.png);
            titlebar-normal-icon: url(undock.png);
            border: 0px;
        }

        QDockWidget::title {
            background: rgba(30, 30, 35, 0.8);
            padding: 6px;
            font-weight: bold;
            color: #e2e2e8;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }

        /* Glass Panel Widget */
        QFrame#glassPanel {
            background-color: rgba(22, 22, 26, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
        }

        /* Toolbars and Menus */
        QToolBar {
            background-color: rgba(22, 22, 26, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 4px;
            margin: 4px;
            spacing: 8px;
        }

        QToolButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 5px;
            color: #d1d1d6;
        }

        QToolButton:hover {
            background-color: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
        }

        QToolButton:checked {
            background-color: rgba(138, 43, 226, 0.35); /* Neon Purple Accent */
            border: 1px solid rgba(138, 43, 226, 0.8);
            color: #ffffff;
        }

        /* Sidebar lists and trees */
        QTreeView, QListView {
            background-color: rgba(20, 20, 25, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            color: #e2e2e8;
            padding: 5px;
        }

        QTreeView::item, QListView::item {
            padding: 6px;
            border-radius: 4px;
        }

        QTreeView::item:hover, QListView::item:hover {
            background-color: rgba(255, 255, 255, 0.04);
        }

        QTreeView::item:selected, QListView::item:selected {
            background-color: rgba(138, 43, 226, 0.25);
            color: #ffffff;
            border: 1px solid rgba(138, 43, 226, 0.5);
        }

        /* Buttons & Inputs */
        QPushButton {
            background-color: rgba(45, 45, 55, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            color: #ffffff;
            padding: 6px 12px;
            font-size: 12px;
        }

        QPushButton:hover {
            background-color: rgba(65, 65, 80, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        QPushButton:pressed {
            background-color: rgba(138, 43, 226, 0.5);
        }

        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: rgba(15, 15, 18, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            color: #e2e2e8;
            padding: 6px;
        }

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 1px solid rgba(138, 43, 226, 0.8);
        }

        /* Canvas Scrollbars */
        QScrollBar:vertical {
            border: none;
            background: rgba(0, 0, 0, 0.05);
            width: 10px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background: rgba(255, 255, 255, 0.15);
            min-height: 20px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        QScrollBar:horizontal {
            border: none;
            background: rgba(0, 0, 0, 0.05);
            height: 10px;
            margin: 0px;
        }

        QScrollBar::handle:horizontal {
            background: rgba(255, 255, 255, 0.15);
            min-width: 20px;
            border-radius: 5px;
        }

        QScrollBar::handle:horizontal:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        QLabel {
            color: #d1d1d6;
        }
    """

    LIGHT_GLASS = """
        /* Light Glassmorphic Theme */
        QMainWindow {
            background-color: #f0f0f5;
        }

        QWidget#centralWidget {
            background-color: #f0f0f5;
        }

        QDockWidget::title {
            background: rgba(255, 255, 255, 0.8);
            padding: 6px;
            font-weight: bold;
            color: #333333;
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }

        QToolBar {
            background-color: rgba(255, 255, 255, 0.85);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 10px;
            padding: 4px;
            margin: 4px;
            spacing: 8px;
        }

        QToolButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 5px;
            color: #333333;
        }

        QToolButton:hover {
            background-color: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.1);
        }

        QToolButton:checked {
            background-color: rgba(0, 122, 255, 0.2); /* iOS Blue Accent */
            border: 1px solid rgba(0, 122, 255, 0.8);
            color: #000000;
        }

        QTreeView, QListView {
            background-color: rgba(255, 255, 255, 0.6);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 8px;
            color: #333333;
            padding: 5px;
        }

        QTreeView::item:hover, QListView::item:hover {
            background-color: rgba(0, 0, 0, 0.03);
        }

        QTreeView::item:selected, QListView::item:selected {
            background-color: rgba(0, 122, 255, 0.15);
            color: #000000;
            border: 1px solid rgba(0, 122, 255, 0.4);
        }

        QPushButton {
            background-color: rgba(240, 240, 245, 0.9);
            border: 1px solid rgba(0, 0, 0, 0.15);
            border-radius: 6px;
            color: #333333;
            padding: 6px 12px;
        }

        QPushButton:hover {
            background-color: rgba(220, 220, 230, 0.9);
            border: 1px solid rgba(0, 0, 0, 0.25);
        }

        QPushButton:pressed {
            background-color: rgba(0, 122, 255, 0.3);
        }

        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 6px;
            color: #333333;
            padding: 6px;
        }

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 1px solid rgba(0, 122, 255, 0.8);
        }

        QLabel {
            color: #333333;
        }
    """

    SLATE = """
        /* Slate Clean Minimalist Theme */
        QMainWindow {
            background-color: #1e293b;
        }

        QWidget#centralWidget {
            background-color: #1e293b;
        }

        QDockWidget::title {
            background: #0f172a;
            padding: 6px;
            font-weight: bold;
            color: #94a3b8;
            border-bottom: 2px solid #334155;
        }

        QToolBar {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 0px;
            padding: 4px;
            margin: 0px;
        }

        QToolButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 5px;
            color: #94a3b8;
        }

        QToolButton:hover {
            background-color: #1e293b;
            color: #f8fafc;
        }

        QToolButton:checked {
            background-color: #3b82f6; /* Slate Blue */
            color: #ffffff;
            border-radius: 4px;
        }

        QTreeView, QListView {
            background-color: #0f172a;
            border: 1px solid #334155;
            color: #cbd5e1;
            padding: 4px;
        }

        QTreeView::item:selected, QListView::item:selected {
            background-color: #3b82f6;
            color: #ffffff;
        }

        QPushButton {
            background-color: #334155;
            border: 1px solid #475569;
            color: #f8fafc;
            border-radius: 4px;
            padding: 6px 12px;
        }

        QPushButton:hover {
            background-color: #475569;
        }

        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 4px;
            color: #cbd5e1;
        }

        QLabel {
            color: #94a3b8;
        }
    """

    @staticmethod
    def get_style(name):
        styles = {
            "Dark Glass": Themes.DARK_GLASS,
            "Light Glass": Themes.LIGHT_GLASS,
            "Slate": Themes.SLATE
        }
        return styles.get(name, Themes.DARK_GLASS)
