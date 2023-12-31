from typing import List, MutableSet, Callable, FrozenSet
from collections import defaultdict
import sys
from dataclasses import dataclass
from models import Board, Node
from functools import cache
import threading
from utils import measure_time
from pysat.solvers import Solver
import time


@dataclass
class Statistics:
    acum_time: float = 0
    clauses: int = 0
    variables: int = 0
    retried: int = 0

    # def __init__(self):
    #     self.acum_time = 0
    #     self.clauses = 0
    #     self.variables = 0
    #     self.retried = 0

    def reset(self):
        self.acum_time = 0
        self.clauses = 0
        self.variables = 0
        self.retried = 0


class MySolver:
    def __init__(
        self,
        board: Board,
        cancel_event: threading.Event = None,
    ):
        self.board = board
        self.cancel_event = cancel_event
        self.stats = Statistics()

        self.assumpsions = []
        self.hint_clauses = []
        self.subcribers = []
        pass

    def add_partial_solution_callback(
        self, callback: Callable[[Board, Statistics], None]
    ):
        self.subcribers.append(callback)

    @measure_time
    def solve(self) -> Board:
        start = time.perf_counter()
        self.assign_edges_index()

        contraints = self.encode_rules()
        with Solver(
            "g4",
            bootstrap_with=contraints,
            use_timer=True,
            warm_start=True,
            incr=True,
        ) as solver:
            for retried, test_solution in enumerate(
                solver.enum_models(assumptions=self.assumpsions),
                start=1,
            ):
                # Update stats
                self.stats.clauses = solver.nof_clauses()
                self.stats.variables = solver.nof_vars()
                self.stats.acum_time += solver.time() + time.perf_counter() - start
                self.stats.retried = retried

                # Check for cancellation
                if self.cancel_event and self.cancel_event.is_set():
                    break

                if self.subcribers:
                    self._extract_solution(test_solution)
                    for callback in self.subcribers:
                        callback(self.board, self.stats)

                start = time.perf_counter()

                for hints in self.hint_clauses:
                    solver.add_clause(hints)
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

        loops = self.extract_loops(models)

        if len(loops) > 1:
            # self.hint_clauses.append([-x for x in self.extract_loop_edge(visited)])
            return False

        return True

    def extract_loops(self, models):
        loops = []

        def get_start():
            return next(
                (
                    node
                    for node, neighbors in self.board.graph.items()
                    if neighbors and node not in all_visisted
                ),
                None,
            )

        all_visisted = set()
        start = get_start()

        while start:
            visited = set()
            self._dfs(start, visited)
            loops.append(visited)
            hints = set()
            for node in visited:
                edges = [
                    x
                    for x in [node.top, node.bottom, node.left, node.right]
                    if x in models
                ]
                hints.update(edges)

            self.hint_clauses.append([-x for x in hints])
            all_visisted.update(visited)
            start = get_start()

        return loops

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
            self._cell_contraints()
            + self._node_contraints()
            + self._corners_rules()
            + self._break_smalloop()
        )

        tmp = self._heuristic_rules()
        for cnf in tmp:
            if len(cnf) == 1:
                self.assumpsions.append(cnf[0])

        self.assumpsions = list(frozenset(self.assumpsions))

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
        """Dù có cho bao nhiêu luật đi nữa hiệu quả vẫn không tăng"""
        contraints = []
        for i in range(1, self.board.rows - 1):
            for j in range(1, self.board.columns - 1):
                cell = self.board.cells[i][j]
                if cell.value == -1:
                    continue
                cnf = self.dia_adjacent(cell, i, j) + self._cell_nextto(cell, i, j)
                contraints.extend(cnf)

        return contraints

    def break_loop(self, graph):
        pass

    def _break_smalloop(self):
        contraints = []
        m = self.board.rows
        n = self.board.columns

        top = lambda i, j: i * n + j + 1
        bottom = lambda i, j: (i + 1) * n + j + 1
        left = lambda i, j: (m + 1) * n + j * m + i + 1
        right = lambda i, j: (m + 1) * n + (j + 1) * m + i + 1

        loops = [
            lambda i, j: (
                [
                    top(i, j),
                    bottom(i, j),
                    left(i, j),
                    top(i, j + 1),
                    bottom(i, j + 1),
                    right(i, j + 1),
                ],
                j < n - 1,
            ),
            lambda i, j: (
                [
                    top(i, j),
                    left(i, j),
                    right(i, j),
                    bottom(i + 1, j),
                    left(i + 1, j),
                    right(i + 1, j),
                ],
                i < m - 1,
            ),
            lambda i, j: (
                [
                    top(i, j),
                    left(i, j),
                    top(i, j + 1),
                    right(i, j + 1),
                    bottom(i, j + 1),
                    left(i + 1, j),
                    right(i + 1, j),
                    bottom(i + 1, j),
                ],
                i < m - 1 and j < n - 1,
            ),
            lambda i, j: (
                [
                    top(i, j),
                    left(i, j),
                    right(i, j),
                    left(i + 1, j),
                    bottom(i + 1, j),
                    top(i + 1, j + 1),
                    right(i + 1, j + 1),
                    bottom(i + 1, j + 1),
                ],
                i < m - 1 and j < n - 1,
            ),
            lambda i, j: (
                [
                    right(i, j),
                    bottom(i, j),
                    top(i, j + 1),
                    right(i, j + 1),
                    right(i + 1, j + 1),
                    bottom(i + 1, j + 1),
                    bottom(i + 1, j),
                    left(i + 1, j),
                ],
                i < m - 1 and j < n - 1,
            ),
            lambda i, j: (
                [
                    left(i, j),
                    top(i, j),
                    bottom(i, j),
                    top(i, j + 1),
                    right(i, j + 1),
                    right(i + 1, j + 1),
                    bottom(i + 1, j + 1),
                    left(i + 1, j + 1),
                ],
                i < m - 1 and j < n - 1,
            ),
        ]
        for i in range(self.board.rows):
            for j in range(self.board.columns):
                for loop in loops[:1]:
                    cnf, useable = loop(i, j)
                    if not useable:
                        continue

                    contraints.extend([[-x for x in cnf]])

        return contraints

    def dia_adjacent(self, cell, i, j):
        cnf = []
        rb_cell = self.board.cells[i + 1][j + 1]
        lb_cell = self.board.cells[i + 1][j - 1]

        if cell.value == 3 and rb_cell.value == 3:
            e1, e2, e3, e4 = cell.top, cell.left, rb_cell.right, rb_cell.bottom
            cnf += [[e1], [e2], [e3], [e4]]
        elif cell.value == 3 and lb_cell.value == 3:
            e1, e2, e3, e4 = cell.top, cell.right, lb_cell.left, lb_cell.bottom
            cnf += [[e1], [e2], [e3], [e4]]

        return cnf

    def _cell_nextto(self, cell, i, j):
        hoz_next = self.board.cells[i][j + 1]
        vert_next = self.board.cells[i + 1][j]
        cnf = []
        if cell.value == 3 and vert_next.value == 3:
            cnf += [[cell.top], [cell.bottom], [vert_next.top]]
        elif cell.value == 3 and hoz_next.value == 3:
            cnf += [[cell.left], [cell.right], [hoz_next.left]]
        elif cell.value == 3 and vert_next.value == 0:
            l_cell = self.board.cells[i][j - 1]
            r_cell = hoz_next
            cnf += [
                [cell.top],
                [cell.left],
                [cell.right],
                [l_cell.bottom],
                [r_cell.bottom],
            ]
        elif cell.value == 0 and vert_next.value == 3:
            l_cell = self.board.cells[i][j - 1]
            r_cell = hoz_next
            cnf += [
                [vert_next.bottom],
                [vert_next.left],
                [vert_next.right],
                [l_cell.bottom],
                [r_cell.bottom],
            ]
        elif cell.value == 3 and hoz_next.value == 0:
            t_cell = self.board.cells[i - 1][j]
            b_cell = vert_next
            cnf += [
                [cell.top],
                [cell.left],
                [cell.bottom],
                [t_cell.right],
                [b_cell.right],
            ]
        elif cell.value == 0 and hoz_next.value == 3:
            t_cell = self.board.cells[i - 1][j]
            b_cell = vert_next
            cnf += [
                [hoz_next.top],
                [hoz_next.right],
                [hoz_next.bottom],
                [t_cell.right],
                [b_cell.right],
            ]

        return cnf

    def _line_to_1(self, cell, i, j):
        cnf = []
        _, e2, e3, _ = [cell.top, cell.right, cell.bottom, cell.left]
        if cell.value == 1:
            tl_cell = self.board.cells[i - 1][j - 1]
            e5, e6 = tl_cell.right, tl_cell.bottom
            # cnf = [[e5, -e6, -e2], [e5, -e6, -e3], [-e6, e2, e3, -e5]]
            cnf = [[e5, -e6, -e2], [e5, -e6, -e3]]

            return cnf

        return cnf

    def _corners_rules(self):
        """https://en.wikipedia.org/wiki/Slitherlink?useskin=vector#Corners"""
        contraints = []
        corners = [
            self.board.cells[0][0],
            self.board.cells[0][self.board.columns - 1],
            self.board.cells[self.board.rows - 1][0],
            self.board.cells[self.board.rows - 1][self.board.columns - 1],
        ]
        corner_awaylines = [
            [
                self.board.cells[0][1].top,
                self.board.cells[1][0].left,
            ],
            [
                self.board.cells[0][self.board.columns - 2].top,
                self.board.cells[1][self.board.columns - 1].right,
            ],
            [
                self.board.cells[self.board.rows - 1][1].bottom,
                self.board.cells[self.board.rows - 2][0].left,
            ],
            [
                self.board.cells[self.board.rows - 1][self.board.columns - 2].bottom,
                self.board.cells[self.board.rows - 2][self.board.columns - 1].right,
            ],
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
            elif corner.value == 2:
                contraints.extend([[line] for line in corner_awaylines[index]])
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
