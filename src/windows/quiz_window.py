"""description for 'QuizWindow'"""

# textual
# from textual.app import ComposeResult
from textual.containers import Container

# here
from ..node_tree import Node


TITLE = "Quiz"


class QuizWindow(Container):
    """the quiz window"""

    DEFAULT_CLASSES = "window"

    _MSG = "Select the part to quiz"

    _N: Node = None

    def __init__(self) -> None:
        super().__init__()

    # def compose(self) -> ComposeResult:
    # 	pass
    # 	with Container() as c3:
    # 		c3.styles.align = ("center")
