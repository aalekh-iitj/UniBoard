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
            "canvas_type": "plain",  # "plain" | "html" | "compiler" | "browser" | "presentation"
            "html_code": "<!-- Paste HTML here -->\n<div style='background: linear-gradient(135deg, #8a2be2, #4a00e0); color: white; padding: 40px; border-radius: 12px; font-family: sans-serif; text-align: center;'>\n  <h2>UniBoard HTML Presentation</h2>\n  <p>Render presentation pages and annotate on top of them.</p>\n</div>",
            "live_url": "https://www.google.com",
            "compiled_code": "# Write python code here\nprint('Hello UniBoard compiler!')\n",
            "compiler_lang": "Python",
            "ppt_path": ""
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
        self.default_page_id = None
        
        # Set up a default page
        default_page = self.create_page("Introduction")
        self.default_page_id = default_page.id

    def get_slide_counts(self):
        """Returns (above_count, below_count, total_count) of root pages."""
        if not self.root_pages:
            return 0, 0, 0
        try:
            default_idx = next(i for i, n in enumerate(self.root_pages) if n.id == self.default_page_id)
        except StopIteration:
            return 0, 0, len(self.root_pages)
            
        above = default_idx
        below = len(self.root_pages) - default_idx - 1
        return above, below, len(self.root_pages)

    def can_add_root_page(self, insert_index=None):
        """Checks if a root page can be added at the target insert_index."""
        above, below, total = self.get_slide_counts()
        if total >= 55:
            return False, "Maximum limit of 55 pages reached."
            
        if not self.root_pages:
            return True, ""
            
        try:
            default_idx = next(i for i, n in enumerate(self.root_pages) if n.id == self.default_page_id)
        except StopIteration:
            default_idx = 0

        # If insert_index is not specified, we append (which goes below default page)
        if insert_index is None:
            insert_index = len(self.root_pages)

        # If inserting before or at the default index, it shifts the default index right,
        # which increases the "above" count.
        if insert_index <= default_idx:
            if above >= 5:
                return False, "Cannot add more than 5 pages above the default page."
        else:
            if below >= 50:
                return False, "Cannot add more than 50 pages below the default page."
                
        return True, ""

    def create_page(self, title, parent_id=None, insert_after_id=None):
        """Creates a new page node, enforcing slide limits if it is a root page."""
        if parent_id:
            # Subtopic - no limit check needed as it doesn't count towards main slides limit
            parent_node = self.find_node_by_id(parent_id)
            if parent_node:
                new_node = PageNode(title, parent=parent_node)
                parent_node.add_child(new_node)
                return new_node

        # Root page insertion logic
        above, below, total = self.get_slide_counts()
        
        # Determine insertion index
        insert_idx = len(self.root_pages)
        if insert_after_id:
            try:
                ref_idx = next(i for i, n in enumerate(self.root_pages) if n.id == insert_after_id)
                insert_idx = ref_idx + 1
            except StopIteration:
                pass

        # Verify limits
        if self.default_page_id is not None:  # Skip limit checks on initialization of default page
            can_add, err_msg = self.can_add_root_page(insert_idx)
            if not can_add:
                raise ValueError(err_msg)

        new_node = PageNode(title)
        self.root_pages.insert(insert_idx, new_node)
            
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
