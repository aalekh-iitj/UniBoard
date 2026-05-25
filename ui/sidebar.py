from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QInputDialog, QMessageBox
)
from PySide6.QtCore import Signal, Qt

class SidebarWidget(QWidget):
    page_selected = Signal(str)  # Emits the selected page_id
    add_page_requested = Signal(bool)  # Emits True for subpage, False for sibling page
    delete_page_requested = Signal(str)
    rename_page_requested = Signal(str, str)

    def __init__(self, page_manager, parent=None):
        super().__init__(parent)
        self.page_manager = page_manager

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Header Label
        self.header_label = QLabel("Presentation Outline")
        self.header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        self.layout.addWidget(self.header_label)

        # Slide Tree
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setColumnCount(1)
        self.tree_widget.setSelectionMode(QTreeWidget.SingleSelection)
        # Enable inline editing
        self.tree_widget.setEditTriggers(QTreeWidget.DoubleClicked | QTreeWidget.EditKeyPressed)
        self.tree_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree_widget.itemChanged.connect(self.on_item_renamed)
        self.layout.addWidget(self.tree_widget)

        # Control Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(6)

        row1 = QHBoxLayout()
        self.add_sibling_btn = QPushButton("Add Slide")
        self.add_sibling_btn.clicked.connect(self.add_sibling_slide)

        self.add_child_btn = QPushButton("Add Subtopic")
        self.add_child_btn.clicked.connect(self.add_child_subtopic)
        row1.addWidget(self.add_sibling_btn)
        row1.addWidget(self.add_child_btn)
        btn_layout.addLayout(row1)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setStyleSheet("background-color: rgba(220, 50, 50, 0.4); border: 1px solid #ff3333;")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        btn_layout.addWidget(self.delete_btn)

        self.layout.addLayout(btn_layout)

        # Populate tree
        self.refresh_tree()

    def refresh_tree(self):
        """Re-populates the QTreeWidget from the page manager."""
        self.tree_widget.blockSignals(True)
        self.tree_widget.clear()
        self.item_map = {}

        def add_nodes(nodes, parent_item=None):
            for node in nodes:
                item = QTreeWidgetItem()
                item.setText(0, node.title)
                item.setData(0, Qt.UserRole, node.id)
                # Make item editable
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                if parent_item:
                    parent_item.addChild(item)
                else:
                    self.tree_widget.addTopLevelItem(item)
                self.item_map[node.id] = item
                item.setExpanded(True)
                add_nodes(node.children, item)

        add_nodes(self.page_manager.root_pages)
        # Highlight active page
        if self.page_manager.active_page and self.page_manager.active_page.id in self.item_map:
            self.item_map[self.page_manager.active_page.id].setSelected(True)
        self.tree_widget.blockSignals(False)

    def on_selection_changed(self):
        selected_items = self.tree_widget.selectedItems()
        if selected_items:
            page_id = selected_items[0].data(0, Qt.UserRole)
            self.page_selected.emit(page_id)

    def on_item_double_clicked(self, item, column):
        """Inline double click rename (handled by default edit trigger)."""
        pass

    def on_item_renamed(self, item, column):
        """Emit rename signal when a tree item title changes."""
        new_title = item.text(0)
        page_id = item.data(0, Qt.UserRole)
        self.rename_page_requested.emit(page_id, new_title)
        # Update the underlying page node title
        node = self.page_manager.find_node_by_id(page_id)
        if node:
            node.title = new_title

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
