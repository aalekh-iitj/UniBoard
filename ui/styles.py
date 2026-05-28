class Themes:
    DARK_GLASS = """
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
        QFrame#glassPanel {
            background-color: rgba(22, 22, 26, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
        }
        QToolBar {
            background-color: rgba(22, 22, 26, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 2px;
            margin: 2px;
            spacing: 4px;
        }
        QToolButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 5px;
            padding: 4px 6px;
            color: #d1d1d6;
            font-size: 13px;
        }
        QToolButton:hover {
            background-color: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
        }
        QToolButton:checked {
            background-color: rgba(138, 43, 226, 0.35);
            border: 1px solid rgba(138, 43, 226, 0.8);
            color: #ffffff;
        }
        QToolButton:disabled {
            color: rgba(255, 255, 255, 0.2);
        }
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
        QComboBox {
            background-color: rgba(30, 30, 38, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            color: #d1d1d6;
            padding: 4px 8px;
            min-width: 60px;
        }
        QComboBox:hover {
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #d1d1d6;
            margin-right: 6px;
        }
        QComboBox QAbstractItemView {
            background-color: rgba(22, 22, 26, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            color: #d1d1d6;
            selection-background-color: rgba(138, 43, 226, 0.4);
            selection-color: #ffffff;
            padding: 4px;
        }
        QSpinBox {
            background-color: rgba(30, 30, 38, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            color: #d1d1d6;
            padding: 3px 6px;
            min-width: 40px;
        }
        QSpinBox:hover {
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        QSpinBox:focus {
            border: 1px solid rgba(138, 43, 226, 0.8);
        }
        QSpinBox::up-button, QSpinBox::down-button {
            background-color: rgba(255, 255, 255, 0.05);
            border: none;
            width: 16px;
        }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        QSpinBox::up-arrow {
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 4px solid #d1d1d6;
        }
        QSpinBox::down-arrow {
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #d1d1d6;
        }
        QMenuBar {
            background-color: rgba(22, 22, 26, 0.85);
            color: #d1d1d6;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        QMenuBar::item {
            background: transparent;
            padding: 4px 10px;
            border-radius: 4px;
        }
        QMenuBar::item:selected {
            background-color: rgba(138, 43, 226, 0.25);
        }
        QMenu {
            background-color: rgba(22, 22, 26, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            color: #d1d1d6;
            padding: 4px;
        }
        QMenu::item {
            padding: 6px 20px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background-color: rgba(138, 43, 226, 0.3);
        }
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
        QSplitter::handle {
            background-color: rgba(255, 255, 255, 0.08);
        }
        QSplitter::handle:hover {
            background-color: rgba(138, 43, 226, 0.5);
        }
        QStackedWidget {
            background-color: transparent;
        }
        QToolTip {
            background-color: rgba(30, 30, 38, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 4px;
            color: #e2e2e8;
            padding: 4px 8px;
            font-size: 11px;
        }
    """

    LIGHT_GLASS = """
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
            background-color: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 8px;
            padding: 2px;
            margin: 2px;
            spacing: 4px;
        }
        QToolButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 5px;
            padding: 4px 6px;
            color: #333333;
            font-size: 13px;
        }
        QToolButton:hover {
            background-color: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.1);
        }
        QToolButton:checked {
            background-color: rgba(0, 122, 255, 0.2);
            border: 1px solid rgba(0, 122, 255, 0.8);
            color: #000000;
        }
        QToolButton:disabled {
            color: rgba(0, 0, 0, 0.2);
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
        QComboBox {
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(0, 0, 0, 0.12);
            border-radius: 5px;
            color: #333333;
            padding: 4px 8px;
            min-width: 60px;
        }
        QComboBox:hover {
            border: 1px solid rgba(0, 0, 0, 0.2);
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #333333;
            margin-right: 6px;
        }
        QComboBox QAbstractItemView {
            background-color: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(0, 0, 0, 0.12);
            border-radius: 6px;
            color: #333333;
            selection-background-color: rgba(0, 122, 255, 0.2);
            selection-color: #000000;
            padding: 4px;
        }
        QSpinBox {
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(0, 0, 0, 0.12);
            border-radius: 5px;
            color: #333333;
            padding: 3px 6px;
            min-width: 40px;
        }
        QSpinBox:hover {
            border: 1px solid rgba(0, 0, 0, 0.2);
        }
        QSpinBox:focus {
            border: 1px solid rgba(0, 122, 255, 0.8);
        }
        QSpinBox::up-button, QSpinBox::down-button {
            background-color: rgba(0, 0, 0, 0.05);
            border: none;
            width: 16px;
        }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background-color: rgba(0, 0, 0, 0.1);
        }
        QSpinBox::up-arrow {
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 4px solid #333333;
        }
        QSpinBox::down-arrow {
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #333333;
        }
        QMenuBar {
            background-color: rgba(255, 255, 255, 0.88);
            color: #333333;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
        }
        QMenuBar::item {
            background: transparent;
            padding: 4px 10px;
            border-radius: 4px;
        }
        QMenuBar::item:selected {
            background-color: rgba(0, 122, 255, 0.15);
        }
        QMenu {
            background-color: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 6px;
            color: #333333;
            padding: 4px;
        }
        QMenu::item {
            padding: 6px 20px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background-color: rgba(0, 122, 255, 0.15);
        }
        QLabel {
            color: #333333;
        }
        QSplitter::handle {
            background-color: rgba(0, 0, 0, 0.08);
        }
        QSplitter::handle:hover {
            background-color: rgba(0, 122, 255, 0.4);
        }
        QStackedWidget {
            background-color: transparent;
        }
        QToolTip {
            background-color: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(0, 0, 0, 0.12);
            border-radius: 4px;
            color: #333333;
            padding: 4px 8px;
            font-size: 11px;
        }
    """

    SLATE = """
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
            border-radius: 6px;
            padding: 2px;
            margin: 2px;
            spacing: 4px;
        }
        QToolButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 4px 6px;
            color: #94a3b8;
            font-size: 13px;
        }
        QToolButton:hover {
            background-color: #1e293b;
            color: #f8fafc;
        }
        QToolButton:checked {
            background-color: #3b82f6;
            color: #ffffff;
            border-radius: 4px;
        }
        QToolButton:disabled {
            color: rgba(148, 163, 184, 0.3);
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
        QComboBox {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 4px;
            color: #cbd5e1;
            padding: 4px 8px;
            min-width: 60px;
        }
        QComboBox:hover {
            border: 1px solid #475569;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #cbd5e1;
            margin-right: 6px;
        }
        QComboBox QAbstractItemView {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 4px;
            color: #cbd5e1;
            selection-background-color: #3b82f6;
            selection-color: #ffffff;
            padding: 4px;
        }
        QSpinBox {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 4px;
            color: #cbd5e1;
            padding: 3px 6px;
            min-width: 40px;
        }
        QSpinBox:hover {
            border: 1px solid #475569;
        }
        QSpinBox:focus {
            border: 1px solid #3b82f6;
        }
        QSpinBox::up-button, QSpinBox::down-button {
            background-color: rgba(255, 255, 255, 0.05);
            border: none;
            width: 16px;
        }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        QSpinBox::up-arrow {
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 4px solid #cbd5e1;
        }
        QSpinBox::down-arrow {
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #cbd5e1;
        }
        QMenuBar {
            background-color: #0f172a;
            color: #94a3b8;
            border-bottom: 1px solid #334155;
        }
        QMenuBar::item {
            background: transparent;
            padding: 4px 10px;
            border-radius: 4px;
        }
        QMenuBar::item:selected {
            background-color: rgba(59, 130, 246, 0.2);
        }
        QMenu {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 4px;
            color: #cbd5e1;
            padding: 4px;
        }
        QMenu::item {
            padding: 6px 20px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background-color: rgba(59, 130, 246, 0.3);
        }
        QLabel {
            color: #94a3b8;
        }
        QSplitter::handle {
            background-color: #334155;
        }
        QSplitter::handle:hover {
            background-color: #3b82f6;
        }
        QStackedWidget {
            background-color: transparent;
        }
        QToolTip {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 4px;
            color: #f8fafc;
            padding: 4px 8px;
            font-size: 11px;
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
