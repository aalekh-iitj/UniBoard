import os
import copy

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGraphicsView,
    QGraphicsScene, QGraphicsPathItem, QGraphicsRectItem, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QInputDialog, QFileDialog,
    QMessageBox, QFrame, QGraphicsItem, QGraphicsProxyWidget, QSizePolicy,
    QApplication, QCheckBox
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPainterPath, QFont, QCursor, QPixmap, QFontInfo
)
from PySide6.QtCore import Qt, QPointF, QRectF, QPoint, Signal, QTimer

import config
from core.ppt_handler import PptHandler
from ui.canvas import (
    MovablePathItem, ResizableRectItem, ResizableEllipseItem,
    ResizableLineItem, MovableTextItem
)

_BTN_PRIMARY = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(99, 102, 241, 0.85), stop:1 rgba(79, 70, 229, 0.90));
        color: #f0f0ff;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 7px 18px;
        font-weight: 600;
        font-size: 13px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(119, 122, 255, 0.95), stop:1 rgba(99, 90, 249, 1.0));
        border: 1px solid rgba(255,255,255,0.18);
    }
    QPushButton:pressed {
        background: rgba(67, 56, 202, 1.0);
    }
"""

_BTN_ACCENT = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(16, 185, 129, 0.85), stop:1 rgba(5, 150, 105, 0.90));
        color: #ecfdf5;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 7px 18px;
        font-weight: 600;
        font-size: 13px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(36, 205, 149, 0.95), stop:1 rgba(16, 170, 125, 1.0));
        border: 1px solid rgba(255,255,255,0.18);
    }
    QPushButton:pressed {
        background: rgba(4, 120, 87, 1.0);
    }
"""

_BTN_SUBTLE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(55, 55, 75, 0.7), stop:1 rgba(40, 40, 60, 0.8));
        color: #c4c4d8;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 8px;
        padding: 7px 18px;
        font-weight: 600;
        font-size: 13px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(70, 70, 95, 0.85), stop:1 rgba(55, 55, 75, 0.9));
        border: 1px solid rgba(255,255,255,0.18);
    }
    QPushButton:pressed {
        background: rgba(35, 35, 55, 1.0);
    }
