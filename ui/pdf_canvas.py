import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QFrame, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

import config
from core.pdf_handler import PdfHandler
from ui.ppt_canvas import PptCanvasView, _BTN_PRIMARY, _BTN_SUBTLE, _NAV_LABEL


class PdfCanvasWidget(QWidget):
    """PDF viewer canvas with annotation overlay, navigation, and export."""

    pdf_loaded = Signal(str)
    page_changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_handler = PdfHandler()
        self.current_page_index = 0
        self.page_annotations = {}
        self._current_file_path = None
        self._render_dpi = 150

        self._build_ui()

    def set_theme(self, theme_name: str):
        """Update toolbar styles to match the selected theme."""
        if theme_name == "Light Glass":
            bg = "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255,255,255,0.98), stop:1 rgba(245,245,250,0.96));"
        elif theme_name == "Slate":
            bg = "background: #1e293b;"
        else:
            bg = "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(18, 18, 30, 230), stop:1 rgba(30, 30, 50, 210));"
        self._toolbar.setStyleSheet(f"""
            QFrame#pdfToolbar {{
                {bg}
                border-bottom: 1px solid rgba(99, 102, 241, 0.15);
            }}
        """)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top toolbar
        self._toolbar = QFrame(self)
        self._toolbar.setObjectName("pdfToolbar")
        self._toolbar.setStyleSheet("""
            QFrame#pdfToolbar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(18, 18, 30, 230), stop:1 rgba(30, 30, 50, 210));
                border-bottom: 1px solid rgba(99, 102, 241, 0.15);
            }
        """)
        tb_layout = QHBoxLayout(self._toolbar)
        tb_layout.setContentsMargins(14, 10, 14, 10)
        tb_layout.setSpacing(10)

        self.upload_btn = QPushButton("📂  Upload PDF")
        self.upload_btn.setStyleSheet(_BTN_PRIMARY)
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.clicked.connect(self.upload_pdf)
        tb_layout.addWidget(self.upload_btn)

        self.export_btn = QPushButton("💾  Export Annotated")
        self.export_btn.setStyleSheet(_BTN_SUBTLE)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_annotated)
        self.export_btn.setEnabled(False)
        tb_layout.addWidget(self.export_btn)

        self.persist_cb = QCheckBox("Persistent Annotations")
        self.persist_cb.setStyleSheet("""
            QCheckBox {
                color: #c4c4d8;
                font-size: 13px;
                font-weight: 500;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid rgba(99, 102, 241, 0.5);
                border-radius: 3px;
                background: rgba(10, 10, 18, 0.6);
            }
            QCheckBox::indicator:checked {
                background: rgba(99, 102, 241, 0.8);
                border: 2px solid rgba(99, 102, 241, 0.9);
            }
            QCheckBox::indicator:hover {
                border: 2px solid rgba(99, 102, 241, 0.8);
            }
        """)
        self.persist_cb.setChecked(False)
        tb_layout.addWidget(self.persist_cb)

        tb_layout.addStretch()

        self.file_label = QLabel("No PDF loaded")
        self.file_label.setStyleSheet("color: #94a3b8; font-size: 13px; padding: 0 8px;")
        tb_layout.addWidget(self.file_label)

        root.addWidget(toolbar)

        # Page view area
        self.page_view = PptCanvasView(self)
        root.addWidget(self.page_view, 1)

        # Bottom navigation bar
        nav_bar = QFrame(self)
        nav_bar.setObjectName("pdfNavBar")
        nav_bar.setStyleSheet("""
            QFrame#pdfNavBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(18, 18, 30, 230), stop:1 rgba(30, 30, 50, 210));
                border-top: 1px solid rgba(99, 102, 241, 0.15);
            }
        """)
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(14, 10, 14, 10)
        nav_layout.setSpacing(10)

        self.prev_btn = QPushButton("◀  Previous")
        self.prev_btn.setStyleSheet(_BTN_SUBTLE)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)

        self.page_counter = QLabel("Page 0 / 0")
        self.page_counter.setStyleSheet(_NAV_LABEL)
        nav_layout.addWidget(self.page_counter)

        self.next_btn = QPushButton("Next  ▶")
        self.next_btn.setStyleSheet(_BTN_SUBTLE)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)

        nav_layout.addStretch()

        go_label = QLabel("Go to:")
        go_label.setStyleSheet("color: #94a3b8; font-size: 13px;")
        nav_layout.addWidget(go_label)

        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 1)
        self.page_spin.setValue(1)
        self.page_spin.setFixedWidth(70)
        self.page_spin.setStyleSheet("""
            QSpinBox {
                background: rgba(10, 10, 18, 0.9);
                color: #e2e8f0;
                border: 1px solid rgba(99, 102, 241, 0.25);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
            }
            QSpinBox:focus {
                border: 1px solid rgba(99, 102, 241, 0.6);
            }
        """)
        self.page_spin.valueChanged.connect(self.go_to_page)
        nav_layout.addWidget(self.page_spin)

        root.addWidget(nav_bar)

    def upload_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF",
            "",
            "PDF Files (*.pdf);;All Files (*.*)"
        )
        if not file_path:
            return
        self._load_pdf(file_path)

    def _load_pdf(self, file_path):
        try:
            count = self.pdf_handler.load(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load PDF:\n{str(e)}")
            return

        self._current_file_path = file_path
        self.current_page_index = 0
        self.page_annotations.clear()
        self.page_view.undo_stack.clear()
        self.page_view.redo_stack.clear()

        self.file_label.setText(os.path.basename(file_path))
        self.page_spin.setRange(1, count)
        self.page_spin.setValue(1)
        self.export_btn.setEnabled(True)
        self._update_nav_buttons()
        self._show_page(0)
        self.pdf_loaded.emit(file_path)

    def _save_current_annotations(self):
        if self._current_file_path is None:
            return
        items = self.page_view.get_annotation_items()
        for item in items:
            self.page_view.scene().removeItem(item)
        self.page_annotations[self.current_page_index] = {
            "items": items,
            "undo": list(self.page_view.undo_stack),
            "redo": list(self.page_view.redo_stack),
        }

    def _load_annotations(self, index):
        self.page_view.clear_annotations()
        self.page_view.undo_stack.clear()
        self.page_view.redo_stack.clear()
        if index in self.page_annotations:
            data = self.page_annotations[index]
            self.page_view.load_annotation_items(data["items"])
            self.page_view.undo_stack = list(data.get("undo", []))
            self.page_view.redo_stack = list(data.get("redo", []))

    def _show_page(self, index):
        pixmap = self.pdf_handler.get_page_pixmap(index, self._render_dpi)
        if self.persist_cb.isChecked():
            self.page_view.set_slide_background(pixmap)
            self._load_annotations(index)
        else:
            self.page_view.set_slide_background(pixmap)
        self.page_counter.setText(f"Page {index + 1} / {self.pdf_handler.page_count}")
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(index + 1)
        self.page_spin.blockSignals(False)
        self._update_nav_buttons()
        self.page_changed.emit(index, self.pdf_handler.page_count)

    def _update_nav_buttons(self):
        total = self.pdf_handler.page_count
        cur = self.current_page_index
        self.prev_btn.setEnabled(cur > 0)
        self.next_btn.setEnabled(cur < total - 1)

    def next_page(self):
        if self.persist_cb.isChecked():
            self._save_current_annotations()
        if self.current_page_index < self.pdf_handler.page_count - 1:
            self.current_page_index += 1
            self._show_page(self.current_page_index)

    def prev_page(self):
        if self.persist_cb.isChecked():
            self._save_current_annotations()
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self._show_page(self.current_page_index)

    def go_to_page(self, page_num):
        target = page_num - 1
        if target == self.current_page_index:
            return
        if 0 <= target < self.pdf_handler.page_count:
            if self.persist_cb.isChecked():
                self._save_current_annotations()
            self.current_page_index = target
            self._show_page(target)

    def _re_add_current_annotations(self):
        if self.current_page_index in self.page_annotations:
            for item in self.page_annotations[self.current_page_index]["items"]:
                self.page_view.scene().addItem(item)

    def export_annotated(self):
        self._save_current_annotations()
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Annotated PDF",
            os.path.splitext(os.path.basename(self._current_file_path))[0] + "_annotated.pdf",
            "PDF Files (*.pdf)"
        )
        if not output_path:
            self._re_add_current_annotations()
            return

        try:
            annotation_map = {}
            for idx, data in self.page_annotations.items():
                items = data["items"]
                if items:
                    scene = QGraphicsScene()
                    for item in items:
                        scene.addItem(item)
                    annotation_map[idx] = scene

            success = self.pdf_handler.export_annotated_pdf(output_path, annotation_map)
            self._re_add_current_annotations()
            if success:
                QMessageBox.information(
                    self, "Export Complete",
                    f"Annotated PDF saved to:\n{output_path}"
                )
            else:
                QMessageBox.critical(self, "Export Error", "Failed to save annotated PDF.")
        except Exception as e:
            self._re_add_current_annotations()
            QMessageBox.critical(self, "Export Error", f"An error occurred:\n{str(e)}")

    def set_tool(self, tool_mode):
        self.page_view.set_tool(tool_mode)

    def set_pen_color(self, color):
        self.page_view.pen_color = color
        self.page_view.highlighter_color = QColor(color.red(), color.green(), color.blue(), 100)

    def set_pen_width(self, width):
        self.page_view.pen_width = width
        self.page_view.highlighter_width = max(width * 4, 8)
        self.page_view.eraser_width = max(width * 5, 10)

    def set_text_size(self, size):
        self.page_view.text_size = size

    def undo(self):
        self.page_view.undo()

    def redo(self):
        self.page_view.redo()
