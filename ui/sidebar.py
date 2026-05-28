from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QInputDialog, QMessageBox, QFrame
)
from PySide6.QtCore import Signal, Qt


class SidebarWidget(QWidget):
    page_selected = Signal(str)
    delete_page_requested = Signal(str)
    rename_page_requested = Signal(str, str)

    def __init__(self, page_manager, parent=None):
        super().__init__(parent)
        self.page_manager = page_manager
        self._renaming = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header
        header = QLabel("Outline Manager")
        header.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff; padding: 4px 0;")
        layout.addWidget(header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.08); max-height: 1px;")
        layout.addWidget(sep)

        # Slide Tree
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setColumnCount(1)
        self.tree_widget.setSelectionMode(QTreeWidget.SingleSelection)
        self.tree_widget.setEditTriggers(QTreeWidget.DoubleClicked | QTreeWidget.EditKeyPressed)
        self.tree_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree_widget.itemChanged.connect(self.on_item_renamed)
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: rgba(20, 20, 25, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 8px;
                color: #e2e2e8;
                padding: 5px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 6px 8px;
                border-radius: 4px;
                margin: 1px 2px;
            }
            QTreeWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.04);
            }
            QTreeWidget::item:selected {
                background-color: rgba(138, 43, 226, 0.25);
                color: #ffffff;
                border: 1px solid rgba(138, 43, 226, 0.5);
            }
        """)
        layout.addWidget(self.tree_widget)

        # Control Buttons
        btn_frame = QFrame()
        btn_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 25, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 8px;
            }
        """)
        btn_layout = QVBoxLayout(btn_frame)
        btn_layout.setContentsMargins(8, 8, 8, 8)
        btn_layout.setSpacing(6)

        row1 = QHBoxLayout()
        self.add_sibling_btn = QPushButton("+ Slide")
        self.add_sibling_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(138, 43, 226, 0.3);
                border: 1px solid rgba(138, 43, 226, 0.6);
                color: #ffffff;
                padding: 6px 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(138, 43, 226, 0.5);
            }
        """)
        self.add_sibling_btn.clicked.connect(self.add_sibling_slide)
        row1.addWidget(self.add_sibling_btn)

        self.add_child_btn = QPushButton("+ Subtopic")
        self.add_child_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 122, 255, 0.3);
                border: 1px solid rgba(0, 122, 255, 0.6);
                color: #ffffff;
                padding: 6px 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(0, 122, 255, 0.5);
            }
        """)
        self.add_child_btn.clicked.connect(self.add_child_subtopic)
        row1.addWidget(self.add_child_btn)
        btn_layout.addLayout(row1)

        self.rename_btn = QPushButton("Rename")
        self.rename_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                color: #d1d1d6;
                padding: 6px 10px;
                border-radius: 5px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.rename_btn.clicked.connect(self.rename_selected)
        btn_layout.addWidget(self.rename_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 50, 50, 0.25);
                border: 1px solid rgba(255, 50, 50, 0.4);
                color: #ff6666;
                padding: 6px 10px;
                border-radius: 5px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(220, 50, 50, 0.4);
                border: 1px solid rgba(255, 50, 50, 0.6);
            }
        """)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        btn_layout.addWidget(self.delete_btn)

        layout.addWidget(btn_frame)

        # Populate tree
        self.refresh_tree()

    def refresh_tree(self):
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
                item.setExpanded(True)
                add_nodes(node.children, item)

        add_nodes(self.page_manager.root_pages)

        if self.page_manager.active_page and self.page_manager.active_page.id in self.item_map:
            self.item_map[self.page_manager.active_page.id].setSelected(True)
        self.tree_widget.blockSignals(False)

    def on_selection_changed(self):
        if self._renaming:
            return
        selected_items = self.tree_widget.selectedItems()
        if selected_items:
            page_id = selected_items[0].data(0, Qt.UserRole)
            self.page_selected.emit(page_id)

    def on_item_double_clicked(self, item, column):
        self._renaming = True
        self.tree_widget.editItem(item, column)

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

    def rename_selected(self):
        selected_items = self.tree_widget.selectedItems()
        if selected_items:
            item = selected_items[0]
            self._renaming = True
            self.tree_widget.editItem(item, 0)

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
                ref_idx = next(i for i, n in enumerate(self.page_manager.root_pages) if n.id == insert_after_id)
                insert_idx = ref_idx + 1
            except StopIteration:
                pass

        can_add, err_msg = self.page_manager.can_add_root_page(insert_idx)
        if not can_add:
            QMessageBox.warning(self, "Limit Exceeded", err_msg)
            return

        title, ok = QInputDialog.getText(self, "New Slide Topic", "Enter slide/topic title:")
        if ok and title.strip():
            try:
                new_node = self.page_manager.create_page(title.strip(), insert_after_id=insert_after_id)
                self.page_manager.active_page = new_node
                self.refresh_tree()
                self.page_selected.emit(new_node.id)
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def add_child_subtopic(self):
        current_active = self.page_manager.active_page
        if not current_active:
            QMessageBox.warning(self, "Selection Required", "Please select a Topic page first.")
            return
        parent_node = current_active if not current_active.parent else current_active.parent
        title, ok = QInputDialog.getText(self, "New Subtopic", f"Add subtopic to '{parent_node.title}':")
        if ok and title.strip():
            new_node = self.page_manager.create_page(title.strip(), parent_id=parent_node.id)
            self.refresh_tree()
            self.page_selected.emit(parent_node.id)

    def on_delete_clicked(self):
        selected_items = self.tree_widget.selectedItems()
        if selected_items:
            page_id = selected_items[0].data(0, Qt.UserRole)
            self.delete_page_requested.emit(page_id)
