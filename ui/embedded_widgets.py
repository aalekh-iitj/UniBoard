from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QPlainTextEdit, QTextEdit, QLineEdit, QSplitter, QLabel, QFrame
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView

from core.compiler import CodeCompiler

class HTMLRenderWidget(QWidget):
    html_changed = Signal(str)

    def __init__(self, initial_html="", parent=None):
        super().__init__(parent)
        self.resize(1100, 640)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)

        # Web view for rendering
        self.web_view = QWebEngineView()
        self.web_view.setHtml(initial_html)
        
        # Splitter to allow showing/hiding editor
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.web_view)
        
        # HTML Source editor panel
        self.editor_panel = QFrame()
        self.editor_panel.setObjectName("glassPanel")
        self.editor_panel.setStyleSheet("background-color: rgba(20, 20, 25, 0.95); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px;")
        editor_layout = QVBoxLayout(self.editor_panel)
        editor_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl = QLabel("HTML / CSS Editor:")
        lbl.setStyleSheet("color: #ffffff; font-weight: bold;")
        editor_layout.addWidget(lbl)
        
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 10))
        self.editor.setPlainText(initial_html)
        editor_layout.addWidget(self.editor)
        
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Render HTML")
        self.apply_btn.clicked.connect(self.apply_html)
        btn_layout.addWidget(self.apply_btn)
        
        self.close_editor_btn = QPushButton("Hide Editor")
        self.close_editor_btn.clicked.connect(self.toggle_editor)
        btn_layout.addWidget(self.close_editor_btn)
        editor_layout.addLayout(btn_layout)
        
        self.splitter.addWidget(self.editor_panel)
        self.splitter.setSizes([800, 300])
        self.layout.addWidget(self.splitter)
        
        # Floating top editor button
        self.edit_toggle_btn = QPushButton("✏️ Edit HTML", self.web_view)
        self.edit_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.edit_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(138, 43, 226, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: rgb(138, 43, 226);
            }
        """)
        self.edit_toggle_btn.clicked.connect(self.toggle_editor)
        self.edit_toggle_btn.move(10, 10)

        self.editor_panel.setVisible(False)  # Hidden by default for presenting

    def toggle_editor(self):
        is_visible = self.editor_panel.isVisible()
        self.editor_panel.setVisible(not is_visible)
        if not is_visible:
            self.splitter.setSizes([800, 300])

    def apply_html(self):
        html_code = self.editor.toPlainText()
        self.web_view.setHtml(html_code)
        self.html_changed.emit(html_code)

    def set_html(self, html_code):
        self.editor.setPlainText(html_code)
        self.web_view.setHtml(html_code)


class CompilerWidget(QWidget):
    code_changed = Signal(str, str)  # Emits (code, language)

    def __init__(self, initial_code="", initial_lang="Python", parent=None):
        super().__init__(parent)
        self.resize(1100, 640)
        self.setStyleSheet("background-color: #121214; color: #ffffff;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Editor controls bar
        controls_layout = QHBoxLayout()
        self.lang_box = QComboBox()
        self.lang_box.addItems(["Python", "JavaScript"])
        self.lang_box.setCurrentText(initial_lang)
        self.lang_box.currentTextChanged.connect(self.on_lang_changed)
        controls_layout.addWidget(self.lang_box)

        self.run_btn = QPushButton("⚡ Run Code")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #00aa66;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover { background-color: #00cc88; }
        """)
        self.run_btn.clicked.connect(self.run_code)
        controls_layout.addWidget(self.run_btn)
        
        controls_layout.addStretch()
        self.layout.addLayout(controls_layout)

        # Code editor & Console output splitter
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setPlainText(initial_code)
        self.editor.textChanged.connect(self.on_text_changed)
        self.splitter.addWidget(self.editor)
        
        # Console output
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(0, 0, 0, 0)
        
        console_hdr = QLabel("Console Output:")
        console_hdr.setStyleSheet("font-weight: bold; color: #aaaaaa;")
        console_layout.addWidget(console_hdr)
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 11))
        self.console.setStyleSheet("background-color: #08080a; color: #00ff66; border: 1px solid #22222b;")
        console_layout.addWidget(self.console)
        
        self.splitter.addWidget(console_widget)
        self.splitter.setSizes([600, 450])
        self.layout.addWidget(self.splitter)

    def on_lang_changed(self, lang):
        self.on_text_changed()

    def on_text_changed(self):
        self.code_changed.emit(self.editor.toPlainText(), self.lang_box.currentText())

    def run_code(self):
        lang = self.lang_box.currentText().lower()
        code = self.editor.toPlainText()
        self.console.setText("[Executing...]")
        self.run_btn.setEnabled(False)
        
        # Subprocess execution run inside QThread to prevent blockages
        from PySide6.QtCore import QThread
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
            self.console.append(f"[Finished with code {code}]")

    def set_content(self, code, lang):
        self.editor.blockSignals(True)
        self.editor.setPlainText(code)
        self.editor.blockSignals(False)
        self.lang_box.setCurrentText(lang)


class BrowserWidget(QWidget):
    url_changed = Signal(str)

    def __init__(self, initial_url="https://www.google.com", parent=None):
        super().__init__(parent)
        self.resize(1100, 640)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)

        # Nav bar
        nav_bar = QHBoxLayout()
        nav_bar.setContentsMargins(5, 5, 5, 5)
        nav_bar.setSpacing(6)
        
        self.back_btn = QPushButton("⬅️")
        self.back_btn.setFixedWidth(36)
        self.back_btn.clicked.connect(self.navigate_back)
        nav_bar.addWidget(self.back_btn)
        
        self.forward_btn = QPushButton("➡️")
        self.forward_btn.setFixedWidth(36)
        self.forward_btn.clicked.connect(self.navigate_forward)
        nav_bar.addWidget(self.forward_btn)
        
        self.reload_btn = QPushButton("🔄")
        self.reload_btn.setFixedWidth(36)
        self.reload_btn.clicked.connect(self.navigate_reload)
        nav_bar.addWidget(self.reload_btn)
        
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL here...")
        self.url_bar.setText(initial_url)
        self.url_bar.returnPressed.connect(self.load_url)
        nav_bar.addWidget(self.url_bar)
        
        self.go_btn = QPushButton("Go")
        self.go_btn.setFixedWidth(50)
        self.go_btn.clicked.connect(self.load_url)
        nav_bar.addWidget(self.go_btn)
        
        self.layout.addLayout(nav_bar)

        # WebEngine Browser View
        self.web_view = QWebEngineView()
        self.web_view.load(QUrl(initial_url))
        self.web_view.urlChanged.connect(self.on_url_loaded)
        self.layout.addWidget(self.web_view)

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
