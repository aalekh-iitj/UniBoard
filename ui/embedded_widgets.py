from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QPlainTextEdit, QTextEdit, QLineEdit, QSplitter, QLabel, QFrame
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, Signal, QUrl, QThread
from PySide6.QtWebEngineWidgets import QWebEngineView

from core.compiler import CodeCompiler

EMBEDDED_WIDGET_STYLE = """
    QWidget {
        background-color: #121214;
        color: #e2e2e8;
    }
    QPushButton {
        background-color: rgba(45, 45, 55, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        color: #ffffff;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: rgba(65, 65, 80, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    QPushButton:pressed {
        background-color: rgba(138, 43, 226, 0.5);
    }
    QComboBox {
        background-color: rgba(30, 30, 38, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 5px;
        color: #d1d1d6;
        padding: 5px 10px;
        min-width: 80px;
    }
    QComboBox:hover {
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    QComboBox::drop-down {
        border: none;
        width: 22px;
    }
    QComboBox::down-arrow {
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #d1d1d6;
    }
    QComboBox QAbstractItemView {
        background-color: rgba(22, 22, 26, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #d1d1d6;
        selection-background-color: rgba(138, 43, 226, 0.4);
        selection-color: #ffffff;
    }
    QPlainTextEdit, QTextEdit {
        background-color: rgba(15, 15, 18, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 6px;
        color: #e2e2e8;
        padding: 8px;
    }
    QLineEdit {
        background-color: rgba(15, 15, 18, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        color: #e2e2e8;
        padding: 6px 10px;
        font-size: 13px;
    }
    QLineEdit:focus {
        border: 1px solid rgba(138, 43, 226, 0.8);
    }
    QLabel {
        color: #b0b0b8;
        font-size: 12px;
    }
    QSplitter::handle {
        background-color: rgba(255, 255, 255, 0.08);
        width: 3px;
        height: 3px;
    }
    QSplitter::handle:hover {
        background-color: rgba(138, 43, 226, 0.5);
    }
"""


class HTMLRenderWidget(QWidget):
    html_changed = Signal(str)

    def __init__(self, initial_html="", parent=None):
        super().__init__(parent)
        self.setStyleSheet(EMBEDDED_WIDGET_STYLE)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar with toggle
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 6, 8, 6)
        top_bar.setSpacing(8)

        lbl = QLabel("HTML / CSS Editor")
        lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #8a2be2;")
        top_bar.addWidget(lbl)

        top_bar.addStretch()

        self.render_btn = QPushButton("Render HTML")
        self.render_btn.clicked.connect(self.apply_html)
        top_bar.addWidget(self.render_btn)

        self.toggle_btn = QPushButton("Show Editor")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.toggled.connect(self.toggle_editor)
        top_bar.addWidget(self.toggle_btn)

        main_layout.addLayout(top_bar)

        # Splitter
        self.splitter = QSplitter(Qt.Vertical)

        # Web view
        self.web_view = QWebEngineView()
        self.web_view.setHtml(initial_html if initial_html else "<html><body style='background:#121214;display:flex;align-items:center;justify-content:center;height:100vh;margin:0'><p style='color:#666;font-family:sans-serif'>Enter HTML code and click Render</p></body></html>")
        self.splitter.addWidget(self.web_view)

        # Editor panel
        self.editor_panel = QWidget()
        editor_layout = QVBoxLayout(self.editor_panel)
        editor_layout.setContentsMargins(8, 8, 8, 8)
        editor_layout.setSpacing(6)

        editor_lbl = QLabel("HTML / CSS Source Code:")
        editor_lbl.setStyleSheet("font-weight: bold; color: #8a2be2;")
        editor_layout.addWidget(editor_lbl)

        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setPlainText(initial_html)
        editor_layout.addWidget(self.editor)

        self.splitter.addWidget(self.editor_panel)
        self.splitter.setSizes([500, 250])
        self.splitter.setCollapsible(1, True)

        main_layout.addWidget(self.splitter)
        self.editor_panel.setVisible(False)

    def toggle_editor(self, visible):
        self.editor_panel.setVisible(visible)
        self.toggle_btn.setText("Hide Editor" if visible else "Show Editor")
        if visible:
            self.splitter.setSizes([400, 250])

    def apply_html(self):
        html_code = self.editor.toPlainText()
        self.web_view.setHtml(html_code)
        self.html_changed.emit(html_code)

    def set_html(self, html_code):
        self.editor.setPlainText(html_code)
        self.web_view.setHtml(html_code)


