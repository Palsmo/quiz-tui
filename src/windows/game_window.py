"""description for 'GameWindow'"""

# textual
from textual.containers import Container


TITLE = "Game"


class GameWindow(Container):
    """the game window"""

    DEFAULT_CLASSES = "window"

    def __init__(self) -> None:
        super().__init__()
