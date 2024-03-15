"""description for 'NodeTree'"""

# stdlib
from __future__ import annotations
from collections import deque

# rich
from rich.segment import Segment

# textual
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding, _Bindings
from textual.containers import Horizontal
from textual.geometry import Region, Size
from textual.reactive import reactive
from textual.scroll_view import ScrollView
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Label

# here
import src.utils as util


_SPACE = 2


class Node:
    """label holding references to other labels"""

    __slots__ = [
        "lab",  # label
        "children",  # children
    ]

    def __init__(self, label: str, children: list[Node] | None = None) -> None:
        self.lab = label
        self.children = children

    def __str__(self):
        c = []
        if self.children:
            for e in self.children:
                c.append(e.__str__())
        return f"Node({self.lab}, {c if len(c) else None})"


class _NodeSliver:
    _CHILD_PREFIX_LAST = "└──"
    _CHILD_PREFIX_MIDDLE = "├──"
    _MARK_PREFIX = "▪"
    _PARENT_PREFIX_LAST = "│   "
    _PARENT_PREFIX_MIDDLE = "    "
    _SPACE = " "

    __slots__ = [
        "atr",  # attribute
        "dep",  # depth
        "end",  # ending
        "lab",  # label
        "par",  # parent
        "pre",  # prefix
        "sel",  # selected
    ]

    def __init__(
        self,
        depth: int,
        label: str,
        parent: _NodeSliver | None = None,
        ending=False,
        attribute: str | None = None,
    ) -> None:
        self.atr = attribute
        self.dep = depth
        self.end = ending
        self.lab = label
        self.par = parent
        self.pre = self._prefix()
        self.sel = False

    def _prefix(self) -> str:
        # if root-node
        if self.dep == 0:
            return _NodeSliver._MARK_PREFIX + _NodeSliver._SPACE
        # if child-node
        pre = deque()
        pre.appendleft(_NodeSliver._SPACE)
        pre.appendleft(
            _NodeSliver._CHILD_PREFIX_LAST
            if self.end
            else _NodeSliver._CHILD_PREFIX_MIDDLE
        )
        # prefix according to parent-nodes
        p = self.par
        while p and p.par:
            pre.appendleft(
                _NodeSliver._PARENT_PREFIX_MIDDLE
                if p.end
                else _NodeSliver._PARENT_PREFIX_LAST
            )
            p = p.par
        # complete prefix
        return "".join(pre)


class _NodeSliverStack(ScrollView):
    COMPONENT_CLASSES = {
        "_node-sliver-stack--default",
        "_node-sliver-stack--parent",
        "_node-sliver-stack--child-select",
    }

    DEFAULT_CSS = """
        _NodeSliverStack {
            scrollbar-background-active: $panel-darken-1;
            scrollbar-background-hover: $panel-darken-1;
            scrollbar-color-active: $primary-lighten-1;
            scrollbar-size-vertical: 1;
        }
        _NodeSliverStack > ._node-sliver-stack--default {
            color: $text-muted;
        }
        _NodeSliverStack > ._node-sliver-stack--parent {
            color: $text-disabled;
        }
        _NodeSliverStack > ._node-sliver-stack--child-select {
            background: $accent;
            text-style: italic;
        }
    """

    __slots__ = [
        "ns",  # '_NodeSliver' list
        "_typ",  # selection type
    ]

    def __init__(self, ns: list[_NodeSliver], typ: str):
        super().__init__()
        self.ns = ns
        self._typ = typ
        if typ == "none":
            self.styles.overflow_y = "hidden"
        else:
            self.virtual_size = Size(0, len(ns))
        self.styles.max_width = self._get_width()

    def _get_width(self) -> int:
        # calculate width
        f = self.ns[0]
        w = len(f.pre + f.lab)
        for i in range(1, len(self.ns)):
            c = self.ns[i]
            sw = len(c.pre + c.lab)  # width of a sliver
            if sw > w:
                w = sw
        if self._typ == "none":
            return w
        return w + _SPACE + self.styles.scrollbar_size_vertical

    @property
    def allow_vertical_scroll(self) -> bool:
        return False

    def render_line(self, y: int) -> Strip:
        ofs_x, ofs_y = self.scroll_offset
        y += ofs_y  # so correct row is accessed
        # styling on selected
        s = self.ns[y]
        st = None
        if s.atr == "parent":
            st = self.get_component_rich_style("_node-sliver-stack--parent")
        else:
            if s.sel:
                st = self.get_component_rich_style("_node-sliver-stack--child-select")
        # formulate and ship row
        d = self.get_component_rich_style("_node-sliver-stack--default")
        seg = [Segment(s.pre, d), Segment(s.lab, st if st else d)]
        return Strip(seg).crop(ofs_x, ofs_x + self.size.width)

    def update_row(self, i: int) -> None:
        """render row 'i' again"""
        e = self.ns[i]
        x = len(e.pre)
        y = i
        w = len(e.lab)
        h = i if i else 1
        region = Region(x, y, w, h).translate(-self.scroll_offset)
        self.refresh(region)


