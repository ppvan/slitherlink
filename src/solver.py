from typing import List, MutableSet, Callable, FrozenSet
from collections import defaultdict
import pycosat
import time
import sys
from dataclasses import dataclass
from models import Board, Node
from functools import cache
import threading


@dataclass
class Statistics:
    time: float = 0
    clauses: int = 0
    variables: int = 0
    retried: int = 0

    def __init__(self):
        self.time = 0
        self.clauses = 0
        self.variables = 0
        self.retried = 0

    def reset(self):
        self.time = 0
        self.clauses = 0
        self.variables = 0
        self.retried = 0


class Solver:
    def __init__(
        self,
        board: Board,
        cancel_event: threading.Event = None,
    ):
        self.board = board
        self.cancel_event = cancel_event
        self.stats = Statistics()

        self.subcribers = []
        pass

    def add_partial_solution_callback(
        self, callback: Callable[[Board, Statistics], None]
    ):
        self.subcribers.append(callback)

    def solve(self) -> Board:
        self.assign_edges_index()

        contraints = self.encode_rules()
        m = self.board.rows
        n = self.board.columns
        total_time = 0
        variables = (m + 1) * n + (n + 1) * m
        clauses = len(contraints)
        retried = 0

        start = time.perf_counter()
        for test_solution in pycosat.itersolve(contraints):
            clauses += 1  # one more clause for each iteration
            retried += 1
            # only account for SAT solving time
            total_time += time.perf_counter() - start

            # Check for cancellation
            if self.cancel_event and self.cancel_event.is_set():
                break

            # Update stats
            self.stats.clauses = clauses
            self.stats.variables = variables
            self.stats.time = total_time
            self.stats.retried = retried

            if self.subcribers:
                self._extract_solution(test_solution)
                for callback in self.subcribers:
                    callback(self.board, self.stats)

            # only account for SAT solving time
            start = time.perf_counter()
            if self._validate(test_solution):
                self._extract_solution(test_solution)
                self.board.solved = True
                break

        return self.board

    def _dfs(self, node: Node, visited: MutableSet[Node]):
        visited.add(node)
        for neighbor in self.board.graph[node]:
            if neighbor not in visited:
                self._dfs(neighbor, visited)

    def _validate(self, ans):
        models = frozenset(x for x in ans if x > 0)
        for row in self.board.cells:
            for cell in row:
                if cell.edges().issubset(models):
                    return False

        self._extract_solution(ans)

        start = next(
            (node for node, neighbors in self.board.graph.items() if neighbors), None
        )
        visited = set()
        self._dfs(start, visited)

        if len(visited) != len(self.board.graph):
            return False

        return True

    def assign_edges_index(self):
        m = self.board.rows
        n = self.board.columns
        cells = self.board.cells
        nodes = self.board.nodes

        for i in range(m):
            for j in range(n):
                cells[i][j].top = i * n + j + 1
                cells[i][j].bottom = (i + 1) * n + j + 1
                cells[i][j].left = (m + 1) * n + j * m + i + 1
                cells[i][j].right = (m + 1) * n + (j + 1) * m + i + 1

        for i in range(m + 1):
            for j in range(n + 1):
                nodes[i][j].left = i * n + j if j > 0 else 0
                nodes[i][j].right = i * n + j + 1 if j < n else 0
                nodes[i][j].top = (m + 1) * n + j * m + i if i > 0 else 0
                nodes[i][j].bottom = (m + 1) * n + j * m + i + 1 if i < m else 0

    def encode_rules(self):
        self.contraints = (
            self._cell_contraints() + self._node_contraints() + self._corners_rules()
        )
        return self.contraints

    @cache
    def do_extract_solution(self, model: FrozenSet[int]):
        nodes = self.board.nodes
        m = self.board.rows
        n = self.board.columns

        graph = defaultdict(list)
        for i in range(m):
            for j in range(n):
                top = i * n + j + 1
                bottom = (i + 1) * n + j + 1
                left = (m + 1) * n + j * m + i + 1
                right = (m + 1) * n + (j + 1) * m + i + 1

                if top in model:
                    graph[nodes[i][j]].append(nodes[i][j + 1])
                    graph[nodes[i][j + 1]].append(nodes[i][j])

                if bottom in model:
                    graph[nodes[i + 1][j]].append(nodes[i + 1][j + 1])
                    graph[nodes[i + 1][j + 1]].append(nodes[i + 1][j])
                    pass
                if left in model:
                    graph[nodes[i][j]].append(nodes[i + 1][j])
                    graph[nodes[i + 1][j]].append(nodes[i][j])
                    pass
                if right in model:
                    graph[nodes[i][j + 1]].append(nodes[i + 1][j + 1])
                    graph[nodes[i + 1][j + 1]].append(nodes[i][j + 1])
                    pass
        return graph

    def _extract_solution(self, model: List[int]):
        clean_model = frozenset(x for x in model if x > 0)
        self.board.graph = self.do_extract_solution(clean_model)

    def _cell_contraints(self):
        atmosts = [zero, one, two, three]
        constraints = []
        for i in range(self.board.rows):
            for j in range(self.board.columns):
                cell = self.board.cells[i][j]
                if cell.value == -1:
                    cnf = [[-cell.top, -cell.bottom, -cell.left, -cell.right]]
                    constraints.extend(cnf)
                    continue
                else:
                    cnf = atmosts[cell.value](
                        cell.top, cell.bottom, cell.left, cell.right
                    )

                    constraints.extend(cnf)
        return constraints

    def _node_contraints(self):
        constraints = []
        for i in range(self.board.rows + 1):
            for j in range(self.board.columns + 1):
                node = self.board.nodes[i][j]
                e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]
                constraints.extend(zero_or_two(e1, e2, e3, e4))

        return constraints

    def _heuristic_rules(self):
        contraints = []
        for i in range(1, self.board.rows - 1):
            for j in range(1, self.board.columns - 1):
                cell = self.board.cells[i][j]
                _, e2, e3, _ = [cell.top, cell.right, cell.bottom, cell.left]
                if cell.value == -1:
                    continue
                else:
                    if cell.value == 1:
                        tl_cell = self.board.cells[i - 1][j - 1]
                        e5, e6 = tl_cell.right, tl_cell.bottom
                        cnf = [[e5, -e6, -e2], [e5, -e6, -e3]]
                    contraints.extend(cnf)
        pass

    def _corners_rules(self):
        """https://en.wikipedia.org/wiki/Slitherlink?useskin=vector#Corners"""
        contraints = []
        corners = [
            self.board.cells[0][0],
            self.board.cells[0][self.board.columns - 1],
            self.board.cells[self.board.rows - 1][0],
            self.board.cells[self.board.rows - 1][self.board.columns - 1],
        ]
        cornerlines = [
            [
                self.board.cells[0][0].top,
                self.board.cells[0][0].left,
            ],
            [
                self.board.cells[0][self.board.columns - 1].top,
                self.board.cells[0][self.board.columns - 1].right,
            ],
            [
                self.board.cells[self.board.rows - 1][0].bottom,
                self.board.cells[self.board.rows - 1][0].left,
            ],
            [
                self.board.cells[self.board.rows - 1][self.board.columns - 1].bottom,
                self.board.cells[self.board.rows - 1][self.board.columns - 1].right,
            ],
        ]

        for index, corner in enumerate(corners):
            if corner.value == 1:
                contraints.extend([[-line] for line in cornerlines[index]])
            elif corner.value == 3:
                contraints.extend([[line] for line in cornerlines[index]])
            else:
                pass

        return contraints


