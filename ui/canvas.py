from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsRectItem,
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QInputDialog,
    QLabel, QVBoxLayout, QGraphicsProxyWidget, QGraphicsItem,
    QWidget, QScrollBar, QToolButton
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


class MovableTextItem(QGraphicsTextItem):
    """A text item that the user can select, move (with the Select tool),
    and edit (on double-click).

    Unlike the default Qt behaviour with ``TextEditorInteraction`` (which
    swallows the first click into edit-mode and prevents the user from
    grabbing the item to reposition it), this subclass:

    * Never auto-enters edit mode on a single click.
    * Is *only* movable while the Select tool is active – the canvas
      toggles ``ItemIsMovable`` on/off via ``_set_text_items_movable``.
    * Opens an input dialog on *double-click* to edit the text.
    """
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        # ItemIsMovable is intentionally left unset here – the canvas
        # sets it based on whichever tool is currently active so that
        # drawing tools can paint over the items without dragging them.
        # NOTE: we deliberately do NOT call setTextInteractionFlags so the
        # item never auto-enters edit mode on single click.

    def shape(self):
        """Return a slightly padded rectangle so the item is easy to grab."""
        rect = self.boundingRect()
        path = QPainterPath()
        path.addRect(rect.adjusted(-10, -6, 10, 6))
        return path

    def mouseDoubleClickEvent(self, event):
        """Open an input dialog to edit the text."""
        from PySide6.QtWidgets import QInputDialog
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        new_text, ok = QInputDialog.getText(
            view, "Edit Text", "Enter text:", text=self.toPlainText()
        )
        if ok and new_text is not None:
            self.setPlainText(new_text)
        super().mouseDoubleClickEvent(event)


