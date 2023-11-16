from copy import deepcopy
from dataclasses import dataclass
from typing import List, DefaultDict, FrozenSet
from collections import defaultdict


@dataclass
class Cell:
    value: int
    row: int
    column: int

    # neighbors edges
    top: int = 0
    bottom: int = 0
    left: int = 0
    right: int = 0

    def edges(self) -> FrozenSet[int]:
        return frozenset([self.top, self.bottom, self.left, self.right])

    def __copy__(self):
        # Create a new instance of the Cell class with the same values
        return Cell(
            value=self.value,
            top=self.top,
            bottom=self.bottom,
            left=self.left,
            right=self.right,
            row=self.row,
            column=self.column,
        )

    def __hash__(self):
        return self.row * 31 + self.column

    def __deepcopy__(self, memo):
        # Create a deep copy of the Cell class
        return Cell(
            value=deepcopy(self.value, memo),
            top=deepcopy(self.top, memo),
            bottom=deepcopy(self.bottom, memo),
            left=deepcopy(self.left, memo),
            right=deepcopy(self.right, memo),
            row=deepcopy(self.row),
            column=deepcopy(self.column),
        )


@dataclass
class Node:
    row: int
    column: int

    top: int = 0
    bottom: int = 0
    left: int = 0
    right: int = 0

    _hash: int = 0

    def __hash__(self):
        if self._hash == 0:
            self._hash = self.row * 31 + self.column + 1

        return self._hash

    def __eq__(self, other):
        if self is other:
            return True
        else:
            return self.column == other.column and self.row == other.row

    def __copy__(self):
        # Create a new instance of the Node class with the same values
        return Node(
            row=self.row,
            column=self.column,
            top=self.top,
            bottom=self.bottom,
            left=self.left,
            right=self.right,
        )

    def __deepcopy__(self, memo):
        # Create a deep copy of the Node class
        return Node(
            row=deepcopy(self.row, memo),
            column=deepcopy(self.column, memo),
            top=deepcopy(self.top, memo),
            bottom=deepcopy(self.bottom, memo),
            left=deepcopy(self.left, memo),
            right=deepcopy(self.right, memo),
        )


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
        self.solved = False

    def deep_copy(self):
        cells = deepcopy(self.cells)
        # Create a new instance of the Board class
        new_board = Board(rows=self.rows, columns=self.columns, cells=cells)

        return new_board
