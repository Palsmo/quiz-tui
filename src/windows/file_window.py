"""description for 'FileWindow'"""

# stdlib
import os
import re

# textual
from textual.app import ComposeResult
from textual.containers import Horizontal

# here
from ..node_tree import Node, NodeTree
from ..other import Center, Divider, Message


PATH = "quizes_test"
TITLE = "File"


class FileWindow(Horizontal):
    """the file window"""

    DEFAULT_CLASSES = "window"

    _MSG = "Select a file to read quizes from"

    def __init__(self, root: str) -> None:
        super().__init__()
        self._n = self._build(root)  # node

    def _build(self, root: str) -> Node:
        c = []
        for e in os.listdir(root):
            path = f"{root}/{e}"
            if os.path.isdir(path):
                c.append(self._build(path))
            elif e.endswith(".yml"):
                c.append(Node(e, None))
        # regex: "./quizes/example" -> "example"
        return Node("/" + re.search(r"[^\/]+$", root).group(), c if len(c) else None)

    def compose(self) -> ComposeResult:
        # 'NodeTree'
        with Center():
            root = [Node("first", None), self._n]
            n = NodeTree(root, "single", auto_select=True, limit=15)
            yield n
        # 'Divider'
        with Center() as c:
            c.styles.width = 3
            d = Divider()
            d.styles.height = "70%"
            yield d
        # 'Message'
        with Center():
            m = Message(self._MSG)
            m.styles.margin = (0, 1, 0, 0)
            yield m