def zero(e1, e2, e3, e4):
    """
    All e1, e2, e3 and e4 must be false.
    """
    return [[-e1], [-e2], [-e3], [-e4]]


def one(e1, e2, e3, e4):
    """
    The "exactly one" constraint can be expressed as
    * Amongst any two of booleans, at least one must be false.
    * Atleast one of the booleans is true.
    """
    return [
        [-e1, -e2],
        [-e1, -e3],
        [-e1, -e4],
        [-e2, -e3],
        [-e2, -e4],
        [-e3, -e4],
        [e1, e2, e3, e4],
    ]


def two(e1, e2, e3, e4):
    """
    Amongst any three booleans, at least one must be true,
    and atleast one must be false.
    """
    return [
        [e2, e3, e4],
        [e1, e3, e4],
        [e1, e2, e4],
        [e1, e2, e3],
        [-e2, -e3, -e4],
        [-e1, -e3, -e4],
        [-e1, -e2, -e4],
        [-e1, -e2, -e3],
    ]


def three(e1, e2, e3, e4):
    """
    Amongst any two booleans, at least one must be true. This ensures
    that there are at least three true booleans.
    Also add a clause that ensures at least one of them must be false.
    Together they ensure the "exactly three correct"
    """
    return [
        [e1, e2],
        [e1, e3],
        [e1, e4],
        [e2, e3],
        [e2, e4],
        [e3, e4],
        [-e1, -e2, -e3, -e4],
    ]


def zero_or_two(e1, e2, e3, e4):
    true = sys.maxsize
    false = -true
    edges = []
    for item in [e1, e2, e3, e4]:
        if item == 0:
            edges.append(false)
        else:
            edges.append(item)
    e1, e2, e3, e4 = edges
    generic_contraints = [
        [-e1, -e2, -e3],
        [-e1, -e2, -e4],
        [-e1, -e3, -e4],
        [-e2, -e3, -e4],
        [-e1, e2, e3, e4],
        [e1, -e2, e3, e4],
        [e1, e2, -e3, e4],
        [e1, e2, e3, -e4],
    ]

    contraints = []
    for row in generic_contraints:
        if true in row:
            continue

        contraints.append([x for x in row if x != false])

    return contraints