class CompilerWidget(QWidget):
    code_changed = Signal(str, str)

    def __init__(self, initial_code="", initial_lang="Python", parent=None):
        super().__init__(parent)
        self.setStyleSheet(EMBEDDED_WIDGET_STYLE)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Controls bar
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        lang_lbl = QLabel("Language:")
        controls_layout.addWidget(lang_lbl)

        self.lang_box = QComboBox()
        self.lang_box.addItems(["Python", "JavaScript"])
        self.lang_box.setCurrentText(initial_lang)
        self.lang_box.currentTextChanged.connect(self.on_lang_changed)
        controls_layout.addWidget(self.lang_box)

        controls_layout.addSpacing(10)

        self.run_btn = QPushButton("Run Code")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 170, 102, 0.8);
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 20px;
            }
            QPushButton:hover { background-color: rgba(0, 200, 130, 0.9); }
            QPushButton:disabled { background-color: rgba(80, 80, 80, 0.5); color: #888; }
        """)
        self.run_btn.clicked.connect(self.run_code)
        controls_layout.addWidget(self.run_btn)

        controls_layout.addStretch()

        clear_btn = QPushButton("Clear Output")
        clear_btn.setStyleSheet("padding: 5px 12px; font-size: 11px;")
        clear_btn.clicked.connect(lambda: self.console.clear())
        controls_layout.addWidget(clear_btn)

        main_layout.addLayout(controls_layout)

        # Splitter: editor + console
        self.splitter = QSplitter(Qt.Vertical)

        # Code editor
        editor_frame = QFrame()
        editor_frame.setStyleSheet("QFrame { border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; }")
        ef_layout = QVBoxLayout(editor_frame)
        ef_layout.setContentsMargins(6, 6, 6, 6)
        ef_layout.setSpacing(4)

        ed_lbl = QLabel("Source Code:")
        ed_lbl.setStyleSheet("font-weight: bold; color: #8a2be2; font-size: 11px;")
        ef_layout.addWidget(ed_lbl)

        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setPlainText(initial_code)
        self.editor.textChanged.connect(self.on_text_changed)
        ef_layout.addWidget(self.editor)

        self.splitter.addWidget(editor_frame)

        # Console output
        console_frame = QFrame()
        console_frame.setStyleSheet("QFrame { border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; }")
        cf_layout = QVBoxLayout(console_frame)
        cf_layout.setContentsMargins(6, 6, 6, 6)
        cf_layout.setSpacing(4)

        con_lbl = QLabel("Console Output:")
        con_lbl.setStyleSheet("font-weight: bold; color: #8a2be2; font-size: 11px;")
        cf_layout.addWidget(con_lbl)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 11))
        self.console.setStyleSheet("background-color: #08080a; color: #00ff66; border: 1px solid rgba(255,255,255,0.04); border-radius: 4px;")
        cf_layout.addWidget(self.console)

        self.splitter.addWidget(console_frame)
        self.splitter.setSizes([300, 200])

        main_layout.addWidget(self.splitter)

    def on_lang_changed(self, lang):
        self.on_text_changed()

    def on_text_changed(self):
        self.code_changed.emit(self.editor.toPlainText(), self.lang_box.currentText())

    def run_code(self):
        lang = self.lang_box.currentText().lower()
        code = self.editor.toPlainText()
        self.console.setText("[Executing...]")
        self.run_btn.setEnabled(False)

        class RunThread(QThread):
            finished = Signal(str, str, int)
            def __init__(self, c, l):
                super().__init__()
                self.c = c
                self.l = l
            def run(self):
                o, e, r = CodeCompiler.run_code(self.c, self.l)
                self.finished.emit(o, e, r)

        self.runner = RunThread(code, lang)
        self.runner.finished.connect(self.on_run_finished)
        self.runner.start()

    def on_run_finished(self, stdout, stderr, code):
        self.run_btn.setEnabled(True)
        self.console.clear()
        if stdout:
            self.console.setTextColor(QColor("#00ff66"))
            self.console.append(stdout)
        if stderr:
            self.console.setTextColor(QColor("#ff3333"))
            self.console.append(stderr)
        if not stdout and not stderr:
            self.console.setTextColor(QColor("#ffffff"))
            self.console.append(f"[Finished with exit code {code}]")

    def set_content(self, code, lang):
        self.editor.blockSignals(True)
        self.editor.setPlainText(code)
        self.editor.blockSignals(False)
        self.lang_box.setCurrentText(lang)


class BrowserWidget(QWidget):
    url_changed = Signal(str)

    def __init__(self, initial_url="https://www.google.com", parent=None):
        super().__init__(parent)
        self.setStyleSheet(EMBEDDED_WIDGET_STYLE)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Navigation bar
        nav_bar = QHBoxLayout()
        nav_bar.setContentsMargins(8, 6, 8, 6)
        nav_bar.setSpacing(6)

        self.back_btn = QPushButton("<")
        self.back_btn.setFixedWidth(32)
        self.back_btn.clicked.connect(self.navigate_back)
        nav_bar.addWidget(self.back_btn)

        self.forward_btn = QPushButton(">")
        self.forward_btn.setFixedWidth(32)
        self.forward_btn.clicked.connect(self.navigate_forward)
        nav_bar.addWidget(self.forward_btn)

        self.reload_btn = QPushButton("Refresh")
        self.reload_btn.setFixedWidth(60)
        self.reload_btn.clicked.connect(self.navigate_reload)
        nav_bar.addWidget(self.reload_btn)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL...")
        self.url_bar.setText(initial_url)
        self.url_bar.returnPressed.connect(self.load_url)
        nav_bar.addWidget(self.url_bar)

        self.go_btn = QPushButton("Go")
        self.go_btn.setFixedWidth(45)
        self.go_btn.clicked.connect(self.load_url)
        nav_bar.addWidget(self.go_btn)

        main_layout.addLayout(nav_bar)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: rgba(255,255,255,0.08); max-height: 1px;")
        main_layout.addWidget(sep)

        # WebEngine Browser View
        self.web_view = QWebEngineView()
        self.web_view.load(QUrl(initial_url))
        self.web_view.urlChanged.connect(self.on_url_loaded)
        main_layout.addWidget(self.web_view)

    def load_url(self):
        url_text = self.url_bar.text().strip()
        if not url_text:
            return
        if not url_text.startswith("http://") and not url_text.startswith("https://"):
            url_text = "https://" + url_text
        self.web_view.load(QUrl(url_text))

    def navigate_back(self):
        self.web_view.back()

    def navigate_forward(self):
        self.web_view.forward()

    def navigate_reload(self):
        self.web_view.reload()

    def on_url_loaded(self, qurl):
        self.url_bar.setText(qurl.toString())
        self.url_changed.emit(qurl.toString())

    def set_url(self, url):
        self.url_bar.setText(url)
        self.web_view.load(QUrl(url))