"""

_NAV_LABEL = """
    QLabel {
        color: #c4c4d8;
        font-size: 14px;
        font-weight: 600;
        padding: 4px 12px;
        background: rgba(30, 30, 50, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 8px;
    }
"""


class PptCanvasView(QGraphicsView):
    """QGraphicsView that shows a PPT slide with annotation overlay."""

    stroke_drawn = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(
            QPainter.Antialiasing |
            QPainter.SmoothPixmapTransform |
            QPainter.TextAntialiasing
        )
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setAcceptDrops(False)
        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.NoDrag)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self.slide_pixmap = None
        self.slide_bg_item = None

        # Tool state (mirrors WhiteboardCanvas)
        self.current_tool = config.MODE_PEN
        self.pen_color = QColor("#00ffcc")
        self.pen_width = 3
        self.text_size = 16
        self.highlighter_color = QColor(255, 255, 0, 100)
        self.highlighter_width = 15
        self.eraser_width = 24

        # Interaction states
        self.is_drawing = False
        self.is_panning = False
        self.pan_start = None
        self.last_point = QPointF()
        self.current_item = None

        # Manual drag-state for Select tool
        self._drag_item = None
        self._drag_offset = QPointF()

        # Undo/Redo stacks (per slide)
        self.undo_stack = []
        self.redo_stack = []

        # Eraser cursor
        self._eraser_cursor = self._make_eraser_cursor()

        # Zoom state
        self._zoom = 1.0

    @property
    def zoom(self):
        return self._zoom

    def set_zoom(self, zoom_factor: float):
        self._zoom = max(0.1, min(zoom_factor, 10.0))
        self.resetTransform()
        self.scale(self._zoom, self._zoom)

    def set_slide_background(self, pixmap):
        self._scene.clear()
        self.slide_pixmap = pixmap
        if pixmap:
            self.slide_bg_item = self._scene.addPixmap(pixmap)
            self.slide_bg_item.setZValue(-1)
            self._scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
            self.fitInView(0, 0, pixmap.width(), pixmap.height(), Qt.KeepAspectRatio)
        else:
            self._scene.setSceneRect(0, 0, 800, 600)

    def update_background_only(self, pixmap):
        """Replaces only the slide background, preserving annotation items."""
        if self.slide_bg_item is not None:
            self._scene.removeItem(self.slide_bg_item)
            self.slide_bg_item = None
        self.slide_pixmap = pixmap
        if pixmap:
            self.slide_bg_item = self._scene.addPixmap(pixmap)
            self.slide_bg_item.setZValue(-1)
            self._scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
            self.fitInView(0, 0, pixmap.width(), pixmap.height(), Qt.KeepAspectRatio)
        else:
            self._scene.setSceneRect(0, 0, 800, 600)

    def set_tool(self, tool_mode):
        self.current_tool = tool_mode
        is_select = (tool_mode == config.MODE_SELECT)
        self.setDragMode(QGraphicsView.NoDrag)
        if tool_mode == config.MODE_ERASER:
            self.setCursor(self._eraser_cursor)
        else:
            self.setCursor(Qt.ArrowCursor if is_select else Qt.CrossCursor)
        self._set_text_items_movable(is_select)

    def _make_eraser_cursor(self):
        size = int(self.eraser_width * 1.2)
        px = QPixmap(size, size)
        px.fill(QColor(0, 0, 0, 0))
        p = QPainter(px)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(255, 80, 80, 200), 2.5))
        p.setBrush(QColor(255, 80, 80, 40))
        p.drawEllipse(1, 1, size - 3, size - 3)
        p.setPen(QPen(QColor(255, 255, 255, 120), 1))
        p.drawLine(size // 2, 4, size // 2, size - 4)
        p.drawLine(4, size // 2, size - 4, size // 2)
        p.end()
        return QCursor(px)

    def _set_text_items_movable(self, movable):
        if not self.scene():
            return
        for item in self.scene().items():
            if isinstance(item, QGraphicsTextItem):
                item.setFlag(QGraphicsItem.ItemIsMovable, movable)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            zoom_factor = 1.15 if event.angleDelta().y() > 0 else 0.85
            current_zoom = self.transform().m11()
            if config.MIN_ZOOM <= current_zoom * zoom_factor <= config.MAX_ZOOM:
                self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())

        if event.button() == Qt.MiddleButton:
            self.is_panning = True
            self.pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            return

        if self.current_tool == config.MODE_SELECT:
            item = self.itemAt(event.pos())
            top_text_item = None
            while item is not None:
                if isinstance(item, QGraphicsTextItem):
                    top_text_item = item
                    break
                item = item.parentItem()
            if top_text_item is not None:
                self.scene().clearSelection()
                top_text_item.setSelected(True)
                if top_text_item.flags() & QGraphicsItem.ItemIsMovable:
                    self._drag_item = top_text_item
                    self._drag_offset = scene_pos - top_text_item.scenePos()
                else:
                    self._drag_item = None
            else:
                self.scene().clearSelection()
                self._drag_item = None
            return

        self.is_drawing = True
        self.last_point = scene_pos
        self.redo_stack.clear()

        if self.current_tool == config.MODE_PEN:
            self.current_item = MovablePathItem()
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            self.current_item.setPen(pen)
            path = QPainterPath(scene_pos)
            self.current_item.setPath(path)
            self.scene().addItem(self.current_item)

        elif self.current_tool == config.MODE_HIGHLIGHTER:
            self.current_item = QGraphicsPathItem()
            pen = QPen(self.highlighter_color, self.highlighter_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            self.current_item.setPen(pen)
            path = QPainterPath(scene_pos)
            self.current_item.setPath(path)
            self.scene().addItem(self.current_item)

        elif self.current_tool == config.MODE_LINE:
            self.current_item = ResizableLineItem(
                scene_pos.x(), scene_pos.y(), scene_pos.x(), scene_pos.y()
            )
            self.current_item.setPen(QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap))
            self.scene().addItem(self.current_item)

        elif self.current_tool == config.MODE_RECT:
            self.current_item = ResizableRectItem(scene_pos.x(), scene_pos.y(), 0, 0)
            self.current_item.setPen(QPen(self.pen_color, self.pen_width))
            self.current_item.setBrush(QBrush(QColor(0, 0, 0, 0)))
            self.scene().addItem(self.current_item)

        elif self.current_tool == config.MODE_CIRCLE:
            self.current_item = ResizableEllipseItem(scene_pos.x(), scene_pos.y(), 0, 0)
            self.current_item.setPen(QPen(self.pen_color, self.pen_width))
            self.current_item.setBrush(QBrush(QColor(0, 0, 0, 0)))
            self.scene().addItem(self.current_item)

        elif self.current_tool == config.MODE_TEXT:
            text, ok = QInputDialog.getMultiLineText(self, "Add Text", "Enter text:")
            if ok and text.strip():
                text_item = MovableTextItem(text)
                text_item.setDefaultTextColor(self.pen_color)
                text_item.setFont(QFont("Segoe UI", self.text_size))
                text_item.setPos(scene_pos)
                text_item.setFlag(
                    QGraphicsItem.ItemIsMovable,
                    self.current_tool == config.MODE_SELECT,
                )
                self.scene().addItem(text_item)
                self.undo_stack.append(("add", text_item))
            self.is_drawing = False

        elif self.current_tool == config.MODE_ERASER:
            self.erase_at_point(scene_pos)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())

        if self.is_panning:
            delta = event.pos() - self.pan_start
            self.pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return

        if self.current_tool == config.MODE_SELECT and self._drag_item is not None:
            new_pos = scene_pos - self._drag_offset
            self._drag_item.setPos(new_pos)
            self._drag_item.setSelected(True)
            return

        if not self.is_drawing:
            super().mouseMoveEvent(event)
            return

        if self.current_tool in (config.MODE_PEN, config.MODE_HIGHLIGHTER):
            if self.current_item:
                path = self.current_item.path()
                path.lineTo(scene_pos)
                self.current_item.setPath(path)

        elif self.current_tool == config.MODE_LINE:
            if self.current_item:
                self.current_item.setLine(
                    self.last_point.x(), self.last_point.y(),
                    scene_pos.x(), scene_pos.y()
                )

        elif self.current_tool == config.MODE_RECT:
            if self.current_item:
                x = min(self.last_point.x(), scene_pos.x())
                y = min(self.last_point.y(), scene_pos.y())
                w = abs(self.last_point.x() - scene_pos.x())
                h = abs(self.last_point.y() - scene_pos.y())
                self.current_item.setRect(x, y, w, h)

        elif self.current_tool == config.MODE_CIRCLE:
            if self.current_item:
                x = min(self.last_point.x(), scene_pos.x())
                y = min(self.last_point.y(), scene_pos.y())
                w = abs(self.last_point.x() - scene_pos.x())
                h = abs(self.last_point.y() - scene_pos.y())
                self.current_item.setRect(x, y, w, h)

        elif self.current_tool == config.MODE_ERASER:
            self.erase_at_point(scene_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.is_panning = False
            self.setCursor(
                Qt.ArrowCursor if self.current_tool == config.MODE_SELECT else Qt.CrossCursor
            )
            return

        if self.current_tool == config.MODE_SELECT:
            self._drag_item = None
            return

        if not self.is_drawing:
            super().mouseReleaseEvent(event)
            return

        self.is_drawing = False

        if self.current_item:
            self.undo_stack.append(("add", self.current_item))
            self.current_item = None
            self.stroke_drawn.emit()

    def erase_at_point(self, scene_pos):
        eraser_rect = QRectF(
            scene_pos.x() - self.eraser_width / 2,
            scene_pos.y() - self.eraser_width / 2,
            self.eraser_width,
            self.eraser_width
        )
        items = self.scene().items(eraser_rect, Qt.IntersectsItemShape)
        for item in items:
            if item is self.slide_bg_item:
                continue
            if isinstance(item, QGraphicsProxyWidget):
                continue
            if isinstance(item, (
                QGraphicsPathItem, QGraphicsRectItem, QGraphicsEllipseItem,
                QGraphicsLineItem, QGraphicsTextItem,
                MovablePathItem, ResizableRectItem, ResizableEllipseItem, ResizableLineItem
            )):
                self.undo_stack.append(("remove", item))
                self.scene().removeItem(item)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            selected = self.scene().selectedItems()
            if selected:
                for item in selected:
                    if item is self.slide_bg_item:
                        continue
                    if isinstance(item, QGraphicsTextItem):
                        if item.textInteractionFlags() & Qt.TextEditorInteraction:
                            if item.hasFocus():
                                super().keyPressEvent(event)
                                return
                    self.undo_stack.append(("remove", item))
                    self.scene().removeItem(item)
                return
        super().keyPressEvent(event)

    def undo(self):
        if not self.undo_stack:
            return
        action, item = self.undo_stack.pop()
        if action == "add":
            if item in self.scene().items():
                self.scene().removeItem(item)
                self.redo_stack.append(("add", item))
        elif action == "remove":
            self.scene().addItem(item)
            self.redo_stack.append(("remove", item))

    def redo(self):
        if not self.redo_stack:
            return
        action, item = self.redo_stack.pop()
        if action == "add":
            self.scene().addItem(item)
            self.undo_stack.append(("add", item))
        elif action == "remove":
            if item in self.scene().items():
                self.scene().removeItem(item)
                self.undo_stack.append(("remove", item))

    def get_annotation_items(self):
        items = []
        for item in self.scene().items():
            if item is self.slide_bg_item:
                continue
            items.append(item)
        return items

    def load_annotation_items(self, items):
        for item in items:
            if item is not self.slide_bg_item:
                self.scene().addItem(item)

    def clear_annotations(self):
        for item in self.get_annotation_items():
            self.scene().removeItem(item)


class PptCanvasWidget(QWidget):
    """Main PPT canvas widget with slide view, navigation, and annotation support."""

    ppt_loaded = Signal(str)
    slide_changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ppt_handler = PptHandler()
        self.current_slide_index = 0
        self.slide_annotations = {}
        self._current_file_path = None

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
            QFrame#pptToolbar {{
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
        self._toolbar.setObjectName("pptToolbar")
        self._toolbar.setStyleSheet("""
            QFrame#pptToolbar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(18, 18, 30, 230), stop:1 rgba(30, 30, 50, 210));
                border-bottom: 1px solid rgba(99, 102, 241, 0.15);
            }
        """)
        tb_layout = QHBoxLayout(self._toolbar)
        tb_layout.setContentsMargins(14, 10, 14, 10)
        tb_layout.setSpacing(10)

        self.upload_btn = QPushButton("📂  Upload PPT")
        self.upload_btn.setStyleSheet(_BTN_PRIMARY)
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.clicked.connect(self.upload_ppt)
        tb_layout.addWidget(self.upload_btn)

        self.download_btn = QPushButton("💾  Download Annotated")
        self.download_btn.setStyleSheet(_BTN_SUBTLE)
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.clicked.connect(self.download_annotated)
        self.download_btn.setEnabled(False)
        tb_layout.addWidget(self.download_btn)

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

        self.file_label = QLabel("No presentation loaded")
        self.file_label.setStyleSheet("color: #94a3b8; font-size: 13px; padding: 0 8px;")
        tb_layout.addWidget(self.file_label)

        root.addWidget(self._toolbar)

        # Slide view area
        self.slide_view = PptCanvasView(self)
        root.addWidget(self.slide_view, 1)

        # Bottom navigation bar
        nav_bar = QFrame(self)
        nav_bar.setObjectName("pptNavBar")
        nav_bar.setStyleSheet("""
            QFrame#pptNavBar {
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
        self.prev_btn.clicked.connect(self.prev_slide)
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)

        self.slide_counter = QLabel("Slide 0 / 0")
        self.slide_counter.setStyleSheet(_NAV_LABEL)
        nav_layout.addWidget(self.slide_counter)

        self.next_btn = QPushButton("Next  ▶")
        self.next_btn.setStyleSheet(_BTN_SUBTLE)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_slide)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)

        nav_layout.addStretch()

        # Slide number input
        self.slide_input_label = QLabel("Go to:")
        self.slide_input_label.setStyleSheet("color: #94a3b8; font-size: 13px;")
        nav_layout.addWidget(self.slide_input_label)

        from PySide6.QtWidgets import QSpinBox
        self.slide_spin = QSpinBox()
        self.slide_spin.setRange(1, 1)
        self.slide_spin.setValue(1)
        self.slide_spin.setFixedWidth(70)
        self.slide_spin.setStyleSheet("""
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
        self.slide_spin.valueChanged.connect(self.go_to_slide)
        nav_layout.addWidget(self.slide_spin)

        root.addWidget(nav_bar)

    def upload_ppt(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Presentation",
            "",
            "PowerPoint Files (*.pptx *.ppt);;All Files (*.*)"
        )
        if not file_path:
            return

        self._load_ppt(file_path)

    def _load_ppt(self, file_path):
        try:
            count = self.ppt_handler.load(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load presentation:\n{str(e)}")
            return

        self._current_file_path = file_path
        self.current_slide_index = 0
        self.slide_annotations.clear()
        self.slide_view.undo_stack.clear()
        self.slide_view.redo_stack.clear()

        self.file_label.setText(os.path.basename(file_path))
        self.slide_spin.setRange(1, count)
        self.slide_spin.setValue(1)
        self._update_nav_buttons()
        self._show_slide(0)
        self.setEnabled(True)
        self.download_btn.setEnabled(True)
        self.ppt_loaded.emit(file_path)

    def _save_current_annotations(self):
        if self._current_file_path is None:
            return
        items = self.slide_view.get_annotation_items()
        # Remove items from scene so QGraphicsScene.clear() won't delete them
        for item in items:
            self.slide_view.scene().removeItem(item)
        self.slide_annotations[self.current_slide_index] = {
            "items": items,
            "undo": list(self.slide_view.undo_stack),
            "redo": list(self.slide_view.redo_stack),
        }

    def _load_annotations(self, index):
        self.slide_view.clear_annotations()
        self.slide_view.undo_stack.clear()
        self.slide_view.redo_stack.clear()
        if index in self.slide_annotations:
            data = self.slide_annotations[index]
            self.slide_view.load_annotation_items(data["items"])
            self.slide_view.undo_stack = list(data.get("undo", []))
            self.slide_view.redo_stack = list(data.get("redo", []))

    def _show_slide(self, index):
        pixmap = self.ppt_handler.get_slide_pixmap(index)
        if self.persist_cb.isChecked():
            # Persistent ON: restore per-slide annotations
            self.slide_view.set_slide_background(pixmap)
            self._load_annotations(index)
        else:
            # Persistent OFF: annotations are temporary, cleared on navigation
            self.slide_view.set_slide_background(pixmap)
        self.slide_counter.setText(f"Slide {index + 1} / {self.ppt_handler.slide_count}")
        self.slide_spin.blockSignals(True)
        self.slide_spin.setValue(index + 1)
        self.slide_spin.blockSignals(False)
        self._update_nav_buttons()
        self.slide_changed.emit(index, self.ppt_handler.slide_count)

    def _update_nav_buttons(self):
        total = self.ppt_handler.slide_count
        cur = self.current_slide_index
        self.prev_btn.setEnabled(cur > 0)
        self.next_btn.setEnabled(cur < total - 1)

    def next_slide(self):
        if self.persist_cb.isChecked():
            self._save_current_annotations()
        if self.current_slide_index < self.ppt_handler.slide_count - 1:
            self.current_slide_index += 1
            self._show_slide(self.current_slide_index)

    def prev_slide(self):
        if self.persist_cb.isChecked():
            self._save_current_annotations()
        if self.current_slide_index > 0:
            self.current_slide_index -= 1
            self._show_slide(self.current_slide_index)

    def go_to_slide(self, slide_num):
        target = slide_num - 1
        if target == self.current_slide_index:
            return
        if 0 <= target < self.ppt_handler.slide_count:
            if self.persist_cb.isChecked():
                self._save_current_annotations()
            self.current_slide_index = target
            self._show_slide(target)

    def _re_add_current_annotations(self):
        if self.current_slide_index in self.slide_annotations:
            for item in self.slide_annotations[self.current_slide_index]["items"]:
                self.slide_view.scene().addItem(item)

    def download_annotated(self):
        self._save_current_annotations()
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Annotated Presentation",
            os.path.splitext(os.path.basename(self._current_file_path))[0] + "_annotated.pptx",
            "PowerPoint Files (*.pptx)"
        )
        if not output_path:
            self._re_add_current_annotations()
            return

        try:
            annotation_map = {}
            for idx, data in self.slide_annotations.items():
                items = data["items"]
                if items:
                    scene = QGraphicsScene()
                    for item in items:
                        scene.addItem(item)
                    annotation_map[idx] = scene

            success = self.ppt_handler.export_annotated_pptx(output_path, annotation_map)
            self._re_add_current_annotations()
            if success:
                QMessageBox.information(
                    self, "Export Complete",
                    f"Annotated presentation saved to:\n{output_path}"
                )
            else:
                QMessageBox.critical(self, "Export Error", "Failed to save annotated presentation.")
        except Exception as e:
            self._re_add_current_annotations()
            QMessageBox.critical(self, "Export Error", f"An error occurred:\n{str(e)}")

    def set_tool(self, tool_mode):
        self.slide_view.set_tool(tool_mode)

    @property
    def pen_color(self):
        return self.slide_view.pen_color

    @pen_color.setter
    def pen_color(self, color):
        self.slide_view.pen_color = color
        self.slide_view.highlighter_color = QColor(color.red(), color.green(), color.blue(), 100)

    @property
    def pen_width(self):
        return self.slide_view.pen_width

    @pen_width.setter
    def pen_width(self, width):
        self.slide_view.pen_width = width
        self.slide_view.highlighter_width = max(width * 4, 8)
        self.slide_view.eraser_width = max(width * 5, 10)

    @property
    def text_size(self):
        return self.slide_view.text_size

    @text_size.setter
    def text_size(self, size):
        self.slide_view.text_size = size

    @property
    def highlighter_color(self):
        return self.slide_view.highlighter_color

    @highlighter_color.setter
    def highlighter_color(self, color):
        self.slide_view.highlighter_color = color

    @property
    def highlighter_width(self):
        return self.slide_view.highlighter_width

    @highlighter_width.setter
    def highlighter_width(self, width):
        self.slide_view.highlighter_width = width

    @property
    def eraser_width(self):
        return self.slide_view.eraser_width

    @eraser_width.setter
    def eraser_width(self, width):
        self.slide_view.eraser_width = width

    def undo(self):
        self.slide_view.undo()

    def redo(self):
        self.slide_view.redo()