class _SelectableNodeSliverStack(Horizontal):
    _POINTER = "▶"

    _i = reactive(0)  # index for pointed row in '_NodeSliverStack'

    __slots__ = [
        "_aut",  # auto select
        "_hei",  # heigh cache
        "_ofs",  # offset to pointer symbol from widget top
        "_pnt",  # pointer
        "si",  # selected index(ex)
        "_typ",  # selection type
        "nss",  # '_NodeSliverStack' ref.
    ]

    def __init__(self, ns: list[_NodeSliver], typ: str, auto: bool) -> None:
        super().__init__()
        if typ != "none":
            self._aut = auto
            self._hei = self.size.height
            self._ofs = 0
            self._pnt = Label(self._POINTER)
            self._pnt.styles.margin = (0, 2, 0, 0)
            self.si = [] if typ == "multi" else None
        self._typ = typ
        self.nss = _NodeSliverStack(ns, typ)
        self.styles.max_width = self._get_width()

    def _on_resize(self, event: events.Resize) -> None:
        if self._typ == "none":
            return
        # let widget edge push pointer
        if self._ofs >= event.size.height:
            d = self._hei - event.size.height
            self._ofs -= d
            self._i -= d
        # counter adjusting where the 'NodeSliverStack' get shifed down relative to the pointer
        if (
            self._i + (self.size.height - self._ofs) > self.nss.virtual_size.height
            and event.size.height > self._hei
        ):
            self._i -= 1
        # renew cache
        self._hei = event.size.height

    def _get_width(self) -> int:
        # calculate width
        if self._typ == "none":
            return self.nss.styles.width
        return len(self._POINTER) + _SPACE + self.nss.styles.max_width.value

    def _watch__i(self, i: int) -> None:
        if self._typ == "none":
            return
        # update pointer offset
        self._pnt.styles.offset = (0, self._ofs)
        # scroll shortest distance to row 'i'
        self.nss.scroll_to_region(Region(0, i, 0, 1), animate=False, force=True)
        # if auto select
        if self._aut:
            self.pnt_select()

    def get_selected(self) -> list[str]:
        """return labels of selected nodes"""
        return [self.nss.ns[i].lab for i in self.si]

    def pnt_jump_end(self) -> None:
        """jump to tree end"""
        self._ofs = self.size.height - 1
        self._i = len(self.nss.ns) - 1

    def pnt_jump_start(self) -> None:
        """jump to tree start"""
        self._ofs = 0
        self._i = 0

    def pnt_next(self) -> None:
        """go down in tree"""
        if self._ofs < self.size.height - 1:
            self._ofs += 1
        if self._i < len(self.nss.ns) - 1:
            self._i += 1

    def pnt_previous(self) -> None:
        """go up in tree"""
        if self._ofs > 0:
            self._ofs -= 1
        if self._i > 0:
            self._i -= 1

    def pnt_select(self) -> None:
        """select a node in tree"""
        self.select(self._i)

    def select(self, i: int) -> None:
        """select row 'i'"""

        def update_sel_indexes(i: int, sel: bool, si: list[int]):
            (s, pos) = util.bin_search(si, i)
            if s and not sel:
                si.pop(pos)
            elif not s:
                si.insert(pos, i)

        ns = self.nss.ns  # '_NodeSliver' list
        c = ns[i]  # current selected '_NodeSliver'

        # single select
        if self._typ == "single":
            # if on parent, single don't allow multi select, deselect any
            if c.atr == "parent" and self._aut and self.si is not None:
                ns[self.si].sel = False
                self.nss.update_row(self.si)
                self.si = None
                return

            c.sel = not c.sel
            self.nss.update_row(i)

            # if no select or did not reselect same -> setup 'i' as selected index
            if self.si is None or self.si != i:
                if self.si is not None:  # on replace
                    ns[self.si].sel = False
                    self.nss.update_row(self.si)
            self.si = i

        # multi select
        else:
            si = self.si.copy()  # snapshot to work on (catching overselect)
            updates = [(i, not c.sel)]  # row indexes with future select states

            # parent select state -> child select state
            if c.atr == "parent":
                for _i in range(i + 1, len(ns)):
                    n = ns[_i]
                    if n.dep <= c.dep:
                        break
                    if not n.atr == "parent":
                        update_sel_indexes(_i, not c.sel, si)
                    updates.append((_i, not c.sel))
            else:
                update_sel_indexes(i, not c.sel, si)
            # if child unselect -> unselect parent(s)
            if c.sel:
                for _i in range(i - 1, -1, -1):
                    p = ns[_i]
                    if p.dep >= c.dep:  # if not direct family
                        continue
                    if not p.sel:  # if parent unselected
                        break
                    updates.append((_i, False))
                    c = p
            # check againsts selection limit
            if self.parent.update_select_count(len(si)):
                self.si = si
                for _i, s in updates:
                    ns[_i].sel = s
                    self.nss.update_row(_i)

    def compose(self) -> ComposeResult:
        if self._typ != "none":
            yield self._pnt
        yield self.nss


