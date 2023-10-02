from dataclasses import dataclass
from typing import List


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
    edges: List[Edge]

    def __init__(
        self,
        rows: int,
        columns: int,
        cells: List[List[Cell]] = [],
        edges: List[Edge] = [],
    ):
        assert rows == len(cells)
        assert columns == len(cells[0])

        self.rows = rows
        self.columns = columns
        self.cells = cells
        self.edges = edges
        self.nodes = [[Node(i, j) for j in range(columns + 1)] for i in range(rows + 1)]
