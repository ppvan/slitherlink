from typing import List
from collections import defaultdict
import utils
import pycosat
import time
from dataclasses import dataclass


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
    def __init__(self, board):
        self.board = board
        pass

    def solve(self):
        start = time.perf_counter()
        self.stats = Statistics()
        clauses = self.encode_rules()
        m = self.board.rows
        n = self.board.columns

        self.assign_edges_index()
        self.stats.clauses = len(clauses)
        self.stats.variables = (m + 1) * n + (n + 1) * m

        model = self._solve()
        self._extract_solution(model)

        self.stats.time = time.perf_counter() - start

    def _dfs(self, node, visited):
        visited.append(node)
        for neighbor in self.board.graph[node]:
            if neighbor not in visited:
                self._dfs(neighbor, visited)

    def _solve(self):
        clauses = self.encode_rules()
        ans = []

        utils.DEBUG(len(clauses))
        count = 0
        for test_solution in pycosat.itersolve(clauses):
            if test_solution in ["UNSAT", "UNKNOWN"]:
                print("UNSATSISFIED")
                break
            if self._validate(test_solution):
                ans = test_solution
                break
            print("Not valid, trying again")
            count += 1

        utils.DEBUG(count)
        self.stats.retried = count
        return ans

    def _validate(self, ans):
        self._extract_solution(ans)

        start = None
        for node, neighbors in self.board.graph.items():
            if len(neighbors) > 0:
                start = node
                break

        visited = []
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
                nodes[i][j].left = i * n + j
                nodes[i][j].right = i * n + j + 1
                nodes[i][j].top = (m + 1) * n + j * m + i
                nodes[i][j].bottom = (m + 1) * n + j * m + i + 1

    def encode_rules(self):
        self.contraints = self._cell_contraints() + self._loop_contraints()

        return self.contraints

    def _extract_solution(self, model: List[int]):
        nodes = self.board.nodes
        clean_model = [x for x in model if x > 0]
        m = self.board.rows
        n = self.board.columns

        self.board.graph = defaultdict(list)

        for i in range(m):
            for j in range(n):
                top = i * n + j + 1
                bottom = (i + 1) * n + j + 1
                left = (m + 1) * n + j * m + i + 1
                right = (m + 1) * n + (j + 1) * m + i + 1

                if top in clean_model:
                    self.board.graph[nodes[i][j]].append(nodes[i][j + 1])
                    self.board.graph[nodes[i][j + 1]].append(nodes[i][j])

                if bottom in clean_model:
                    self.board.graph[nodes[i + 1][j]].append(nodes[i + 1][j + 1])
                    self.board.graph[nodes[i + 1][j + 1]].append(nodes[i + 1][j])
                    pass
                if left in clean_model:
                    self.board.graph[nodes[i][j]].append(nodes[i + 1][j])
                    self.board.graph[nodes[i + 1][j]].append(nodes[i][j])
                    pass
                if right in clean_model:
                    self.board.graph[nodes[i][j + 1]].append(nodes[i + 1][j + 1])
                    self.board.graph[nodes[i + 1][j + 1]].append(nodes[i][j + 1])
                    pass

    def _cell_contraints(self):
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

        atmosts = [zero, one, two, three]
        constraints = []
        for i in range(self.board.rows):
            for j in range(self.board.columns):
                cell = self.board.cells[i][j]
                if cell.value == -1:
                    continue
                else:
                    cnf = atmosts[cell.value](
                        cell.top, cell.bottom, cell.left, cell.right
                    )

                    constraints.extend(cnf)
        return constraints

    def _loop_contraints(self):
        constraints = []
        for i in range(1, self.board.rows):
            for j in range(1, self.board.columns):
                node = self.board.nodes[i][j]
                e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]

                constraints.extend(
                    [
                        [-e1, -e2, -e3],
                        [-e1, -e2, -e4],
                        [-e1, -e3, -e4],
                        [-e2, -e3, -e4],
                        [-e1, e2, e3, e4],
                        [e1, -e2, e3, e4],
                        [e1, e2, -e3, e4],
                        [e1, e2, e3, -e4],
                    ]
                )
        # exit(0)

        # outer nodes
        for j in range(1, self.board.columns):
            node = self.board.nodes[0][j]
            e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]
            constraints.extend(
                [[-e2, e3, e4], [e2, -e3, e4], [e2, e3, -e4], [-e2, -e3, -e4]]
            )

            node = self.board.nodes[self.board.rows][j]
            e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]
            constraints.extend(
                [[-e1, e2, e4], [e1, -e2, e4], [e1, e2, -e4], [-e1, -e2, -e4]]
            )

        for i in range(1, self.board.rows):
            node = self.board.nodes[i][0]
            e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]
            constraints.extend(
                [[-e1, e2, e3], [e1, -e2, e3], [e1, e2, -e3], [-e1, -e2, -e3]]
            )

            node = self.board.nodes[i][self.board.columns]
            e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]
            constraints.extend(
                [[-e1, e3, e4], [e1, -e3, e4], [e1, e3, -e4], [-e1, -e3, -e4]]
            )

        # conner nodes
        topleft = self.board.nodes[0][0]
        topright = self.board.nodes[0][self.board.columns]
        bottomleft = self.board.nodes[self.board.rows][0]
        bottomright = self.board.nodes[self.board.rows][self.board.columns]

        e1, e2, e3, e4 = [topleft.top, topleft.right, topleft.bottom, topleft.left]
        constraints.extend([[-e2, e3], [e2, -e3]])

        e1, e2, e3, e4 = [topright.top, topright.right, topright.bottom, topright.left]
        constraints.extend([[-e4, e3], [e4, -e3]])

        e1, e2, e3, e4 = [
            bottomleft.top,
            bottomleft.right,
            bottomleft.bottom,
            bottomleft.left,
        ]
        constraints.extend([[-e2, e1], [e2, -e1]])

        e1, e2, e3, e4 = [
            bottomright.top,
            bottomright.right,
            bottomright.bottom,
            bottomright.left,
        ]
        constraints.extend([[-e4, e1], [e4, -e1]])

        return constraints
