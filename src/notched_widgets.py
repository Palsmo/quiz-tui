"""description for 'NotchedWidgets'"""

# rich
from rich.segment import Segment

# textual
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.strip import Strip
from textual.walk import walk_depth_first
from textual.widget import Widget
from textual.widgets import ContentSwitcher, Static


class Notch(Widget):
    """notch widget"""

    __slots__ = [
        "tit",  # title
    ]

    def __init__(self, title: str) -> None:
        super().__init__()
        self.tit = title


class _NotchSliver(Widget):
    """a line render of a notch"""

    COMPONENT_CLASSES = {
        "_notch-sliver--default",
    }

    DEFAULT_CSS = """
        _NotchSliver {
            padding: 1;
            width: 3;
        }
        _NotchSliver.select {
            background: $accent;
        }
        _NotchSliver > ._notch-sliver--default {
            color: $text;
        }
    """

    _sel = reactive(False)  # selected

    __slots__ = [
        "_txt",  # title
    ]

    def __init__(self, notch: Notch) -> None:
        super().__init__()
        self._txt = notch.tit
        self.styles.height = len(self._txt) + 2

    def select(self) -> None:
        """select this notch"""
        self._sel = not self._sel
        if self._sel:
            self.add_class("select")
        else:
            self.remove_class("select")

    def render_line(self, y: int) -> Strip:
        if y < self.size.height:
            seg = [Segment(self._txt[y], self.get_component_rich_style(
                "_notch-sliver--default"))]
            return Strip(seg)
        # render blank after last row
        return Strip.blank(self.size.width)


class _NotchSliverStack(Vertical):

    DEFAULT_CSS = """
        _NotchSliverStack {
            width: auto;
        }
    """

    __slots__ = [
        "ns",  # '_NotchSliver' list
    ]

    def __init__(self, ns: list[_NotchSliver]):
        super().__init__()
        self.ns = ns

    def compose(self) -> ComposeResult:
        s = Static(classes="background")
        s.styles.height = "1fr"
        yield from self.ns
        yield s


class NotchedWidgets(Horizontal):
    """manager of notch-widget pairs to switch between"""

    DEFAULT_CSS = """
        NotchedWidgets {
            background: $surface;
            margin: 1 0 1 1;
        }
    """

    # current: reactive[str | None] = reactive(None)

    __slots__ = [
        "_i",    # active notch-widget
        "_nss",  # '_NotchSliverStack' ref.
        "_wid",  # widgets
        "_cs",   # 'ContentSwitcher' ref.
    ]

    def __init__(self, notches: list[Notch], widgets: list[Widget]) -> None:
        super().__init__()
        if len(notches) != len(widgets):
            raise ValueError("the lists given should have matching length")
        self._i = 0
        self._nss = _NotchSliverStack(self._notch_to_sliver(notches))
        self._wid = widgets
        # set id & select first widget + notch
        for i, w in enumerate(widgets):
            w.id = f"notched-widgets--wid-{str(i)}"  # set id
        self._cs = ContentSwitcher(*widgets, initial=widgets[0].id)
        self._nss.ns[0].select()

    @staticmethod
    def _notch_to_sliver(nl: list[Notch]) -> list[_NotchSliver]:
        return [_NotchSliver(n) for n in nl]

    def switch_to_next(self) -> None:
        """switch to next notch + widget"""
        self._nss.ns[self._i].select()  # deselect old
        self._i = (self._i + 1) % len(self._nss.ns)  # increment '_i' in a loop
        self._nss.ns[self._i].select()  # select new
        c = self._wid[self._i]
        self._cs.current = c.id
        for child in walk_depth_first(c, Widget):
            if child.can_focus:
                child.focus()
                break

    # def watch_current(self, old: str | None, new: str | None) -> None:

    def compose(self) -> ComposeResult:
        yield self._nss
        yield self._cs
