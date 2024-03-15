"""top level module for app"""
# rich
from rich.segment import Segment

# textual
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Footer, Label

# here
from .other import install_mark_border
from .notched_widgets import Notch, NotchedWidgets
from .windows.file_window import FileWindow, TITLE as FILE_TITLE
from .windows.game_window import GameWindow, TITLE as GAME_TITLE
from .windows.quiz_window import QuizWindow, TITLE as QUIZ_TITLE

_TITLE = r"""
 _____   _     _ _____  ______       ______ _     _  _____
|   __|  |     |   |     ____/  ___    /    |     |    /
 \____ \ \_____/ __|__  /_____        /     \_____/ __/__
"""

_QUOTE = "The formula for getting good at something is; \
repetition with intensity and tied together with persistence."

_SIGN = "-- Made by · Johannes Green · 2023"


class Banner(Widget):
    """a space that displays '_TITLE'"""

    COMPONENT_CLASSES = {
        "banner--default",
    }

    DEFAULT_CSS = """
        Banner > .banner--default {
            color: $text;
        }
    """

    __slots__ = [
        "_t",  # title lines
    ]

    def __init__(self, title: str) -> None:
        super().__init__()
        self._t = title.strip("\n").split("\n")
        self.styles.height = len(self._t)
        self.styles.width = len(self._t[0])

    def render_line(self, y: int) -> Strip:
        if y < self.size.height:
            seg = [Segment(self._t[y], self.get_component_rich_style("banner--default"))]
            return Strip(seg)
        # render blank after last row
        return Strip.blank(self.size.width)


class Home(Screen):
    """the app home screen"""

    BINDINGS = [
        # hacky display of 'TAB' in 'Footer' and get all to work right
        Binding("TAB", "switch_widget", "Switch"),
        Binding("tab", "switch_widget", priority=True),
    ]

    _NCH = [Notch(FILE_TITLE), Notch(QUIZ_TITLE), Notch(GAME_TITLE)]
    _WID = [FileWindow("quizes_test"), QuizWindow(), GameWindow()]
    _NW = NotchedWidgets(_NCH, _WID)

    @staticmethod
    def action_switch_widget() -> None:
        """switch to next notch + window"""
        Home._NW.switch_to_next()

    def compose(self) -> ComposeResult:
        with Container() as c:
            c.styles.align_horizontal = "center"
            c.styles.height = "auto"
            yield Banner(_TITLE)
        yield self._NW
        yield Footer()


class Info(Screen):
    """the app info screen"""

    BINDINGS = [
        Binding("escape", "app.pop_screen"),
        Binding("?", "app.pop_screen", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical() as v:
            v.styles.align = ("center", "middle")
            l1 = Label(_QUOTE)
            l1.styles.text_style = "italic"
            l1.styles.max_width = "1fr"
            l1.styles.margin = (0, 4)
            l2 = Label(_SIGN)
            l2.styles.margin = (1, 0, 0, 4)
            yield l1
            yield l2
        yield Footer()


class QuizTUI(App):
    """the app"""

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+t", "toggle_mode", "Toggle"),
        Binding("?", "push_screen('info')", "Info"),
    ]

    CSS_PATH = "styling/styling.tcss"

    SCREENS = {"info": Info()}

    install_mark_border()

    def _action_toggle_mode(self) -> None:
        self.dark = not self.dark

    def on_mount(self) -> None:
        """on app mount event"""
        self.install_screen(Home(), name="home")
        self.push_screen("home")
