from collections import namedtuple
from typing import List

Node = namedtuple("Node", ["row", "column"])
Edge = namedtuple("Edge", ["src", "dest"])


class Board:
    """This class represents a Sitherlink Board.
    The board is a grid of sizexsize points. This points can be connected by edges.
    The grid create (size - 1)x(size - 1) cells.
    """

    size: int
    cells: List[List[int]]
    edges: List[Edge]

    def __init__(self, size: int, cells: List[List[int]] = [], edges: List[Edge] = []):
        self.size = size
        self.cells = cells
        self.edges = edges
