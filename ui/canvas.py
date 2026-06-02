from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsRectItem,
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QInputDialog,
    QLabel, QVBoxLayout, QGraphicsProxyWidget, QGraphicsItem,
    QWidget, QScrollBar
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPainterPath, QFont, QCursor
)
from PySide6.QtCore import Qt, QPointF, QTimer, Signal, QRectF, QPoint

import config
from core.handwriting import HandwritingWorker


# ---------------------------------------------------------------------------
# Resizable shape items – selectable + movable after drawing
# ---------------------------------------------------------------------------
class ResizableRectItem(QGraphicsRectItem):
    """A rectangle that is selectable and movable after creation."""
    def __init__(self, x, y, w, h, parent=None):
        super().__init__(x, y, w, h, parent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)


class ResizableEllipseItem(QGraphicsEllipseItem):
    def __init__(self, x, y, w, h, parent=None):
        super().__init__(x, y, w, h, parent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)


class ResizableLineItem(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, parent=None):
        super().__init__(x1, y1, x2, y2, parent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)


class MovablePathItem(QGraphicsPathItem):
    """A freehand path that is selectable and movable after creation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)


# ---------------------------------------------------------------------------
# Main Whiteboard Canvas
# ---------------------------------------------------------------------------
class WhiteboardCanvas(QGraphicsView):
    stroke_drawn = Signal()
    selection_changed = Signal()
    canvas_type_changed = Signal(str)

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

        # Grid settings
        self.grid_visible = True
        self.grid_size = config.GRID_SIZE

        # Active page node reference
        self.active_node = None
        self.current_canvas_type = config.CANVAS_PLAIN

        # Tool state
        self.current_tool = config.MODE_PEN
        self.pen_color = QColor("#00ffcc")
        self.pen_width = 3
        self.text_size = 16
        self.highlighter_color = QColor(255, 255, 0, 100)
        self.highlighter_width = 15
        self.eraser_width = 20

        # Interaction states
        self.is_drawing = False
        self.is_panning = False
        self.pan_start = None
        self.last_point = QPointF()
        self.current_item = None

        # Undo/Redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Handwriting recognition
        self.handwriting_enabled = False
        self.current_handwriting_strokes = []
        self.current_handwriting_items = []
        self.handwriting_timer = QTimer(self)
        self.handwriting_timer.setSingleShot(True)
        self.handwriting_timer.setInterval(config.HANDWRITING_RECOGNITION_DELAY)
        self.handwriting_timer.timeout.connect(self.trigger_handwriting_recognition)

        # Canvas styling
        self.canvas_bg_color = QColor("#0d0d11")
        self.grid_color = QColor("#1a1a22")

        # Setup initial scene
        self.setScene(QGraphicsScene(self))
        self.scene().setSceneRect(-5000, -5000, 10000, 10000)
        self.update_background()

        # Viewport overlays
        self.setup_viewport_overlays()

    # ------------------------------------------------------------------
    # Page Node Management
    # ------------------------------------------------------------------
    def set_page_node(self, node):
        """Switch to a different page node."""
        self.active_node = node
        self.set_page_scene(node.scene)
        self.current_canvas_type = node.meta.get("canvas_type", config.CANVAS_PLAIN)
        self.refresh_agenda_overlay()
        self.update_overlay_visibility()

    def set_page_scene(self, scene):
        self.setScene(scene)
        scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.update_background()

    def update_background(self):
        if self.scene():
            self.scene().setBackgroundBrush(QBrush(self.canvas_bg_color))

    # ------------------------------------------------------------------
    # Tool Switching
    # ------------------------------------------------------------------
    def set_tool(self, tool_mode):
        self.current_tool = tool_mode
        if tool_mode == config.MODE_SELECT:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setCursor(Qt.ArrowCursor)
        elif tool_mode == config.MODE_ERASER:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)

    # ------------------------------------------------------------------
    # Overlay Visibility
    # ------------------------------------------------------------------
    def update_overlay_visibility(self):
        canvas_type = getattr(self, "current_canvas_type", config.CANVAS_PLAIN)
        is_plain = (canvas_type == config.CANVAS_PLAIN)
        self.title_overlay.setVisible(is_plain)
        self.agenda_overlay.setVisible(is_plain)

    # ------------------------------------------------------------------
    # Viewport Overlays
    # ------------------------------------------------------------------
    def setup_viewport_overlays(self):
        # Title overlay – floats at top center
        self.title_overlay = QLabel(self)
        self.title_overlay.setAlignment(Qt.AlignCenter)
        self.title_overlay.setStyleSheet("""
            QLabel {
                background-color: rgba(13, 13, 17, 0.88);
                border: 1px solid rgba(138, 43, 226, 0.3);
                border-radius: 20px;
                color: #ffffff;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 15px;
                font-weight: bold;
                padding: 8px 28px;
            }
        """)
        self.title_overlay.setText("UniBoard")
        self.title_overlay.show()

        # Agenda overlay – floats on left side
        self.agenda_overlay = QWidget(self)
        self.agenda_layout = QVBoxLayout(self.agenda_overlay)
        self.agenda_layout.setContentsMargins(12, 12, 12, 12)
        self.agenda_layout.setSpacing(8)
        self.agenda_overlay.setStyleSheet("""
            QWidget#agendaContainer {
                background-color: rgba(13, 13, 17, 0.8);
                border: 1px solid rgba(138, 43, 226, 0.2);
                border-radius: 14px;
            }
            QLabel[class="agendaTitle"] {
                color: #a855f7;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 8px;
            }
            QLabel[class="agendaItem"] {
                color: #e2e2e8;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                padding: 5px 10px;
                background-color: rgba(255, 255, 255, 0.03);
                border-radius: 6px;
                border-left: 3px solid rgba(138, 43, 226, 0.5);
            }
        """)
        self.agenda_overlay.setObjectName("agendaContainer")
        self.agenda_overlay.show()

    def update_overlay_widgets(self):
        """Position overlays correctly inside the viewport."""
        w = self.viewport().width()
        h = self.viewport().height()

        # Title: top center
        title_size = self.title_overlay.sizeHint()
        tw = min(title_size.width(), w - 40)
        self.title_overlay.setGeometry(
            int((w - tw) / 2), 14, tw, title_size.height()
        )

        # Agenda: middle left
        agenda_size = self.agenda_overlay.sizeHint()
        ah = min(agenda_size.height(), h - 60)
        aw = min(200, w - 30)
        self.agenda_overlay.setGeometry(
            16, int((h - ah) / 2), aw, ah
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_overlay_widgets()

    def refresh_agenda_overlay(self):
        """Rebuild the agenda from the current node's children."""
        # Clear existing items
        for i in reversed(range(self.agenda_layout.count())):
            widget = self.agenda_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not self.active_node:
            self.agenda_overlay.hide()
            return

        canvas_type = self.active_node.meta.get("canvas_type", config.CANVAS_PLAIN)
        if canvas_type != config.CANVAS_PLAIN:
            self.agenda_overlay.hide()
            self.title_overlay.setText(self.active_node.title)
            self.title_overlay.adjustSize()
            self.update_overlay_widgets()
            return

        self.agenda_overlay.show()
        self.title_overlay.setText(self.active_node.title)
        self.title_overlay.adjustSize()

        # Header
        hdr = QLabel("OUTLINE")
        hdr.setProperty("class", "agendaTitle")
        self.agenda_layout.addWidget(hdr)

        # Subtopics
        subtopics = self.active_node.children
        if not subtopics:
            empty_lbl = QLabel("No subtopics yet")
            empty_lbl.setStyleSheet("color: #555566; font-style: italic; font-size: 11px; padding: 4px 8px;")
            self.agenda_layout.addWidget(empty_lbl)
        else:
            for node in subtopics:
                lbl = QLabel(f"  {node.title}")
                lbl.setProperty("class", "agendaItem")
                lbl.setWordWrap(True)
                self.agenda_layout.addWidget(lbl)

        self.agenda_overlay.adjustSize()
        self.update_overlay_widgets()

    # ------------------------------------------------------------------
    # Background Grid
    # ------------------------------------------------------------------
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if not self.grid_visible:
            return

        painter.save()

        # Faint grid lines
        grid_pen = QPen(self.grid_color, 0.5)
        painter.setPen(grid_pen)

        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)
        right = int(rect.right())
        bottom = int(rect.bottom())

        for x in range(left, right, self.grid_size):
            painter.drawLine(x, top, x, bottom)
        for y in range(top, bottom, self.grid_size):
            painter.drawLine(left, y, right, y)

        painter.restore()

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------
    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            zoom_factor = 1.15 if event.angleDelta().y() > 0 else 0.85
            current_zoom = self.transform().m11()
            if config.MIN_ZOOM <= current_zoom * zoom_factor <= config.MAX_ZOOM:
                self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)

    # ------------------------------------------------------------------
    # Mouse – Drawing Engine
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())

        # Middle-click panning
        if event.button() == Qt.MiddleButton:
            self.is_panning = True
            self.pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            return

        # Select mode – delegate to base
        if self.current_tool == config.MODE_SELECT:
            super().mousePressEvent(event)
            return

        self.is_drawing = True
        self.last_point = scene_pos
        self.redo_stack.clear()

        # --- Pen ---
        if self.current_tool == config.MODE_PEN:
            self.current_item = MovablePathItem()
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            self.current_item.setPen(pen)
            path = QPainterPath(scene_pos)
            self.current_item.setPath(path)
            self.scene().addItem(self.current_item)

            if self.handwriting_enabled:
                self.handwriting_timer.stop()
                self.current_handwriting_strokes.append([(event.pos().x(), event.pos().y())])

        # --- Highlighter ---
        elif self.current_tool == config.MODE_HIGHLIGHTER:
            self.current_item = QGraphicsPathItem()
            pen = QPen(self.highlighter_color, self.highlighter_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            self.current_item.setPen(pen)
            path = QPainterPath(scene_pos)
            self.current_item.setPath(path)
            self.scene().addItem(self.current_item)

        # --- Line ---
        elif self.current_tool == config.MODE_LINE:
            self.current_item = ResizableLineItem(
                scene_pos.x(), scene_pos.y(), scene_pos.x(), scene_pos.y()
            )
            self.current_item.setPen(QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap))
            self.scene().addItem(self.current_item)

        # --- Rectangle ---
        elif self.current_tool == config.MODE_RECT:
            self.current_item = ResizableRectItem(scene_pos.x(), scene_pos.y(), 0, 0)
            self.current_item.setPen(QPen(self.pen_color, self.pen_width))
            self.current_item.setBrush(QBrush(QColor(0, 0, 0, 0)))
            self.scene().addItem(self.current_item)

        # --- Circle ---
        elif self.current_tool == config.MODE_CIRCLE:
            self.current_item = ResizableEllipseItem(scene_pos.x(), scene_pos.y(), 0, 0)
            self.current_item.setPen(QPen(self.pen_color, self.pen_width))
            self.current_item.setBrush(QBrush(QColor(0, 0, 0, 0)))
            self.scene().addItem(self.current_item)

        # --- Text ---
        elif self.current_tool == config.MODE_TEXT:
            text, ok = QInputDialog.getMultiLineText(self, "Add Text", "Enter text:")
            if ok and text.strip():
                text_item = QGraphicsTextItem(text)
                text_item.setDefaultTextColor(self.pen_color)
                text_item.setFont(QFont("Segoe UI", self.text_size))
                text_item.setPos(scene_pos)
                text_item.setFlag(QGraphicsTextItem.ItemIsMovable, True)
                text_item.setFlag(QGraphicsTextItem.ItemIsSelectable, True)
                text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
                self.scene().addItem(text_item)
                self.undo_stack.append(("add", text_item))
            self.is_drawing = False

        # --- Eraser ---
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

        if not self.is_drawing:
            super().mouseMoveEvent(event)
            return

        if self.current_tool in (config.MODE_PEN, config.MODE_HIGHLIGHTER):
            if self.current_item:
                path = self.current_item.path()
                path.lineTo(scene_pos)
                self.current_item.setPath(path)

                if self.current_tool == config.MODE_PEN and self.handwriting_enabled:
                    self.current_handwriting_strokes[-1].append((event.pos().x(), event.pos().y()))

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

        if not self.is_drawing:
            super().mouseReleaseEvent(event)
            return

        self.is_drawing = False

        if self.current_item:
            self.undo_stack.append(("add", self.current_item))
            if self.current_tool == config.MODE_PEN and self.handwriting_enabled:
                self.current_handwriting_items.append(self.current_item)
                self.handwriting_timer.start()
            self.current_item = None
            self.stroke_drawn.emit()

    def erase_at_point(self, scene_pos):
        """Erase drawable items at scene position."""
        eraser_rect = QRectF(
            scene_pos.x() - self.eraser_width / 2,
            scene_pos.y() - self.eraser_width / 2,
            self.eraser_width,
            self.eraser_width
        )
        items = self.scene().items(eraser_rect, Qt.IntersectsItemShape)
        for item in items:
            if isinstance(item, QGraphicsProxyWidget):
                continue
            if isinstance(item, (
                QGraphicsPathItem, QGraphicsRectItem, QGraphicsEllipseItem,
                QGraphicsLineItem, QGraphicsTextItem,
                MovablePathItem, ResizableRectItem, ResizableEllipseItem, ResizableLineItem
            )):
                self.undo_stack.append(("remove", item))
                self.scene().removeItem(item)

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            selected = self.scene().selectedItems()
            if selected:
                for item in selected:
                    # Don't delete text being edited
                    if isinstance(item, QGraphicsTextItem):
                        if item.textInteractionFlags() & Qt.TextEditorInteraction:
                            if item.hasFocus():
                                super().keyPressEvent(event)
                                return
                    self.undo_stack.append(("remove", item))
                    self.scene().removeItem(item)
                return
        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Handwriting Recognition
    # ------------------------------------------------------------------
    def trigger_handwriting_recognition(self):
        if not self.current_handwriting_strokes:
            return

        strokes_to_send = list(self.current_handwriting_strokes)
        items_to_remove = list(self.current_handwriting_items)

        self.current_handwriting_strokes = []
        self.current_handwriting_items = []

        xs, ys = [], []
        for stroke in strokes_to_send:
            for pt in stroke:
                xs.append(pt[0])
                ys.append(pt[1])

        if not xs or not ys:
            return

        min_x, min_y = min(xs), min(ys)

        self.worker = HandwritingWorker(
            strokes_to_send, items_to_remove, self.width(), self.height()
        )
        self.worker.finished_recognition.connect(
            lambda txt, items: self.on_handwriting_finished(txt, items, min_x, min_y)
        )
        self.worker.start()

    def on_handwriting_finished(self, text, items, vp_x, vp_y):
        if not text or not text.strip():
            return

        # Remove the drawn strokes
        for item in items:
            if item in self.scene().items():
                self.scene().removeItem(item)
                for act, it in list(self.undo_stack):
                    if it == item:
                        self.undo_stack.remove((act, it))

        scene_pos = self.mapToScene(QPoint(int(vp_x), int(vp_y)))

        text_item = QGraphicsTextItem(text)
        text_item.setDefaultTextColor(self.pen_color)
        text_item.setFont(QFont("Segoe UI", self.text_size, QFont.Bold))
        text_item.setPos(scene_pos)
        text_item.setFlag(QGraphicsTextItem.ItemIsMovable, True)
        text_item.setFlag(QGraphicsTextItem.ItemIsSelectable, True)
        self.scene().addItem(text_item)
        self.undo_stack.append(("add", text_item))

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------
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
