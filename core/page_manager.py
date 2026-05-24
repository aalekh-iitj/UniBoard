import uuid
from PySide6.QtWidgets import QGraphicsScene

class PageNode:
    def __init__(self, title, parent=None):
        self.id = str(uuid.uuid4())
        self.title = title
        self.parent = parent
        self.children = []
        
        # Each page has its own persistent QGraphicsScene
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QGraphicsScene().backgroundBrush())
        
        # Store metadata for other engines (like HTML views or compilers state)
        self.meta = {
            "html_code": "",
            "live_url": "",
            "compiled_code": "",
            "compiler_lang": "python"
        }

    def add_child(self, child_node):
        child_node.parent = self
        self.children.append(child_node)

    def remove_child(self, child_node):
        if child_node in self.children:
            self.children.remove(child_node)
            child_node.parent = None


class PageManager:
    def __init__(self):
        self.root_pages = []
        self.active_page = None
        
        # Set up a default page
        self.create_page("Introduction")

    def create_page(self, title, parent_id=None):
        """Creates a new page node and sets it as active if it's the first page."""
        if parent_id:
            parent_node = self.find_node_by_id(parent_id)
            if parent_node:
                new_node = PageNode(title, parent=parent_node)
                parent_node.add_child(new_node)
            else:
                new_node = PageNode(title)
                self.root_pages.append(new_node)
        else:
            new_node = PageNode(title)
            self.root_pages.append(new_node)
            
        if self.active_page is None:
            self.active_page = new_node
            
        return new_node

    def delete_page(self, page_id):
        """Deletes a page node by its ID."""
        node = self.find_node_by_id(page_id)
        if not node:
            return False
            
        # If node is active, select another active page first
        if self.active_page == node:
            sibling = self.get_adjacent_node(node)
            self.active_page = sibling

        if node.parent:
            node.parent.remove_child(node)
        else:
            if node in self.root_pages:
                self.root_pages.remove(node)
                
        return True

    def find_node_by_id(self, node_id, search_list=None):
        """Recursively searches for a node in the tree."""
        if search_list is None:
            search_list = self.root_pages

        for node in search_list:
            if node.id == node_id:
                return node
            result = self.find_node_by_id(node_id, node.children)
            if result:
                return result
        return None

    def get_adjacent_node(self, node):
        """Finds another node in the tree to focus on if the current one is deleted."""
        if node.parent:
            siblings = node.parent.children
            idx = siblings.index(node)
            if len(siblings) > 1:
                return siblings[idx - 1] if idx > 0 else siblings[idx + 1]
            return node.parent
        else:
            idx = self.root_pages.index(node)
            if len(self.root_pages) > 1:
                return self.root_pages[idx - 1] if idx > 0 else self.root_pages[idx + 1]
            return None

    def get_all_nodes_flat(self, list_to_search=None, result=None):
        """Returns a flat list of all nodes in pre-order traversal."""
        if result is None:
            result = []
        if list_to_search is None:
            list_to_search = self.root_pages

        for node in list_to_search:
            result.append(node)
            self.get_all_nodes_flat(node.children, result)
        return result