class _InfoBar(Widget):
    COMPONENT_CLASSES = {
        "_info-bar--default",
        "_info-bar--line",
        "_info-bar--error",
    }

    DEFAULT_CSS = """
        _InfoBar {
            height: 2;
            offset: -2 0;
        }
        _InfoBar > ._info-bar--default {
            color: $text-muted;
        }
        _InfoBar > ._info-bar--line {
            color: $text 15%;
        }
        _InfoBar > ._info-bar--error {
            background: $error 60%;
        }
    """

    n = reactive(0)  # count

    __slots__ = [
        "_err",  # error
        "lim",  # limit
        "_lim",  # limit as string
    ]

    def __init__(self, limit: int) -> None:
        super().__init__()
        self._err = False
        self.lim = limit
        self._lim = f"{'∞' if limit == -1 else str(limit)}"
        self.styles.width = self._get_width()

    def _watch_n(self) -> None:
        self.styles.width = self._get_width()

    def _get_width(self) -> int:
        return len(str(self.n)) + 1 + len(self._lim) + 3

    def flash_red(self):
        """flash red for a short duration"""
        region = Region(1, 1, self.size.width - 3, 1)

        def revert_err():
            self._err = False
            self.refresh(region)

        self._err = True
        self.refresh(region)
        self.set_timer(0.1, revert_err)

    def render_line(self, y: int) -> Strip:
        # styling on error
        ts = None # text style
        if self._err:
            ts = self.get_component_rich_style("_info-bar--error")
        else:
            ts = self.get_component_rich_style("_info-bar--default")
        # formulate and ship row
        seg = None
        bs = self.get_component_rich_style("_info-bar--line") # border style
        txt = f"{str(self.n)}/{self._lim}"
        if y == 0:
            seg = [Segment(f"{'─' * (self.size.width - 1)}┐", bs)]
        else:
            seg = [
                Segment(f"{' ' * (self.size.width - len(txt) - 2)}"),
                Segment(txt, ts),
                Segment(" │", bs),
            ]
        return Strip(seg)


