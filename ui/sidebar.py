from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QLineEdit, QHeaderView
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
        self.header_label = QLabel("Topics & Outline")
        self.header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        self.layout.addWidget(self.header_label)

        # Slide Tree
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setColumnCount(1)
        self.tree_widget.setSelectionMode(QTreeWidget.SingleSelection)
        self.tree_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.layout.addWidget(self.tree_widget)

        # Control Buttons
        btn_layout = QHBoxLayout()
        self.add_sibling_btn = QPushButton("Add Page")
        self.add_sibling_btn.clicked.connect(lambda: self.add_page_requested.emit(False))
        
        self.add_child_btn = QPushButton("Add Subpage")
        self.add_child_btn.clicked.connect(lambda: self.add_page_requested.emit(True))
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        
        btn_layout.addWidget(self.add_sibling_btn)
        btn_layout.addWidget(self.add_child_btn)
        btn_layout.addWidget(self.delete_btn)
        self.layout.addLayout(btn_layout)

        # Populate initially
        self.refresh_tree()

    def refresh_tree(self):
        """Re-populates the QTreeWidget from the page manager."""
        self.tree_widget.blockSignals(True)
        self.tree_widget.clear()
        
        # Keep track of Node ID -> QTreeWidgetItem mapping
        self.item_map = {}

        def add_nodes(nodes, parent_item=None):
            for node in nodes:
                item = QTreeWidgetItem()
                item.setText(0, node.title)
                item.setData(0, Qt.UserRole, node.id)
                
                if parent_item:
                    parent_item.addChild(item)
                else:
                    self.tree_widget.addTopLevelItem(item)
                
                self.item_map[node.id] = item
                
                # Expand items
                item.setExpanded(True)
                
                # Recurse children
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
        """Allows double click inline renaming."""
        self.tree_widget.editItem(item, column)
        
    def on_delete_clicked(self):
        selected_items = self.tree_widget.selectedItems()
        if selected_items:
            page_id = selected_items[0].data(0, Qt.UserRole)
            self.delete_page_requested.emit(page_id)

    def rename_active_node(self, new_title):
        """Helper to rename nodes directly from double clicks or properties editor."""
        selected_items = self.tree_widget.selectedItems()
        if selected_items:
            page_id = selected_items[0].data(0, Qt.UserRole)
            self.rename_page_requested.emit(page_id, new_title)
