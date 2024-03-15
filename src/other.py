"""diverse module with stuff connected to 'textual'"""

# rich
from rich.segment import Segment

# textual
from textual._border import BORDER_CHARS, BORDER_LOCATIONS
from textual.containers import Container
from textual.css.constants import VALID_BORDER
from textual.strip import Strip
from textual.widgets import Static
from textual.widget import Widget


class Center(Container):
    """center widget"""

    DEFAULT_CSS = """
        Center {
            align: center middle;
        }
    """


class Divider(Widget):
    """dividing line widget"""

    COMPONENT_CLASSES = {
        "divider--default"
    }

    DEFAULT_CSS = """
        Divider {
            width: 1;
        }
        Divider > .divider--default {
            color: $boost;
        }
    """

    def render_line(self, y: int) -> Strip:
        return Strip([Segment("│", self.get_component_rich_style("divider--default"))])


class Message(Static):
    """a space to display text with a mark"""

    DEFAULT_CSS = """
        Message {
            border: mark $boost;
            color: $text;
            max-width: 1fr;
            padding-right: 1;
            text-align: center;
            height: auto;
            width: auto;
        }
    """


def install_mark_border():
    """add a 'mark' border"""
    BORDER_CHARS.update({
        "mark": (
            (" ", " ", "∎"),
            (" ", " ", " "),
            (" ", " ", " "),
        )
    })
    BORDER_LOCATIONS.update({
        "mark": (
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
        )
    })
    VALID_BORDER.add("mark")
