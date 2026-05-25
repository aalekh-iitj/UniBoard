from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsRectItem,
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QInputDialog,
    QLabel, QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QGraphicsProxyWidget,
    QWidget
)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QTransform, QFont
from PySide6.QtCore import Qt, QPointF, QTimer, Signal, QPoint

import config
from core.handwriting import HandwritingWorker
from ui.embedded_widgets import HTMLRenderWidget, CompilerWidget, BrowserWidget

class WhiteboardCanvas(QGraphicsView):
    stroke_drawn = Signal()
    selection_changed = Signal()
    canvas_type_changed = Signal(str)  # Emits the new mode name

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
        
        # Active page node reference
        self.active_node = None
        
        # Tool state
        self.current_tool = config.MODE_PEN
        self.pen_color = QColor("#00ffcc")  # Default bright cyan neon
        self.pen_width = 3
        self.highlighter_color = QColor(255, 255, 0, 100)
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
        self.current_handwriting_strokes = []  # VIEWPORT coordinates
        self.current_handwriting_items = []    # Graphics items in scene
        self.handwriting_timer = QTimer(self)
        self.handwriting_timer.setSingleShot(True)
        self.handwriting_timer.setInterval(config.HANDWRITING_RECOGNITION_DELAY)
        self.handwriting_timer.timeout.connect(self.trigger_handwriting_recognition)

        # Embedded Widget proxy tracker
        self.current_mode_proxy = None
        self.embedded_widget = None

        # Canvas styling
        self.canvas_bg_color = QColor("#121214")
        self.grid_color = QColor("#1b1b1f")
        
        # Setup initial scene
        self.setScene(QGraphicsScene(self))
        self.scene().setSceneRect(-5000, -5000, 10000, 10000)
        self.update_background()

        # Build UI Overlays
        self.setup_viewport_overlays()

    def set_page_node(self, node):
        """Sets the active page node, updates the scene, and configures the embedded widget."""
        # Clean up old embedded widget
        self.clear_embedded_widget()

        self.active_node = node
        self.set_page_scene(node.scene)
        
        # Build new embedded widget based on metadata canvas_type
        self.load_embedded_widget_from_mode(node.meta.get("canvas_type", "plain"))
        
        # Update Agenda Text
        self.refresh_agenda_overlay()
        
        # Update interaction mode
        self.update_interaction_mode()

    def set_page_scene(self, scene):
        self.setScene(scene)
        scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.update_background()

    def update_background(self):
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
        
        # Update click pass-through on embedded widgets
        self.update_interaction_mode()

    # --- Viewport Overlays Implementation ---
    def setup_viewport_overlays(self):
        # 1. Floating Top Title Label
        self.title_overlay = QLabel(self)
        self.title_overlay.setAlignment(Qt.AlignCenter)
        self.title_overlay.setStyleSheet("""
            QLabel {
                background-color: rgba(22, 22, 26, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 18px;
                color: #ffffff;
                font-family: 'Outfit', 'Segoe UI';
                font-size: 16px;
                font-weight: bold;
                padding: 8px 24px;
            }
        """)
        self.title_overlay.setText("UniBoard")
        self.title_overlay.show()

        # 2. Left side Subtopics Agenda Container
        self.agenda_overlay = QWidget(self)
        self.agenda_layout = QVBoxLayout(self.agenda_overlay)
        self.agenda_layout.setContentsMargins(10, 10, 10, 10)
        self.agenda_layout.setSpacing(12)
        self.agenda_overlay.setStyleSheet("""
            QWidget#agendaContainer {
                background-color: rgba(22, 22, 26, 0.75);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
            QLabel.agendaTitle {
                color: #8a2be2;
                font-weight: bold;
                font-size: 12px;
                text-transform: uppercase;
                margin-bottom: 5px;
            }
            QLabel.agendaItem {
                color: #e2e2e8;
                font-family: 'Outfit';
                font-size: 13px;
                padding: 6px 12px;
                background-color: rgba(255, 255, 255, 0.04);
                border-radius: 6px;
                border-left: 3px solid rgba(138, 43, 226, 0.6);
            }
        """)
        self.agenda_overlay.setObjectName("agendaContainer")
        self.agenda_overlay.show()

        # 3. Bottom-Right Canvas Type Switcher
        self.selector_panel = QFrame(self)
        self.selector_panel.setStyleSheet("""
            QFrame {
                background-color: rgba(22, 22, 26, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: #d1d1d6;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.06);
            }
            QPushButton:checked {
                background-color: rgba(138, 43, 226, 0.8);
                color: white;
            }
        """)
        
        sel_layout = QHBoxLayout(self.selector_panel)
        sel_layout.setContentsMargins(6, 6, 6, 6)
        sel_layout.setSpacing(6)
        
        self.modes = [
            ("🎨 Canvas", "plain"),
            ("🌐 HTML Render", "html"),
            ("💻 Compiler", "compiler"),
            ("🧭 Browser", "browser")
        ]
        self.mode_buttons = {}
        for text, key in self.modes:
            btn = QPushButton(text)
            btn.setCheckable(True)
            if key == "plain":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, k=key: self.switch_canvas_mode(k))
            sel_layout.addWidget(btn)
            self.mode_buttons[key] = btn
            
        self.selector_panel.show()

    def update_overlay_widgets(self):
        """Maintains overlays positioned correctly inside viewport."""
        w = self.viewport().width()
        h = self.viewport().height()
        
        # Position Title Top Middle
        title_size = self.title_overlay.sizeHint()
        self.title_overlay.setGeometry(int((w - title_size.width()) / 2), 15, title_size.width(), title_size.height())

        # Position Agenda Middle Left
        agenda_size = self.agenda_overlay.sizeHint()
        # Cap size to prevent overflow
        self.agenda_overlay.setGeometry(15, int((h - agenda_size.height()) / 2), min(220, w - 30), agenda_size.height())

        # Position Selector Bottom Right
        sel_size = self.selector_panel.sizeHint()
        self.selector_panel.setGeometry(w - sel_size.width() - 20, h - sel_size.height() - 20, sel_size.width(), sel_size.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_overlay_widgets()

    def refresh_agenda_overlay(self):
        """Re‑reads node hierarchy to layout agenda items on left.
        Hide agenda when canvas type is not 'plain'."""
        # Clear layout
        for i in reversed(range(self.agenda_layout.count())):
            self.agenda_layout.itemAt(i).widget().setParent(None)

        if not self.active_node:
            self.agenda_overlay.hide()
            return

        # Hide agenda for non‑plain canvas types
        canvas_type = self.active_node.meta.get("canvas_type", "plain")
        if canvas_type != "plain":
            self.agenda_overlay.hide()
            # Still update title overlay
            self.title_overlay.setText(self.active_node.title)
            self.title_overlay.adjustSize()
            self.update_overlay_widgets()
            return

        self.agenda_overlay.show()

        # Active Topic title
        self.title_overlay.setText(self.active_node.title)
        self.title_overlay.adjustSize()

        # Subtopics header
        hdr = QLabel("Outline Agenda")
        hdr.setObjectName("agendaHeader")
        hdr.setProperty("class", "agendaTitle")
        self.agenda_layout.addWidget(hdr)

        # Distribute bullet points for subtopics
        subtopics = self.active_node.children
        if not subtopics:
            empty_lbl = QLabel("(No subtopics)")
            empty_lbl.setStyleSheet("color: #666677; font-style: italic;")
            self.agenda_layout.addWidget(empty_lbl)
        else:
            for node in subtopics:
                lbl = QLabel(node.title)
                lbl.setProperty("class", "agendaItem")
                lbl.setWordWrap(True)
                self.agenda_layout.addWidget(lbl)

        self.agenda_overlay.adjustSize()
        self.update_overlay_widgets()

    # --- Mode Switching & Embedding Layouts ---
    def switch_canvas_mode(self, mode_key):
        # Update check states
        for key, btn in self.mode_buttons.items():
            btn.setChecked(key == mode_key)
            
        if self.active_node:
            self.active_node.meta["canvas_type"] = mode_key
            self.clear_embedded_widget()
            self.load_embedded_widget_from_mode(mode_key)
            self.update_interaction_mode()
            self.canvas_type_changed.emit(mode_key)

    def clear_embedded_widget(self):
        if self.current_mode_proxy:
            try:
                self.scene().removeItem(self.current_mode_proxy)
            except Exception:
                pass
            self.current_mode_proxy.deleteLater()
            self.current_mode_proxy = None
        if self.embedded_widget:
            try:
                self.embedded_widget.deleteLater()
            except RuntimeError:
                pass  # C++ object already deleted by proxy container
            self.embedded_widget = None

    def load_embedded_widget_from_mode(self, mode_key):
        if not self.active_node or mode_key == "plain":
            return
            
        if mode_key == "html":
            self.embedded_widget = HTMLRenderWidget(self.active_node.meta.get("html_code", ""))
            self.embedded_widget.html_changed.connect(lambda html: self.active_node.meta.update({"html_code": html}))
        elif mode_key == "compiler":
            self.embedded_widget = CompilerWidget(self.active_node.meta.get("compiled_code", ""), self.active_node.meta.get("compiler_lang", "Python"))
            self.embedded_widget.code_changed.connect(self.on_compiler_changed)
        elif mode_key == "browser":
            self.embedded_widget = BrowserWidget(self.active_node.meta.get("live_url", "https://www.google.com"))
            self.embedded_widget.url_changed.connect(lambda url: self.active_node.meta.update({"live_url": url}))

        if self.embedded_widget:
            # Embed widget proxy in scene
            self.current_mode_proxy = self.scene().addWidget(self.embedded_widget)
            # Center at scene origin
            self.current_mode_proxy.setPos(-550, -320)

    def on_compiler_changed(self, code, lang):
        if self.active_node:
            self.active_node.meta["compiled_code"] = code
            self.active_node.meta["compiler_lang"] = lang

    def update_interaction_mode(self):
        """Allows interaction (clicks, scrolls, key inputs) if Select Tool is active, else drawing overrides clicks."""
        accept_clicks = (self.current_tool == config.MODE_SELECT)
        if self.current_mode_proxy:
            if accept_clicks:
                self.current_mode_proxy.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton | Qt.MiddleButton)
                if self.embedded_widget:
                    self.embedded_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            else:
                self.current_mode_proxy.setAcceptedMouseButtons(Qt.NoButton)
                if self.embedded_widget:
                    self.embedded_widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    # --- Mouse Graphics View & Drawing Engine ---
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if not self.grid_visible:
            return

        painter.save()
        painter.setPen(QPen(self.grid_color, 1))
        
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)
        right = int(rect.right())
        bottom = int(rect.bottom())

        for x in range(left, right, self.grid_size):
            painter.drawLine(x, top, x, bottom)
        for y in range(top, bottom, self.grid_size):
            painter.drawLine(left, y, right, y)
            
        painter.restore()

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
            super().mousePressEvent(event)
            return

        self.is_drawing = True
        self.last_point = scene_pos
        self.redo_stack.clear()

        # Create drawing items
        if self.current_tool == config.MODE_PEN:
            self.current_item = QGraphicsPathItem()
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            self.current_item.setPen(pen)
            path = QPainterPath(scene_pos)
            self.current_item.setPath(path)
            self.scene().addItem(self.current_item)
            
            if self.handwriting_enabled:
                self.handwriting_timer.stop()
                # Store Viewport coordinates! (event.pos())
                self.current_handwriting_strokes.append([(event.pos().x(), event.pos().y())])

        elif self.current_tool == config.MODE_HIGHLIGHTER:
            self.current_item = QGraphicsPathItem()
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
            text, ok = QInputDialog.getMultiLineText(self, "Add Text", "Enter text:")
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
            delta = event.pos() - self.pan_start
            self.pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return

        if not self.is_drawing:
            super().mouseMoveEvent(event)
            return

        if self.current_tool in (config.MODE_PEN, config.MODE_HIGHLIGHTER):
            path = self.current_item.path()
            path.lineTo(scene_pos)
            self.current_item.setPath(path)
            
            if self.current_tool == config.MODE_PEN and self.handwriting_enabled:
                # Viewport coordinates
                self.current_handwriting_strokes[-1].append((event.pos().x(), event.pos().y()))

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
        
        if self.current_item:
            self.undo_stack.append(("add", self.current_item))
            if self.current_tool == config.MODE_PEN and self.handwriting_enabled:
                self.current_handwriting_items.append(self.current_item)
                self.handwriting_timer.start()
            self.current_item = None
            self.stroke_drawn.emit()

    def erase_at_point(self, scene_pos):
        items = self.scene().items(scene_pos, Qt.IntersectsItemShape)
        for item in items:
            # Prevent deleting our page content widgets and backgrounds!
            if isinstance(item, QGraphicsProxyWidget):
                continue
            if isinstance(item, (QGraphicsPathItem, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem)):
                self.undo_stack.append(("remove", item))
                self.scene().removeItem(item)

    # --- Handwriting Recognition Thread Triggers ---
    def trigger_handwriting_recognition(self):
        if not self.current_handwriting_strokes:
            return

        strokes_to_send = list(self.current_handwriting_strokes)
        items_to_remove = list(self.current_handwriting_items)
        
        # Reset state
        self.current_handwriting_strokes = []
        self.current_handwriting_items = []

        # Find bounding box in Viewport coordinates
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
        
        # Run asynchronous worker thread
        self.worker = HandwritingWorker(strokes_to_send, items_to_remove, self.width(), self.height())
        # Pass mapped min_x, min_y back to scene coordinates
        self.worker.finished_recognition.connect(
            lambda txt, items: self.on_handwriting_finished(txt, items, min_x, min_y)
        )
        self.worker.start()

    def on_handwriting_finished(self, text, items, vp_x, vp_y):
        if not text or not text.strip():
            return
            
        # Clean up manual drawing strokes
        for item in items:
            if item in self.scene().items():
                self.scene().removeItem(item)
                for act, it in list(self.undo_stack):
                    if it == item:
                        self.undo_stack.remove((act, it))

        # Map viewport coordinates back to scene coordinates
        scene_pos = self.mapToScene(QPoint(int(vp_x), int(vp_y)))

        # Add text element in scene space
        text_item = QGraphicsTextItem(text)
        text_item.setDefaultTextColor(self.pen_color)
        text_item.setFont(QFont("Outfit", 18, QFont.Bold))
        text_item.setPos(scene_pos)
        text_item.setFlag(QGraphicsTextItem.ItemIsMovable)
        text_item.setFlag(QGraphicsTextItem.ItemIsSelectable)
        self.scene().addItem(text_item)
        self.undo_stack.append(("add", text_item))

    # --- Undo / Redo Engine ---
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
