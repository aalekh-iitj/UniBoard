from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsRectItem,
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QInputDialog
)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QTransform, QFont
from PySide6.QtCore import Qt, QPointF, QTimer, Signal
import numpy as np

import config
from core.handwriting import HandwritingWorker

class WhiteboardCanvas(QGraphicsView):
    # Signals
    stroke_drawn = Signal()
    selection_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Grid settings
        self.grid_visible = True
        self.grid_size = config.GRID_SIZE
        
        # Tool state
        self.current_tool = config.MODE_PEN
        self.pen_color = QColor("#00ffcc")  # Default bright cyan neon
        self.pen_width = 3
        self.highlighter_color = QColor(255, 255, 0, 100) # Semi-transparent yellow
        self.highlighter_width = 15
        self.eraser_width = 20
        
        # Interaction states
        self.is_drawing = False
        self.is_panning = False
        self.pan_start = None
        self.last_point = QPointF()
        self.current_item = None
        
        # Undo/Redo Stacks
        self.undo_stack = []
        self.redo_stack = []

        # Handwriting settings
        self.handwriting_enabled = False
        self.current_handwriting_strokes = []
        self.current_handwriting_items = []
        self.handwriting_timer = QTimer(self)
        self.handwriting_timer.setSingleShot(True)
        self.handwriting_timer.setInterval(config.HANDWRITING_RECOGNITION_DELAY)
        self.handwriting_timer.timeout.connect(self.trigger_handwriting_recognition)

        # Set canvas styling
        self.canvas_bg_color = QColor("#1e1e24")  # Deep charcoal
        self.grid_color = QColor("#2a2a35")
        
        # Set central empty scene initially
        self.setScene(QGraphicsScene(self))
        self.scene().setSceneRect(-5000, -5000, 10000, 10000)
        self.update_background()

    def set_page_scene(self, scene):
        """Sets the active scene for the view when pages are switched."""
        self.setScene(scene)
        scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.update_background()

    def update_background(self):
        """Sets background color of active scene."""
        if self.scene():
            self.scene().setBackgroundBrush(QBrush(self.canvas_bg_color))

    def set_tool(self, tool_mode):
        self.current_tool = tool_mode
        if tool_mode == config.MODE_SELECT:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)

    def drawBackground(self, painter, rect):
        """Draws the background grid if visible."""
        super().drawBackground(painter, rect)
        if not self.grid_visible:
            return

        painter.save()
        painter.setPen(QPen(self.grid_color, 1))
        
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)
        right = int(rect.right())
        bottom = int(rect.bottom())

        # Draw grid lines
        for x in range(left, right, self.grid_size):
            painter.drawLine(x, top, x, bottom)
        for y in range(top, bottom, self.grid_size):
            painter.drawLine(left, y, right, y)
            
        painter.restore()

    def wheelEvent(self, event):
        """Handles zooming with ctrl+wheel."""
        if event.modifiers() == Qt.ControlModifier:
            zoom_factor = 1.15 if event.angleDelta().y() > 0 else 0.85
            current_zoom = self.transform().m11()
            
            # Bound zoom levels
            if config.MIN_ZOOM <= current_zoom * zoom_factor <= config.MAX_ZOOM:
                self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        
        if event.button() == Qt.MiddleButton:
            # Pan interaction
            self.is_panning = True
            self.pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            return

        if self.current_tool == config.MODE_SELECT:
            super().mousePressEvent(event)
            return

        self.is_drawing = True
        self.last_point = scene_pos
        self.redo_stack.clear()  # Clear redo on new action

        # Create drawing item based on current tool
        if self.current_tool == config.MODE_PEN:
            self.current_item = QGraphicsPathItem()
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            self.current_item.setPen(pen)
            
            path = QPainterPath(scene_pos)
            self.current_item.setPath(path)
            self.scene().addItem(self.current_item)
            
            if self.handwriting_enabled:
                # Stop timer and start recording new stroke
                self.handwriting_timer.stop()
                self.current_handwriting_strokes.append([(scene_pos.x(), scene_pos.y())])

        elif self.current_tool == config.MODE_HIGHLIGHTER:
            self.current_item = QGraphicsPathItem()
            # Alpha translucent pen
            pen = QPen(self.highlighter_color, self.highlighter_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            self.current_item.setPen(pen)
            
            path = QPainterPath(scene_pos)
            self.current_item.setPath(path)
            self.scene().addItem(self.current_item)

        elif self.current_tool == config.MODE_LINE:
            self.current_item = QGraphicsLineItem(scene_pos.x(), scene_pos.y(), scene_pos.x(), scene_pos.y())
            self.current_item.setPen(QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap))
            self.scene().addItem(self.current_item)

        elif self.current_tool == config.MODE_RECT:
            self.current_item = QGraphicsRectItem(scene_pos.x(), scene_pos.y(), 0, 0)
            self.current_item.setPen(QPen(self.pen_color, self.pen_width))
            self.scene().addItem(self.current_item)

        elif self.current_tool == config.MODE_CIRCLE:
            self.current_item = QGraphicsEllipseItem(scene_pos.x(), scene_pos.y(), 0, 0)
            self.current_item.setPen(QPen(self.pen_color, self.pen_width))
            self.scene().addItem(self.current_item)

        elif self.current_tool == config.MODE_TEXT:
            text, ok = QInputDialog.getMultiLineText(self, "Add Text", "Enter your text:")
            if ok and text.strip():
                text_item = QGraphicsTextItem(text)
                text_item.setDefaultTextColor(self.pen_color)
                text_item.setFont(QFont("Outfit", 14))
                text_item.setPos(scene_pos)
                text_item.setFlag(QGraphicsTextItem.ItemIsMovable)
                text_item.setFlag(QGraphicsTextItem.ItemIsSelectable)
                self.scene().addItem(text_item)
                self.undo_stack.append(("add", text_item))
            self.is_drawing = False

        elif self.current_tool == config.MODE_ERASER:
            self.erase_at_point(scene_pos)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())

        if self.is_panning:
            # Pan calculation
            delta = event.pos() - self.pan_start
            self.pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return

        if not self.is_drawing:
            super().mouseMoveEvent(event)
            return

        # Handle drawing updates
        if self.current_tool in (config.MODE_PEN, config.MODE_HIGHLIGHTER):
            path = self.current_item.path()
            path.lineTo(scene_pos)
            self.current_item.setPath(path)
            
            if self.current_tool == config.MODE_PEN and self.handwriting_enabled:
                self.current_handwriting_strokes[-1].append((scene_pos.x(), scene_pos.y()))

        elif self.current_tool == config.MODE_LINE:
            self.current_item.setLine(self.last_point.x(), self.last_point.y(), scene_pos.x(), scene_pos.y())

        elif self.current_tool == config.MODE_RECT:
            x = min(self.last_point.x(), scene_pos.x())
            y = min(self.last_point.y(), scene_pos.y())
            w = abs(self.last_point.x() - scene_pos.x())
            h = abs(self.last_point.y() - scene_pos.y())
            self.current_item.setRect(x, y, w, h)

        elif self.current_tool == config.MODE_CIRCLE:
            x = min(self.last_point.x(), scene_pos.x())
            y = min(self.last_point.y(), scene_pos.y())
            w = abs(self.last_point.x() - scene_pos.x())
            h = abs(self.last_point.y() - scene_pos.y())
            self.current_item.setRect(x, y, w, h)

        elif self.current_tool == config.MODE_ERASER:
            self.erase_at_point(scene_pos)

        self.last_point = scene_pos

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.is_panning = False
            self.setCursor(Qt.CrossCursor if self.current_tool != config.MODE_SELECT else Qt.ArrowCursor)
            return

        if not self.is_drawing:
            super().mouseReleaseEvent(event)
            return

        self.is_drawing = False
        
        # Commit to undo stack
        if self.current_item:
            self.undo_stack.append(("add", self.current_item))
            
            if self.current_tool == config.MODE_PEN and self.handwriting_enabled:
                self.current_handwriting_items.append(self.current_item)
                # Reset or start handwriting timeout timer
                self.handwriting_timer.start()

            self.current_item = None
            self.stroke_drawn.emit()

    def erase_at_point(self, scene_pos):
        """Removes any items intersecting the eraser circle."""
        items = self.scene().items(scene_pos, Qt.IntersectsItemShape)
        for item in items:
            # Do not erase background layout items, text editors, etc.
            if isinstance(item, (QGraphicsPathItem, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem)):
                self.undo_stack.append(("remove", item))
                self.scene().removeItem(item)

    # Undo/Redo Logic
    def undo(self):
        if not self.undo_stack:
            return
        
        action, item = self.undo_stack.pop()
        if action == "add":
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
            self.scene().removeItem(item)
            self.undo_stack.append(("remove", item))

    # Handwriting conversion trigger
    def trigger_handwriting_recognition(self):
        if not self.current_handwriting_strokes:
            return

        strokes_to_send = list(self.current_handwriting_strokes)
        items_to_remove = list(self.current_handwriting_items)
        
        # Reset state
        self.current_handwriting_strokes = []
        self.current_handwriting_items = []

        # Find visual bounding box of drawings to place the text item
        xs = []
        ys = []
        for stroke in strokes_to_send:
            for pt in stroke:
                xs.append(pt[0])
                ys.append(pt[1])
        
        if not xs or not ys:
            return

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Run worker thread
        self.worker = HandwritingWorker(strokes_to_send, items_to_remove, self.width(), self.height())
        self.worker.finished_recognition.connect(lambda txt, items: self.on_handwriting_finished(txt, items, min_x, min_y))
        self.worker.start()

    def on_handwriting_finished(self, text, items, x, y):
        if not text or not text.strip():
            return
            
        # Delete handwriting drawings
        for item in items:
            if item in self.scene().items():
                self.scene().removeItem(item)
                # Remove from undo stack if it was there
                for act, it in list(self.undo_stack):
                    if it == item:
                        self.undo_stack.remove((act, it))

        # Add text element
        text_item = QGraphicsTextItem(text)
        text_item.setDefaultTextColor(self.pen_color)
        text_item.setFont(QFont("Outfit", 16))
        text_item.setPos(x, y)
        text_item.setFlag(QGraphicsTextItem.ItemIsMovable)
        text_item.setFlag(QGraphicsTextItem.ItemIsSelectable)
        self.scene().addItem(text_item)
        self.undo_stack.append(("add", text_item))
