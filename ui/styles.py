"""
Premium Glassmorphic Theme System for UniBoard.

Provides three polished themes — DARK_GLASS, LIGHT_GLASS, and SLATE —
each styling every major Qt widget with consistent, modern aesthetics.
"""


class Themes:
    """Central theme registry.  Access stylesheets via the class constants
    or dynamically through ``Themes.get_style(name)``."""

    # ------------------------------------------------------------------ #
    #  DARK GLASS — deep dark bg, neon-purple / cyan accents, glass panels
    # ------------------------------------------------------------------ #
    DARK_GLASS: str = """
        /* ===== Base Window ===== */
        QMainWindow {
            background-color: #0d0d11;
        }

        QWidget#centralWidget {
            background-color: #0d0d11;
        }

        /* ===== Dock Widgets ===== */
        QDockWidget {
            color: #e0e0e0;
            font-weight: 600;
            font-size: 13px;
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
            border: 1px solid rgba(138, 43, 226, 0.25);
            border-radius: 10px;
        }

        QDockWidget::title {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(138, 43, 226, 0.18),
                stop:1 rgba(0, 229, 255, 0.10));
            border: 1px solid rgba(138, 43, 226, 0.30);
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding: 8px 12px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        }

        /* ===== Toolbar ===== */
        QToolBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(20, 20, 30, 0.92),
                stop:1 rgba(13, 13, 17, 0.96));
            border-bottom: 1px solid rgba(138, 43, 226, 0.22);
            padding: 4px 6px;
            spacing: 4px;
        }

        QToolButton {
            background: rgba(255, 255, 255, 0.04);
            color: #d0d0d8;
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 6px;
            padding: 6px 8px;
            font-size: 13px;
            font-weight: 500;
        }

        QToolButton:hover {
            background: rgba(138, 43, 226, 0.22);
            border: 1px solid rgba(138, 43, 226, 0.45);
            color: #ffffff;
        }

        QToolButton:checked {
            background: rgba(138, 43, 226, 0.35);
            border: 1px solid rgba(138, 43, 226, 0.60);
            color: #ffffff;
        }

        QToolButton:pressed {
            background: rgba(138, 43, 226, 0.50);
            border: 1px solid rgba(138, 43, 226, 0.70);
            color: #ffffff;
        }

        /* ===== Tree / List Views ===== */
        QTreeView, QListView {
            background: rgba(18, 18, 26, 0.90);
            color: #d0d0d8;
            border: 1px solid rgba(138, 43, 226, 0.15);
            border-radius: 8px;
            padding: 4px;
            outline: none;
            font-size: 13px;
        }

        QTreeView::item, QListView::item {
            padding: 5px 8px;
            border-radius: 5px;
            margin: 1px 2px;
        }

        QTreeView::item:hover, QListView::item:hover {
            background: rgba(138, 43, 226, 0.16);
            border: none;
        }

        QTreeView::item:selected, QListView::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(138, 43, 226, 0.40),
                stop:1 rgba(0, 229, 255, 0.20));
            color: #ffffff;
        }

        /* ===== Push Buttons ===== */
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(138, 43, 226, 0.30),
                stop:1 rgba(0, 229, 255, 0.15));
            color: #e8e8f0;
            border: 1px solid rgba(138, 43, 226, 0.35);
            border-radius: 7px;
            padding: 7px 18px;
            font-size: 13px;
            font-weight: 600;
        }

        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(138, 43, 226, 0.50),
                stop:1 rgba(0, 229, 255, 0.28));
            border: 1px solid rgba(138, 43, 226, 0.60);
            color: #ffffff;
        }

        QPushButton:pressed {
            background: rgba(138, 43, 226, 0.65);
            border: 1px solid rgba(138, 43, 226, 0.80);
        }

        /* ===== Text Inputs ===== */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background: rgba(18, 18, 28, 0.88);
            color: #e0e0e8;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 7px;
            padding: 6px 10px;
            font-size: 13px;
            selection-background-color: rgba(138, 43, 226, 0.45);
            selection-color: #ffffff;
        }

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 1px solid rgba(138, 43, 226, 0.55);
            background: rgba(22, 22, 34, 0.95);
        }

        /* ===== Scrollbars ===== */
        QScrollBar:vertical {
            background: rgba(13, 13, 17, 0.40);
            width: 8px;
            margin: 0;
            border-radius: 4px;
        }

        QScrollBar::handle:vertical {
            background: rgba(138, 43, 226, 0.40);
            min-height: 30px;
            border-radius: 4px;
        }

        QScrollBar::handle:vertical:hover {
            background: rgba(138, 43, 226, 0.60);
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
            height: 0px;
        }

        QScrollBar:horizontal {
            background: rgba(13, 13, 17, 0.40);
            height: 8px;
            margin: 0;
            border-radius: 4px;
        }

        QScrollBar::handle:horizontal {
            background: rgba(138, 43, 226, 0.40);
            min-width: 30px;
            border-radius: 4px;
        }

        QScrollBar::handle:horizontal:hover {
            background: rgba(138, 43, 226, 0.60);
        }

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
            width: 0px;
        }

        /* ===== Labels ===== */
        QLabel {
            color: #d0d0d8;
            font-size: 13px;
            background: transparent;
        }

        /* ===== ComboBox ===== */
        QComboBox {
            background: rgba(18, 18, 28, 0.88);
            color: #e0e0e8;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 7px;
            padding: 5px 10px;
            font-size: 13px;
            min-height: 22px;
        }

        QComboBox:hover {
            border: 1px solid rgba(138, 43, 226, 0.45);
        }

        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 28px;
            border-left: 1px solid rgba(255, 255, 255, 0.08);
            border-top-right-radius: 7px;
            border-bottom-right-radius: 7px;
            background: rgba(138, 43, 226, 0.12);
        }

        QComboBox::down-arrow {
            image: none;
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #b0b0c0;
            margin-top: 2px;
        }

        QComboBox QAbstractItemView {
            background: rgba(20, 20, 30, 0.96);
            color: #e0e0e8;
            border: 1px solid rgba(138, 43, 226, 0.30);
            border-radius: 6px;
            padding: 4px;
            selection-background-color: rgba(138, 43, 226, 0.40);
            selection-color: #ffffff;
            outline: none;
        }

        /* ===== SpinBox ===== */
        QSpinBox {
            background: rgba(18, 18, 28, 0.88);
            color: #e0e0e8;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 7px;
            padding: 4px 8px;
            font-size: 13px;
            min-height: 22px;
        }

        QSpinBox:focus {
            border: 1px solid rgba(138, 43, 226, 0.55);
        }

        QSpinBox::up-button {
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 22px;
            border-left: 1px solid rgba(255, 255, 255, 0.06);
            border-top-right-radius: 7px;
            background: rgba(138, 43, 226, 0.10);
        }

        QSpinBox::up-button:hover {
            background: rgba(138, 43, 226, 0.30);
        }

        QSpinBox::up-arrow {
            image: none;
            width: 0; height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid #b0b0c0;
        }

        QSpinBox::down-button {
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 22px;
            border-left: 1px solid rgba(255, 255, 255, 0.06);
            border-bottom-right-radius: 7px;
            background: rgba(138, 43, 226, 0.10);
        }

        QSpinBox::down-button:hover {
            background: rgba(138, 43, 226, 0.30);
        }

        QSpinBox::down-arrow {
            image: none;
            width: 0; height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #b0b0c0;
        }

        /* ===== Tab Widget ===== */
        QTabWidget {
            background: transparent;
            border: none;
        }

        QTabWidget::pane {
            background: rgba(18, 18, 26, 0.85);
            border: 1px solid rgba(138, 43, 226, 0.18);
            border-radius: 8px;
            margin-top: -1px;
        }

        QTabBar::tab {
            background: rgba(255, 255, 255, 0.04);
            color: #a0a0b0;
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-bottom: none;
            padding: 7px 18px;
            margin-right: 2px;
            border-top-left-radius: 7px;
            border-top-right-radius: 7px;
            font-size: 12px;
            font-weight: 500;
        }

        QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(138, 43, 226, 0.30),
                stop:1 rgba(18, 18, 26, 0.90));
            color: #ffffff;
            border: 1px solid rgba(138, 43, 226, 0.40);
            border-bottom: none;
        }

        QTabBar::tab:hover {
            background: rgba(138, 43, 226, 0.16);
            color: #e0e0e8;
        }

        /* ===== Splitter ===== */
        QSplitter::handle {
            background: rgba(138, 43, 226, 0.18);
            border-radius: 2px;
        }

        QSplitter::handle:horizontal {
            width: 3px;
            margin: 4px 0;
        }

        QSplitter::handle:vertical {
            height: 3px;
            margin: 0 4px;
        }

        QSplitter::handle:hover {
            background: rgba(138, 43, 226, 0.50);
        }

        /* ===== Glass Panel ===== */
        QFrame#glassPanel {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(138, 43, 226, 0.08),
                stop:0.5 rgba(0, 229, 255, 0.04),
                stop:1 rgba(138, 43, 226, 0.06));
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
        }

        /* ===== Menu Bar ===== */
        QMenuBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(20, 20, 30, 0.94),
                stop:1 rgba(13, 13, 17, 0.98));
            color: #c8c8d4;
            border-bottom: 1px solid rgba(138, 43, 226, 0.18);
            padding: 2px 4px;
            font-size: 13px;
        }

        QMenuBar::item {
            background: transparent;
            color: #c8c8d4;
            padding: 6px 12px;
            border-radius: 5px;
            margin: 1px 2px;
        }

        QMenuBar::item:selected {
            background: rgba(138, 43, 226, 0.28);
            color: #ffffff;
        }

        QMenuBar::item:pressed {
            background: rgba(138, 43, 226, 0.45);
        }

        /* ===== Status Bar ===== */
        QStatusBar {
            background: rgba(13, 13, 17, 0.95);
            color: #8a8a9a;
            border-top: 1px solid rgba(138, 43, 226, 0.15);
            font-size: 12px;
            padding: 2px 8px;
        }

        QStatusBar::item {
            border: none;
        }
    """

    # ------------------------------------------------------------------ #
    #  LIGHT GLASS — frosted-white bg, blue accent, soft shadows
    # ------------------------------------------------------------------ #
    LIGHT_GLASS: str = """
        /* ===== Base Window ===== */
        QMainWindow {
            background-color: #f5f5fa;
        }

        QWidget#centralWidget {
            background-color: #f5f5fa;
        }

        /* ===== Dock Widgets ===== */
        QDockWidget {
            color: #2a2a3a;
            font-weight: 600;
            font-size: 13px;
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
            border: 1px solid rgba(0, 102, 255, 0.15);
            border-radius: 10px;
        }

        QDockWidget::title {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(255, 255, 255, 0.95),
                stop:1 rgba(0, 102, 255, 0.06));
            border: 1px solid rgba(0, 0, 0, 0.07);
            border-bottom: 1px solid rgba(0, 0, 0, 0.04);
            padding: 8px 12px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        }

        /* ===== Toolbar ===== */
        QToolBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.98),
                stop:1 rgba(245, 245, 250, 0.96));
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            padding: 4px 6px;
            spacing: 4px;
        }

        QToolButton {
            background: rgba(0, 0, 0, 0.03);
            color: #3a3a4a;
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 6px;
            padding: 6px 8px;
            font-size: 13px;
            font-weight: 500;
        }

        QToolButton:hover {
            background: rgba(0, 102, 255, 0.10);
            border: 1px solid rgba(0, 102, 255, 0.25);
            color: #0055dd;
        }

        QToolButton:checked {
            background: rgba(0, 102, 255, 0.18);
            border: 1px solid rgba(0, 102, 255, 0.35);
            color: #0044bb;
        }

        QToolButton:pressed {
            background: rgba(0, 102, 255, 0.28);
            border: 1px solid rgba(0, 102, 255, 0.45);
            color: #003399;
        }

        /* ===== Tree / List Views ===== */
        QTreeView, QListView {
            background: rgba(255, 255, 255, 0.92);
            color: #2a2a3a;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 8px;
            padding: 4px;
            outline: none;
            font-size: 13px;
        }

        QTreeView::item, QListView::item {
            padding: 5px 8px;
            border-radius: 5px;
            margin: 1px 2px;
        }

        QTreeView::item:hover, QListView::item:hover {
            background: rgba(0, 102, 255, 0.08);
        }

        QTreeView::item:selected, QListView::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(0, 102, 255, 0.22),
                stop:1 rgba(0, 102, 255, 0.12));
            color: #0044bb;
        }

        /* ===== Push Buttons ===== */
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0066ff,
                stop:1 #0055dd);
            color: #ffffff;
            border: 1px solid rgba(0, 80, 200, 0.30);
            border-radius: 7px;
            padding: 7px 18px;
            font-size: 13px;
            font-weight: 600;
        }

        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1a7aff,
                stop:1 #0066ff);
            border: 1px solid rgba(0, 80, 200, 0.50);
        }

        QPushButton:pressed {
            background: #0044bb;
            border: 1px solid rgba(0, 60, 160, 0.60);
        }

        /* ===== Text Inputs ===== */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background: rgba(255, 255, 255, 0.95);
            color: #2a2a3a;
            border: 1px solid rgba(0, 0, 0, 0.10);
            border-radius: 7px;
            padding: 6px 10px;
            font-size: 13px;
            selection-background-color: rgba(0, 102, 255, 0.25);
            selection-color: #002266;
        }

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 1px solid rgba(0, 102, 255, 0.45);
            background: #ffffff;
        }

        /* ===== Scrollbars ===== */
        QScrollBar:vertical {
            background: rgba(0, 0, 0, 0.03);
            width: 8px;
            margin: 0;
            border-radius: 4px;
        }

        QScrollBar::handle:vertical {
            background: rgba(0, 0, 0, 0.15);
            min-height: 30px;
            border-radius: 4px;
        }

        QScrollBar::handle:vertical:hover {
            background: rgba(0, 102, 255, 0.35);
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
            height: 0px;
        }

        QScrollBar:horizontal {
            background: rgba(0, 0, 0, 0.03);
            height: 8px;
            margin: 0;
            border-radius: 4px;
        }

        QScrollBar::handle:horizontal {
            background: rgba(0, 0, 0, 0.15);
            min-width: 30px;
            border-radius: 4px;
        }

        QScrollBar::handle:horizontal:hover {
            background: rgba(0, 102, 255, 0.35);
        }

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
            width: 0px;
        }

        /* ===== Labels ===== */
        QLabel {
            color: #2a2a3a;
            font-size: 13px;
            background: transparent;
        }

        /* ===== ComboBox ===== */
        QComboBox {
            background: rgba(255, 255, 255, 0.95);
            color: #2a2a3a;
            border: 1px solid rgba(0, 0, 0, 0.10);
            border-radius: 7px;
            padding: 5px 10px;
            font-size: 13px;
            min-height: 22px;
        }

        QComboBox:hover {
            border: 1px solid rgba(0, 102, 255, 0.35);
        }

        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 28px;
            border-left: 1px solid rgba(0, 0, 0, 0.08);
            border-top-right-radius: 7px;
            border-bottom-right-radius: 7px;
            background: rgba(0, 102, 255, 0.06);
        }

        QComboBox::down-arrow {
            image: none;
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #6a6a7a;
            margin-top: 2px;
        }

        QComboBox QAbstractItemView {
            background: rgba(255, 255, 255, 0.98);
            color: #2a2a3a;
            border: 1px solid rgba(0, 0, 0, 0.10);
            border-radius: 6px;
            padding: 4px;
            selection-background-color: rgba(0, 102, 255, 0.18);
            selection-color: #0044bb;
            outline: none;
        }

        /* ===== SpinBox ===== */
        QSpinBox {
            background: rgba(255, 255, 255, 0.95);
            color: #2a2a3a;
            border: 1px solid rgba(0, 0, 0, 0.10);
            border-radius: 7px;
            padding: 4px 8px;
            font-size: 13px;
            min-height: 22px;
        }

        QSpinBox:focus {
            border: 1px solid rgba(0, 102, 255, 0.45);
        }

        QSpinBox::up-button {
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 22px;
            border-left: 1px solid rgba(0, 0, 0, 0.06);
            border-top-right-radius: 7px;
            background: rgba(0, 102, 255, 0.05);
        }

        QSpinBox::up-button:hover {
            background: rgba(0, 102, 255, 0.15);
        }

        QSpinBox::up-arrow {
            image: none;
            width: 0; height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid #6a6a7a;
        }

        QSpinBox::down-button {
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 22px;
            border-left: 1px solid rgba(0, 0, 0, 0.06);
            border-bottom-right-radius: 7px;
            background: rgba(0, 102, 255, 0.05);
        }

        QSpinBox::down-button:hover {
            background: rgba(0, 102, 255, 0.15);
        }

        QSpinBox::down-arrow {
            image: none;
            width: 0; height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #6a6a7a;
        }

        /* ===== Tab Widget ===== */
        QTabWidget {
            background: transparent;
            border: none;
        }

        QTabWidget::pane {
            background: rgba(255, 255, 255, 0.90);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 8px;
            margin-top: -1px;
        }

        QTabBar::tab {
            background: rgba(0, 0, 0, 0.03);
            color: #6a6a7a;
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-bottom: none;
            padding: 7px 18px;
            margin-right: 2px;
            border-top-left-radius: 7px;
            border-top-right-radius: 7px;
            font-size: 12px;
            font-weight: 500;
        }

        QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ffffff,
                stop:1 rgba(255, 255, 255, 0.92));
            color: #0055dd;
            border: 1px solid rgba(0, 102, 255, 0.20);
            border-bottom: none;
        }

        QTabBar::tab:hover {
            background: rgba(0, 102, 255, 0.06);
            color: #0066ff;
        }

        /* ===== Splitter ===== */
        QSplitter::handle {
            background: rgba(0, 0, 0, 0.06);
            border-radius: 2px;
        }

        QSplitter::handle:horizontal {
            width: 3px;
            margin: 4px 0;
        }

        QSplitter::handle:vertical {
            height: 3px;
            margin: 0 4px;
        }

        QSplitter::handle:hover {
            background: rgba(0, 102, 255, 0.30);
        }

        /* ===== Glass Panel ===== */
        QFrame#glassPanel {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(255, 255, 255, 0.80),
                stop:0.5 rgba(245, 245, 255, 0.70),
                stop:1 rgba(255, 255, 255, 0.75));
            border: 1px solid rgba(255, 255, 255, 0.60);
            border-radius: 12px;
        }

        /* ===== Menu Bar ===== */
        QMenuBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.98),
                stop:1 rgba(245, 245, 250, 0.96));
            color: #3a3a4a;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            padding: 2px 4px;
            font-size: 13px;
        }

        QMenuBar::item {
            background: transparent;
            color: #3a3a4a;
            padding: 6px 12px;
            border-radius: 5px;
            margin: 1px 2px;
        }

        QMenuBar::item:selected {
            background: rgba(0, 102, 255, 0.12);
            color: #0055dd;
        }

        QMenuBar::item:pressed {
            background: rgba(0, 102, 255, 0.22);
        }

        /* ===== Status Bar ===== */
        QStatusBar {
            background: rgba(255, 255, 255, 0.96);
            color: #6a6a7a;
            border-top: 1px solid rgba(0, 0, 0, 0.06);
            font-size: 12px;
            padding: 2px 8px;
        }

        QStatusBar::item {
            border: none;
        }
    """

    # ------------------------------------------------------------------ #
    #  SLATE — navy-dark bg, electric-blue accent, sharp & minimal
    # ------------------------------------------------------------------ #
    SLATE: str = """
        /* ===== Base Window ===== */
        QMainWindow {
            background-color: #0f172a;
        }

        QWidget#centralWidget {
            background-color: #0f172a;
        }

        /* ===== Dock Widgets ===== */
        QDockWidget {
            color: #cbd5e1;
            font-weight: 600;
            font-size: 13px;
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
            border: 1px solid rgba(59, 130, 246, 0.20);
            border-radius: 8px;
        }

        QDockWidget::title {
            background: #1e293b;
            border: 1px solid rgba(59, 130, 246, 0.18);
            border-bottom: 1px solid #1e293b;
            padding: 8px 12px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }

        /* ===== Toolbar ===== */
        QToolBar {
            background: #1e293b;
            border-bottom: 1px solid rgba(59, 130, 246, 0.15);
            padding: 4px 6px;
            spacing: 4px;
        }

        QToolButton {
            background: rgba(255, 255, 255, 0.04);
            color: #94a3b8;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            padding: 6px 8px;
            font-size: 13px;
            font-weight: 500;
        }

        QToolButton:hover {
            background: rgba(59, 130, 246, 0.18);
            border: 1px solid rgba(59, 130, 246, 0.35);
            color: #e2e8f0;
        }

        QToolButton:checked {
            background: rgba(59, 130, 246, 0.28);
            border: 1px solid rgba(59, 130, 246, 0.50);
            color: #ffffff;
        }

        QToolButton:pressed {
            background: rgba(59, 130, 246, 0.40);
            border: 1px solid rgba(59, 130, 246, 0.60);
            color: #ffffff;
        }

        /* ===== Tree / List Views ===== */
        QTreeView, QListView {
            background: #1e293b;
            color: #cbd5e1;
            border: 1px solid rgba(59, 130, 246, 0.12);
            border-radius: 6px;
            padding: 4px;
            outline: none;
            font-size: 13px;
        }

        QTreeView::item, QListView::item {
            padding: 5px 8px;
            border-radius: 4px;
            margin: 1px 2px;
        }

        QTreeView::item:hover, QListView::item:hover {
            background: rgba(59, 130, 246, 0.12);
        }

        QTreeView::item:selected, QListView::item:selected {
            background: rgba(59, 130, 246, 0.28);
            color: #ffffff;
        }

        /* ===== Push Buttons ===== */
        QPushButton {
            background: #3b82f6;
            color: #ffffff;
            border: 1px solid #2563eb;
            border-radius: 6px;
            padding: 7px 18px;
            font-size: 13px;
            font-weight: 600;
        }

        QPushButton:hover {
            background: #60a5fa;
            border: 1px solid #3b82f6;
        }

        QPushButton:pressed {
            background: #2563eb;
            border: 1px solid #1d4ed8;
        }

        /* ===== Text Inputs ===== */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background: #1e293b;
            color: #e2e8f0;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 13px;
            selection-background-color: rgba(59, 130, 246, 0.40);
            selection-color: #ffffff;
        }

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 1px solid rgba(59, 130, 246, 0.55);
            background: #1a2540;
        }

        /* ===== Scrollbars ===== */
        QScrollBar:vertical {
            background: rgba(15, 23, 42, 0.50);
            width: 8px;
            margin: 0;
            border-radius: 4px;
        }

        QScrollBar::handle:vertical {
            background: rgba(59, 130, 246, 0.35);
            min-height: 30px;
            border-radius: 4px;
        }

        QScrollBar::handle:vertical:hover {
            background: rgba(59, 130, 246, 0.55);
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
            height: 0px;
        }

        QScrollBar:horizontal {
            background: rgba(15, 23, 42, 0.50);
            height: 8px;
            margin: 0;
            border-radius: 4px;
        }

        QScrollBar::handle:horizontal {
            background: rgba(59, 130, 246, 0.35);
            min-width: 30px;
            border-radius: 4px;
        }

        QScrollBar::handle:horizontal:hover {
            background: rgba(59, 130, 246, 0.55);
        }

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
            width: 0px;
        }

        /* ===== Labels ===== */
        QLabel {
            color: #cbd5e1;
            font-size: 13px;
            background: transparent;
        }

        /* ===== ComboBox ===== */
        QComboBox {
            background: #1e293b;
            color: #e2e8f0;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 13px;
            min-height: 22px;
        }

        QComboBox:hover {
            border: 1px solid rgba(59, 130, 246, 0.40);
        }

        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 28px;
            border-left: 1px solid rgba(255, 255, 255, 0.06);
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            background: rgba(59, 130, 246, 0.10);
        }

        QComboBox::down-arrow {
            image: none;
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #94a3b8;
            margin-top: 2px;
        }

        QComboBox QAbstractItemView {
            background: #1e293b;
            color: #e2e8f0;
            border: 1px solid rgba(59, 130, 246, 0.25);
            border-radius: 6px;
            padding: 4px;
            selection-background-color: rgba(59, 130, 246, 0.30);
            selection-color: #ffffff;
            outline: none;
        }

        /* ===== SpinBox ===== */
        QSpinBox {
            background: #1e293b;
            color: #e2e8f0;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 13px;
            min-height: 22px;
        }

        QSpinBox:focus {
            border: 1px solid rgba(59, 130, 246, 0.55);
        }

        QSpinBox::up-button {
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 22px;
            border-left: 1px solid rgba(255, 255, 255, 0.06);
            border-top-right-radius: 6px;
            background: rgba(59, 130, 246, 0.08);
        }

        QSpinBox::up-button:hover {
            background: rgba(59, 130, 246, 0.25);
        }

        QSpinBox::up-arrow {
            image: none;
            width: 0; height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid #94a3b8;
        }

        QSpinBox::down-button {
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 22px;
            border-left: 1px solid rgba(255, 255, 255, 0.06);
            border-bottom-right-radius: 6px;
            background: rgba(59, 130, 246, 0.08);
        }

        QSpinBox::down-button:hover {
            background: rgba(59, 130, 246, 0.25);
        }

        QSpinBox::down-arrow {
            image: none;
            width: 0; height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #94a3b8;
        }

        /* ===== Tab Widget ===== */
        QTabWidget {
            background: transparent;
            border: none;
        }

        QTabWidget::pane {
            background: #1e293b;
            border: 1px solid rgba(59, 130, 246, 0.12);
            border-radius: 6px;
            margin-top: -1px;
        }

        QTabBar::tab {
            background: rgba(255, 255, 255, 0.03);
            color: #94a3b8;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-bottom: none;
            padding: 7px 18px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-size: 12px;
            font-weight: 500;
        }

        QTabBar::tab:selected {
            background: #1e293b;
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.30);
            border-bottom: 1px solid #1e293b;
        }

        QTabBar::tab:hover {
            background: rgba(59, 130, 246, 0.10);
            color: #e2e8f0;
        }

        /* ===== Splitter ===== */
        QSplitter::handle {
            background: rgba(59, 130, 246, 0.12);
            border-radius: 1px;
        }

        QSplitter::handle:horizontal {
            width: 2px;
            margin: 4px 0;
        }

        QSplitter::handle:vertical {
            height: 2px;
            margin: 0 4px;
        }

        QSplitter::handle:hover {
            background: rgba(59, 130, 246, 0.45);
        }

        /* ===== Glass Panel ===== */
        QFrame#glassPanel {
            background: #1e293b;
            border: 1px solid rgba(59, 130, 246, 0.15);
            border-radius: 10px;
        }

        /* ===== Menu Bar ===== */
        QMenuBar {
            background: #1e293b;
            color: #94a3b8;
            border-bottom: 1px solid rgba(59, 130, 246, 0.12);
            padding: 2px 4px;
            font-size: 13px;
        }

        QMenuBar::item {
            background: transparent;
            color: #94a3b8;
            padding: 6px 12px;
            border-radius: 4px;
            margin: 1px 2px;
        }

        QMenuBar::item:selected {
            background: rgba(59, 130, 246, 0.20);
            color: #e2e8f0;
        }

        QMenuBar::item:pressed {
            background: rgba(59, 130, 246, 0.35);
        }

        /* ===== Status Bar ===== */
        QStatusBar {
            background: #0f172a;
            color: #64748b;
            border-top: 1px solid rgba(59, 130, 246, 0.10);
            font-size: 12px;
            padding: 2px 8px;
        }

        QStatusBar::item {
            border: none;
        }
    """

    # ------------------------------------------------------------------ #
    #  Theme look-up helper
    # ------------------------------------------------------------------ #
    _REGISTRY: dict[str, str] = {
        "dark_glass": DARK_GLASS,
        "light_glass": LIGHT_GLASS,
        "slate": SLATE,
    }

    @staticmethod
    def get_style(name: str) -> str:
        """Return the stylesheet for *name* (case-insensitive).

        Accepted values: ``"dark_glass"``, ``"light_glass"``, ``"slate"``.
        Falls back to DARK_GLASS if the name is unrecognised.
        """
        return Themes._REGISTRY.get(name.lower().strip(), Themes.DARK_GLASS)
