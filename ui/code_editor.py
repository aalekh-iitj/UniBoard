from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QPlainTextEdit, QTextEdit, QLabel, QSplitter
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, Signal, QThread

from core.compiler import CodeCompiler

class CompilerWorker(QThread):
    finished = Signal(str, str, int)

    def __init__(self, code, language):
        super().__init__()
        self.code = code
        self.language = language

    def run(self):
        stdout, stderr, code = CodeCompiler.run_code(self.code, self.language)
        self.finished.emit(stdout, stderr, code)


class CodeEditorWidget(QWidget):
    # Signals
    render_html_requested = Signal(str)
    insert_to_canvas_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Header Label
        self.header_label = QLabel("Compiler & Sandbox")
        self.header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        self.layout.addWidget(self.header_label)

        # Language selection + Actions Bar
        top_bar = QHBoxLayout()
        self.lang_box = QComboBox()
        self.lang_box.addItems(["Python", "JavaScript", "HTML"])
        self.lang_box.currentTextChanged.connect(self.on_lang_changed)
        top_bar.addWidget(self.lang_box)

        self.run_btn = QPushButton("Run Script")
        self.run_btn.clicked.connect(self.run_code)
        top_bar.addWidget(self.run_btn)
        
        self.render_btn = QPushButton("Render HTML")
        self.render_btn.clicked.connect(self.render_html)
        self.render_btn.setVisible(False)  # Only visible when HTML selected
        top_bar.addWidget(self.render_btn)

        self.layout.addLayout(top_bar)

        # Splitter to divide code editor from console output
        self.splitter = QSplitter(Qt.Vertical)
        
        # Editor
        self.editor = QPlainTextEdit()
        mono_font = QFont("Consolas", 11)
        self.editor.setFont(mono_font)
        self.editor.setPlainText("# Write python code here\nprint('Hello UniBoard!')\n")
        self.splitter.addWidget(self.editor)
        
        # Console Output
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(0, 5, 0, 0)
        
        self.console_label = QLabel("Execution Output:")
        console_layout.addWidget(self.console_label)
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(mono_font)
        self.console.setStyleSheet("background-color: #0c0c0f; color: #00ff66;")
        console_layout.addWidget(self.console)
        
        # Buttons below console
        console_btns = QHBoxLayout()
        self.send_canvas_btn = QPushButton("Send Output to Whiteboard")
        self.send_canvas_btn.clicked.connect(self.send_output_to_canvas)
        console_btns.addWidget(self.send_canvas_btn)
        
        self.clear_console_btn = QPushButton("Clear Console")
        self.clear_console_btn.clicked.connect(self.console.clear)
        console_btns.addWidget(self.clear_console_btn)
        console_layout.addLayout(console_btns)

        self.splitter.addWidget(console_widget)
        
        # Keep splitter panels balanced
        self.splitter.setSizes([250, 150])
        self.layout.addWidget(self.splitter)

    def on_lang_changed(self, lang):
        if lang == "HTML":
            self.run_btn.setVisible(False)
            self.render_btn.setVisible(True)
            self.editor.setPlainText("<!-- Write HTML/CSS here -->\n<div style='background: linear-gradient(135deg, #12c2e9, #c471ed, #f64f59); padding: 30px; border-radius: 15px; color: white; font-family: sans-serif; text-align: center;'>\n  <h1>Welcome to UniBoard HTML Render</h1>\n  <p>Annotate directly over me!</p>\n</div>\n")
        else:
            self.run_btn.setVisible(True)
            self.render_btn.setVisible(False)
            if lang == "Python":
                self.editor.setPlainText("# Write python code here\nprint('Hello UniBoard!')\n")
            elif lang == "JavaScript":
                self.editor.setPlainText("// Write javascript code here\nconsole.log('Hello UniBoard JS!');\n")

    def run_code(self):
        lang = self.lang_box.currentText().lower()
        code = self.editor.toPlainText()
        self.console.setText("[Executing...]")
        self.run_btn.setEnabled(False)

        self.worker = CompilerWorker(code, lang)
        self.worker.finished.connect(self.on_execution_finished)
        self.worker.start()

    def on_execution_finished(self, stdout, stderr, exit_code):
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
            self.console.append(f"[Process finished with exit code {exit_code}]")

    def render_html(self):
        html_code = self.editor.toPlainText()
        self.render_html_requested.emit(html_code)

    def send_output_to_canvas(self):
        output_text = self.console.toPlainText()
        if output_text.strip():
            self.insert_to_canvas_requested.emit(output_text)
