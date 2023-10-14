from dataclasses import dataclass
from typing import List, DefaultDict, Callable
from collections import defaultdict
from threading import Thread


@dataclass
class Cell:
    value: int

    # neighbors edges
    top: int = 0
    bottom: int = 0
    left: int = 0
    right: int = 0


@dataclass
class Node:
    row: int
    column: int

    top: int = 0
    bottom: int = 0
    left: int = 0
    right: int = 0

    def __key(self):
        return (self.row, self.column)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.__key() == other.__key()
        return NotImplemented


@dataclass
class Edge:
    src: Node
    dest: Node


class Board:
    """This class represents a Sitherlink Board.
    The board is a grid of points. This points can be connected by edges.
    The grid create rowsxcolumns cells.
    """

    rows: int
    columns: int
    nodes: List[List[Node]]
    cells: List[List[Cell]]
    graph: DefaultDict[Node, List[Node]]

    def __init__(
        self,
        rows: int,
        columns: int,
        cells: List[List[Cell]] = [],
    ):
        assert rows == len(cells)
        assert columns == len(cells[0])

        self.rows = rows
        self.columns = columns
        self.cells = cells
        self.graph = defaultdict(list)
        self.nodes = [[Node(i, j) for j in range(columns + 1)] for i in range(rows + 1)]


class Worker(Thread):
    def __init__(self, task: Callable, callback: Callable):
        super().__init__()
        self.setDaemon(True)
        self.task = task
        self.callback = callback

    def run(self):
        self.task()

        self.callback(self)