# ---------------------------------------------------------------------------
# Main Whiteboard Canvas
# ---------------------------------------------------------------------------
class WhiteboardCanvas(QGraphicsView):
    stroke_drawn = Signal()
    selection_changed = Signal()
    canvas_type_changed = Signal(str)
    new_canvas_requested = Signal()

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

        # Manual drag-state for the Select tool.  ``QGraphicsView`` with
        # ``NoDrag`` mode does *not* start item drags on its own, so we
        # implement selection + drag-to-move explicitly here.
        self._drag_item = None
        self._drag_offset = QPointF()

        # Ensure mouse-move events are delivered even when no button is
        # pressed (useful for live cursor feedback).
        self.setMouseTracking(True)

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
        # Refresh movability of the freshly loaded scene's text items
        # according to whichever tool is currently active.
        self._set_text_items_movable(self.current_tool == config.MODE_SELECT)
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
        is_select = (tool_mode == config.MODE_SELECT)
        # Use NoDrag in *all* modes – RubberBandDrag would prevent the
        # user from clicking on a text item to select & move it.
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(Qt.ArrowCursor if is_select else Qt.CrossCursor)
        # Text items are only movable while the Select tool is active.
        self._set_text_items_movable(is_select)

    def _set_text_items_movable(self, movable):
        """Enable or disable movement on every text item in the current scene."""
        if not self.scene():
            return
        for item in self.scene().items():
            if isinstance(item, QGraphicsTextItem):
                item.setFlag(QGraphicsItem.ItemIsMovable, movable)

    # ------------------------------------------------------------------
    # Overlay Visibility
    # ------------------------------------------------------------------
    def update_overlay_visibility(self):
        canvas_type = getattr(self, "current_canvas_type", config.CANVAS_PLAIN)
        is_plain = (canvas_type == config.CANVAS_PLAIN)
        # The legacy title/agenda overlays are permanently hidden – topic
        # and subtopic items now live directly on the canvas.
        self.title_overlay.setVisible(False)
        self.agenda_overlay.setVisible(False)
        # The "+" buttons are only meaningful on the plain drawing canvas
        self.add_topic_btn.setVisible(is_plain)
        self.add_subtopic_btn.setVisible(is_plain)
        self.new_canvas_btn.setVisible(is_plain)

    # ------------------------------------------------------------------
    # Viewport Overlays
    # ------------------------------------------------------------------
    def setup_viewport_overlays(self):
        # Title overlay – floats at top center (hidden, replaced by on-canvas topic)
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
        self.title_overlay.hide()

        # Agenda overlay – floats on left side (hidden, replaced by on-canvas subtopics)
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
        self.agenda_overlay.hide()

        # ---- On-canvas "+" buttons (replaces the left-pane sidebar) ----
        btn_style_purple = """
            QToolButton {
                background-color: rgba(138, 43, 226, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: rgba(138, 43, 226, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }
        """
        btn_style_blue = """
            QToolButton {
                background-color: rgba(59, 130, 246, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: rgba(59, 130, 246, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }
        """
        btn_style_green = """
            QToolButton {
                background-color: rgba(34, 197, 94, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 18px;
                color: white;
                font-size: 22px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: rgba(34, 197, 94, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }
        """

        # "+ Title" button – top center
        self.add_topic_btn = QToolButton(self)
        self.add_topic_btn.setText("+")
        self.add_topic_btn.setToolTip("Add Topic Title")
        self.add_topic_btn.setFixedSize(32, 32)
        self.add_topic_btn.setStyleSheet(btn_style_purple)
        self.add_topic_btn.setCursor(Qt.PointingHandCursor)
        self.add_topic_btn.clicked.connect(self.add_topic)
        self.add_topic_btn.show()

        # "+ Subtopic" button – left side, always visible
        self.add_subtopic_btn = QToolButton(self)
        self.add_subtopic_btn.setText("+")
        self.add_subtopic_btn.setToolTip("Add Subtopic")
        self.add_subtopic_btn.setFixedSize(32, 32)
        self.add_subtopic_btn.setStyleSheet(btn_style_blue)
        self.add_subtopic_btn.setCursor(Qt.PointingHandCursor)
        self.add_subtopic_btn.clicked.connect(self.add_subtopic)
        self.add_subtopic_btn.show()

        # "+ Canvas" button – right bottom corner
        self.new_canvas_btn = QToolButton(self)
        self.new_canvas_btn.setText("+")
        self.new_canvas_btn.setToolTip("New Canvas")
        self.new_canvas_btn.setFixedSize(40, 40)
        self.new_canvas_btn.setStyleSheet(btn_style_green)
        self.new_canvas_btn.setCursor(Qt.PointingHandCursor)
        self.new_canvas_btn.clicked.connect(self.request_new_canvas)
        self.new_canvas_btn.show()

    def update_overlay_widgets(self):
        """Position overlays correctly inside the viewport."""
        w = self.viewport().width()
        h = self.viewport().height()

        # Title: top center (hidden, kept for compatibility)
        title_size = self.title_overlay.sizeHint()
        tw = min(title_size.width(), w - 40)
        self.title_overlay.setGeometry(
            int((w - tw) / 2), 14, tw, title_size.height()
        )

        # Agenda: middle left (hidden, kept for compatibility)
        agenda_size = self.agenda_overlay.sizeHint()
        ah = min(agenda_size.height(), h - 60)
        aw = min(200, w - 30)
        self.agenda_overlay.setGeometry(
            16, int((h - ah) / 2), aw, ah
        )

        # ---- Position the on-canvas "+" buttons ----
        btn_size = 32
        # "+ Title" – top center
        self.add_topic_btn.setGeometry(
            int((w - btn_size) / 2), 14, btn_size, btn_size
        )
        # "+ Subtopic" – left side, below the title area, always visible
        self.add_subtopic_btn.setGeometry(
            16, 60, btn_size, btn_size
        )
        # "+ Canvas" – right bottom corner
        ncb_size = 40
        self.new_canvas_btn.setGeometry(
            w - ncb_size - 20, h - ncb_size - 20, ncb_size, ncb_size
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_overlay_widgets()

    def refresh_agenda_overlay(self):
        """No-op: topic and subtopics are now drawn directly on the canvas.

        Kept as a stub for backward compatibility with any callers.
        """
        # Ensure legacy overlays stay hidden regardless of who calls this.
        self.title_overlay.setVisible(False)
        self.agenda_overlay.setVisible(False)
        return

        # The block below is unreachable dead code (kept for safety only).
        # Subtopics are now drawn directly on the canvas as MovableTextItem
        # instances via add_topic() / add_subtopic().
        # ---- unreachable ----
        subtopics = self.active_node.children if self.active_node else []
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

        # ------------------------------------------------------------------
        # Select tool – handle item selection + drag-to-move manually.
        # QGraphicsView with NoDrag does not start drags on its own, and
        # RubberBandDrag would prevent clicking on items from selecting
        # them.  Doing it ourselves guarantees the click-and-drag works.
        # ------------------------------------------------------------------
        if self.current_tool == config.MODE_SELECT:
            # Find the topmost item under the cursor.
            item = self.itemAt(event.pos())
            # Walk up the parent chain so a click on a child proxy still
            # resolves to the top-level text item.
            top_text_item = None
            while item is not None:
                if isinstance(item, QGraphicsTextItem):
                    top_text_item = item
                    break
                item = item.parentItem()

            if top_text_item is not None:
                # Select this item (single-selection for now).
                self.scene().clearSelection()
                top_text_item.setSelected(True)
                # Start a manual drag if the item is movable.
                if top_text_item.flags() & QGraphicsItem.ItemIsMovable:
                    self._drag_item = top_text_item
                    self._drag_offset = scene_pos - top_text_item.scenePos()
                else:
                    self._drag_item = None
            else:
                # Clicked on empty space – clear selection.
                self.scene().clearSelection()
                self._drag_item = None
            return

        # ------------------------------------------------------------------
        # Drawing tools
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # Select tool – if a drag is in progress, move the item.
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # Select tool – end the manual drag if one is in progress.
        # ------------------------------------------------------------------
        if self.current_tool == config.MODE_SELECT:
            self._drag_item = None
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
    # On-Canvas Topic & Subtopic Management
    # ------------------------------------------------------------------
    DATA_KEY_ROLE = Qt.UserRole + 1   # distinguishes "topic" vs "subtopic"

    def _find_topic_item(self):
        """Return the single topic QGraphicsTextItem in the scene, or None."""
        for item in self.scene().items():
            if isinstance(item, QGraphicsTextItem):
                if item.data(self.DATA_KEY_ROLE) == "topic":
                    return item
        return None

    def _find_subtopic_items(self):
        """Return all subtopic QGraphicsTextItems in the scene, ordered by y."""
        items = []
        for item in self.scene().items():
            if isinstance(item, QGraphicsTextItem):
                if item.data(self.DATA_KEY_ROLE) == "subtopic":
                    items.append(item)
        items.sort(key=lambda it: it.pos().y())
        return items

    def add_topic(self):
        """Add (or focus) the single topic title text item on the canvas.

        The resulting item is fully movable – the user can click and drag
        it to any position on the canvas.  Double-click opens an edit
        dialog to change the text.
        """
        # Only one topic allowed per canvas – if it exists, just focus it.
        existing = self._find_topic_item()
        if existing is not None:
            self.scene().clearSelection()
            existing.setSelected(True)
            self.centerOn(existing)
            return

        text, ok = QInputDialog.getText(
            self, "Add Topic", "Enter topic title:"
        )
        if not ok or not text.strip():
            return

        # Use MovableTextItem so the item is draggable (with Select tool)
        # and is edited only via double-click (no auto-edit-on-click).
        item = MovableTextItem(text.strip())
        item.setData(self.DATA_KEY_ROLE, "topic")
        item.setDefaultTextColor(QColor("#ffffff"))
        item.setFont(QFont("Segoe UI", 22, QFont.Bold))
        item.setZValue(10)  # keep topic on top of drawings
        # ItemIsMovable is set after addItem so it reflects the active tool.

        # Position: a bit below the top-center of the current viewport,
        # well inside the visible area so the user immediately sees and
        # can grab the new item.
        vp = self.viewport().rect()
        scene_pt = self.mapToScene(
            QPoint(int(vp.width() / 2 - 120), int(vp.height() / 2 - 80))
        )
        item.setPos(scene_pt)

        self.scene().addItem(item)
        # Set movability after the item is in the scene, based on the
        # currently active tool.
        item.setFlag(
            QGraphicsItem.ItemIsMovable,
            self.current_tool == config.MODE_SELECT,
        )
        self.undo_stack.append(("add", item))

    def add_subtopic(self):
        """Add a new subtopic text item on the canvas (always shown).

        Like the topic, subtopics are ``MovableTextItem`` instances that
        can be freely dragged anywhere on the canvas.
        """
        text, ok = QInputDialog.getText(
            self, "Add Subtopic", "Enter subtopic:"
        )
        if not ok or not text.strip():
            return

        item = MovableTextItem(text.strip())
        item.setData(self.DATA_KEY_ROLE, "subtopic")
        item.setDefaultTextColor(QColor("#c4b5fd"))
        item.setFont(QFont("Segoe UI", 16))
        item.setZValue(10)

        # Position: below the last subtopic, or below the topic, or default
        subs = self._find_subtopic_items()
        if subs:
            last = subs[-1]
            new_x = last.pos().x()
            new_y = last.pos().y() + last.boundingRect().height() + 16
        else:
            topic = self._find_topic_item()
            if topic:
                new_x = topic.pos().x() + 20
                new_y = topic.pos().y() + topic.boundingRect().height() + 36
            else:
                vp = self.viewport().rect()
                scene_pt = self.mapToScene(
                    QPoint(int(vp.width() / 2 - 120), int(vp.height() / 2 + 20))
                )
                new_x = scene_pt.x()
                new_y = scene_pt.y()

        item.setPos(new_x, new_y)
        self.scene().addItem(item)
        # Set movability after the item is in the scene, based on the
        # currently active tool.
        item.setFlag(
            QGraphicsItem.ItemIsMovable,
            self.current_tool == config.MODE_SELECT,
        )
        self.undo_stack.append(("add", item))

    def request_new_canvas(self):
        """Emit a signal asking the main window to create a new page/canvas."""
        self.new_canvas_requested.emit()

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

        text_item = MovableTextItem(text)
        text_item.setDefaultTextColor(self.pen_color)
        text_item.setFont(QFont("Segoe UI", self.text_size, QFont.Bold))
        text_item.setPos(scene_pos)
        self.scene().addItem(text_item)
        # Set movability after the item is in the scene, based on the
        # currently active tool.
        text_item.setFlag(
            QGraphicsItem.ItemIsMovable,
            self.current_tool == config.MODE_SELECT,
        )
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