class NodeTree(Horizontal):
    """displaying a tree of nodes"""

    _BINDINGS = [
        Binding("down", "next", "Down"),
        Binding("up", "previous", "Up"),
        Binding("end", "end", "End", show=False),
        Binding("home", "start", "Start", show=False),
        Binding("space", "select", "Select"),
    ]

    DEFAULT_CSS = """
        NodeTree {
            align-horizontal: right;
            layers: below above;
            margin: 1;
        }
    """

    __slots__ = [
        "_a_sel",  # auto select
        "_ib",  # '_InfoBar' ref.
        "_lim",  # selection limit
        "_snss",  # '_SelectableNodeSliverStack' ref.
        "_typ",  # selection type
    ]

    def __init__(
        self, nodes: list[Node], selection="multi", auto_select=False, limit=-1
    ) -> None:
        super().__init__()
        self._a_sel = auto_select
        self._lim = limit
        self._handle_selection(selection)
        self._ib = _InfoBar(limit)
        self._snss = _SelectableNodeSliverStack(
            self._nodes_to_slivers(nodes), selection, auto_select
        )
        self._typ = selection
        self.styles.max_height = len(self._snss.nss.ns)
        self.styles.max_width = self._snss.styles.max_width

    def _action_end(self) -> None:
        """jump to tree end"""
        self._snss.pnt_jump_end()

    def _action_next(self) -> None:
        """go down in tree"""
        self._snss.pnt_next()

    def _action_previous(self) -> None:
        """go up in tree"""
        self._snss.pnt_previous()

    def _action_select(self) -> None:
        """select a node in tree"""
        self._snss.pnt_select()

    def _action_start(self) -> None:
        """jump to tree start"""
        self._snss.pnt_jump_start()

    def _handle_selection(self, sel: str) -> None:
        """setup according to 'sel'"""
        match sel:
            case "multi":
                self._a_sel = False
                self.lim = self.lim if self.lim > 0 else -1
                self._bindings = _Bindings(self._BINDINGS)
                self.can_focus = True
            case "single":
                if self._a_sel:
                    # leave out 'select' keybinding
                    self._bindings = _Bindings(self._BINDINGS[:-1])
                self.can_focus = True
            case "none":
                self.lim = 0
            case _:
                raise ValueError(
                    "'NodeTree' parameter 'selection' got non of "
                    + f'["multi", "single", "none"] instead: "{sel}"'
                )

    @staticmethod
    def _nodes_to_slivers(nodes: list[Node]) -> list[_NodeSliver]:
        """work through list of 'Node'(s), unfold and parse into '_NodeSliver'(s)"""

        def _node_to_slivers(
            root: Node, depth=0, parent: _NodeSliver | None = None, ending=False
        ) -> _NodeSliver:
            """recursively yield '_NodeSliver'(s) translated from 'Node'(s)"""
            # if no child -> child or lone root
            if not root.children:
                if depth == 0:
                    ending = True
                yield _NodeSliver(depth, root.lab, parent, ending)
            else:  # if parent
                ns = _NodeSliver(depth, root.lab, parent, ending, attribute="parent")
                yield ns
                for i, c in enumerate(root.children):
                    end = False
                    if i == len(root.children) - 1:
                        end = True  # if last child
                    print(c.lab)
                    # explore
                    yield from _node_to_slivers(c, depth + 1, ns, end)

        # generate '_NodeSliver'(s) from every node, combine to one collection
        return [e for n in nodes for e in _node_to_slivers(n)]

    def get_selected(self) -> list[str]:
        """return labels of selected nodes"""
        return self._snss.get_selected()

    def update_select_count(self, count: int) -> bool:
        """try update select count"""
        if self._ib.lim == -1 or count <= self._ib.lim:
            self._ib.n = count
            return True
        self._ib.flash_red()
        return False

    def compose(self) -> ComposeResult:
        # '_SelectableNodeSliverStack'
        self._snss.styles.layer = "below"
        yield self._snss
        # '_InfoBar'
        if self._typ == "multi":
            self._ib.styles.layer = "above"
            yield self._ib
