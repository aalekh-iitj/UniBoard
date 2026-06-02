from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QInputDialog, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont


class SidebarWidget(QWidget):
    page_selected = Signal(str)
    add_page_requested = Signal(bool)
    delete_page_requested = Signal(str)
    rename_page_requested = Signal(str, str)

    def __init__(self, page_manager, parent=None):
        super().__init__(parent)
        self.page_manager = page_manager
        self._renaming = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(10)

        # ── Header ──────────────────────────────────────────────
        header = QLabel("Presentation Outline")
        header.setStyleSheet(
            "font-family: 'Segoe UI', sans-serif;"
            "font-size: 15px;"
            "font-weight: 600;"
            "color: #e8e8f0;"
            "padding: 2px 0 6px 2px;"
            "letter-spacing: 0.5px;"
        )
        layout.addWidget(header)

        # ── Tree Widget ─────────────────────────────────────────
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setColumnCount(1)
        self.tree_widget.setSelectionMode(QTreeWidget.SingleSelection)
        self.tree_widget.setEditTriggers(
            QTreeWidget.EditKeyPressed | QTreeWidget.DoubleClicked
        )

        tree_font = QFont("Segoe UI", 11)
        self.tree_widget.setFont(tree_font)

        self.tree_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree_widget.itemChanged.connect(self.on_item_renamed)

        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: rgba(18, 18, 24, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 8px;
                color: #dcdce4;
                padding: 6px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 7px 10px;
                border-radius: 5px;
                margin: 1px 3px;
            }
            QTreeWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
            QTreeWidget::item:selected {
                background-color: rgba(138, 43, 226, 0.28);
                color: #ffffff;
                border: 1px solid rgba(138, 43, 226, 0.55);
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                image: none;
                border-image: none;
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                image: none;
                border-image: none;
            }
        """)
        layout.addWidget(self.tree_widget)

        # ── Control Buttons ─────────────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.add_sibling_btn = QPushButton("➕  Add Slide")
        self.add_sibling_btn.setCursor(Qt.PointingHandCursor)
        self.add_sibling_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(138, 43, 226, 0.30);
                border: 1px solid rgba(138, 43, 226, 0.55);
                color: #ffffff;
                padding: 7px 12px;
                border-radius: 6px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(138, 43, 226, 0.50);
                border-color: rgba(138, 43, 226, 0.75);
            }
            QPushButton:pressed {
                background-color: rgba(138, 43, 226, 0.65);
            }
        """)
        self.add_sibling_btn.clicked.connect(self.add_sibling_slide)
        row1.addWidget(self.add_sibling_btn)

        self.add_child_btn = QPushButton("📎  Add Subtopic")
        self.add_child_btn.setCursor(Qt.PointingHandCursor)
        self.add_child_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 122, 255, 0.28);
                border: 1px solid rgba(0, 122, 255, 0.55);
                color: #ffffff;
                padding: 7px 12px;
                border-radius: 6px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(0, 122, 255, 0.48);
                border-color: rgba(0, 122, 255, 0.75);
            }
            QPushButton:pressed {
                background-color: rgba(0, 122, 255, 0.62);
            }
        """)
        self.add_child_btn.clicked.connect(self.add_child_subtopic)
        row1.addWidget(self.add_child_btn)

        layout.addLayout(row1)

        self.delete_btn = QPushButton("🗑  Delete Selected")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 50, 50, 0.22);
                border: 1px solid rgba(255, 60, 60, 0.40);
                color: #ff6b6b;
                padding: 7px 12px;
                border-radius: 6px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(220, 50, 50, 0.42);
                border-color: rgba(255, 60, 60, 0.65);
                color: #ff8888;
            }
            QPushButton:pressed {
                background-color: rgba(220, 50, 50, 0.58);
            }
        """)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        layout.addWidget(self.delete_btn)

        # ── Initial population ──────────────────────────────────
        self.refresh_tree()

    # ────────────────────────────────────────────────────────────
    #  Tree helpers
    # ────────────────────────────────────────────────────────────

    def refresh_tree(self):
        """Repopulate the tree from page_manager, preserving expansion."""
        self.tree_widget.blockSignals(True)
        self.tree_widget.clear()
        self.item_map = {}

        def add_nodes(nodes, parent_item=None):
            for node in nodes:
                item = QTreeWidgetItem()
                item.setText(0, node.title)
                item.setData(0, Qt.UserRole, node.id)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                if parent_item:
                    parent_item.addChild(item)
                else:
                    self.tree_widget.addTopLevelItem(item)
                self.item_map[node.id] = item
                add_nodes(node.children, item)

        add_nodes(self.page_manager.root_pages)

        # Expand everything
        self.tree_widget.expandAll()

        # Highlight the active page
        if (
            self.page_manager.active_page
            and self.page_manager.active_page.id in self.item_map
        ):
            self.item_map[self.page_manager.active_page.id].setSelected(True)

        self.tree_widget.blockSignals(False)

    # ────────────────────────────────────────────────────────────
    #  Slots
    # ────────────────────────────────────────────────────────────

    def on_selection_changed(self):
        if self._renaming:
            return
        selected_items = self.tree_widget.selectedItems()
        if selected_items:
            page_id = selected_items[0].data(0, Qt.UserRole)
            self.page_selected.emit(page_id)

    def on_item_double_clicked(self, item, column):
        """Let the edit triggers handle inline rename."""
        pass

    def on_item_renamed(self, item, column):
        self._renaming = False
        new_title = item.text(0).strip()
        if not new_title:
            page_id = item.data(0, Qt.UserRole)
            node = self.page_manager.find_node_by_id(page_id)
            if node:
                item.setText(0, node.title)
            return
        page_id = item.data(0, Qt.UserRole)
        self.rename_page_requested.emit(page_id, new_title)
        node = self.page_manager.find_node_by_id(page_id)
        if node:
            node.title = new_title

    # ────────────────────────────────────────────────────────────
    #  Page creation
    # ────────────────────────────────────────────────────────────

    def add_sibling_slide(self):
        current_active = self.page_manager.active_page
        insert_after_id = None
        if current_active:
            if current_active.parent:
                insert_after_id = current_active.parent.id
            else:
                insert_after_id = current_active.id

        insert_idx = len(self.page_manager.root_pages)
        if insert_after_id:
            try:
                ref_idx = next(
                    i
                    for i, n in enumerate(self.page_manager.root_pages)
                    if n.id == insert_after_id
                )
                insert_idx = ref_idx + 1
            except StopIteration:
                pass

        can_add, err_msg = self.page_manager.can_add_root_page(insert_idx)
        if not can_add:
            QMessageBox.warning(self, "Limit Exceeded", err_msg)
            return

        title, ok = QInputDialog.getText(
            self, "New Slide Topic", "Enter slide / topic title:"
        )
        if ok and title.strip():
            try:
                new_node = self.page_manager.create_page(
                    title.strip(), insert_after_id=insert_after_id
                )
                self.page_manager.active_page = new_node
                self.refresh_tree()
                self.page_selected.emit(new_node.id)
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def add_child_subtopic(self):
        current_active = self.page_manager.active_page
        if not current_active:
            QMessageBox.warning(
                self, "Selection Required", "Please select a Topic page first."
            )
            return

        parent_node = (
            current_active if not current_active.parent else current_active.parent
        )
        title, ok = QInputDialog.getText(
            self, "New Subtopic", f"Add subtopic to '{parent_node.title}':"
        )
        if ok and title.strip():
            new_node = self.page_manager.create_page(
                title.strip(), parent_id=parent_node.id
            )
            self.refresh_tree()
            self.page_selected.emit(parent_node.id)

    def on_delete_clicked(self):
        selected_items = self.tree_widget.selectedItems()
        if selected_items:
            page_id = selected_items[0].data(0, Qt.UserRole)
            self.delete_page_requested.emit(page_id)
