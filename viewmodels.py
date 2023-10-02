from models import Board, Edge, Cell
from typing import List, Callable
import utils
import pycosat

from pathlib import Path


class BoardViewModel:
    board: Board
    puzzles: List[Board]
    subcribers: List[Callable]
    constraints: List[List[int]]

    BOARD_SIZES = ["5x5", "7x7", "10x10", "15x15", "20x20", "25x30"]
    DIFFICULTY = ["easy", "medium", "hard"]

    def __init__(self, board: Board = None):
        self.board = board
        self.subcribers = []
        self.puzzles = load_puzzles("puzzles.txt")
        self.constraints = []

    def subcribe(self, callback):
        self.subcribers.append(callback)

    def board_changed(self):
        for subscriber in self.subcribers:
            subscriber()

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
        for i in range(self.board.rows):
            for j in range(self.board.columns):
                cell = self.board.cells[i][j]
                if cell.value == -1:
                    continue
                else:
                    cnf = atmosts[cell.value](
                        cell.top, cell.bottom, cell.left, cell.right
                    )

                    self.constraints.extend(cnf)
        return self.constraints

    def _loop_contraints(self):
        for i in range(1, self.board.rows):
            for j in range(1, self.board.columns):
                node = self.board.nodes[i][j]
                e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]

                self.constraints.extend(
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
            self.constraints.extend(
                [[-e2, e3, e4], [e2, -e3, e4], [e2, e3, -e4], [-e2, -e3, -e4]]
            )

            node = self.board.nodes[self.board.rows][j]
            e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]
            self.constraints.extend(
                [[-e1, e2, e4], [e1, -e2, e4], [e1, e2, -e4], [-e1, -e2, -e4]]
            )

        for i in range(1, self.board.rows):
            node = self.board.nodes[i][0]
            e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]
            self.constraints.extend(
                [[-e1, e2, e3], [e1, -e2, e3], [e1, e2, -e3], [-e1, -e2, -e3]]
            )

            node = self.board.nodes[i][self.board.columns]
            e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]
            self.constraints.extend(
                [[-e1, e3, e4], [e1, -e3, e4], [e1, e3, -e4], [-e1, -e3, -e4]]
            )

        # conner nodes
        topleft = self.board.nodes[0][0]
        topright = self.board.nodes[0][self.board.columns]
        bottomleft = self.board.nodes[self.board.rows][0]
        bottomright = self.board.nodes[self.board.rows][self.board.columns]

        e1, e2, e3, e4 = [topleft.top, topleft.right, topleft.bottom, topleft.left]
        self.constraints.extend([[-e2, e3], [e2, -e3]])

        e1, e2, e3, e4 = [topright.top, topright.right, topright.bottom, topright.left]
        self.constraints.extend([[-e4, e3], [e4, -e3]])

        e1, e2, e3, e4 = [
            bottomleft.top,
            bottomleft.right,
            bottomleft.bottom,
            bottomleft.left,
        ]
        self.constraints.extend([[-e2, e1], [e2, -e1]])

        e1, e2, e3, e4 = [
            bottomright.top,
            bottomright.right,
            bottomright.bottom,
            bottomright.left,
        ]
        self.constraints.extend([[-e4, e1], [e4, -e1]])

        return self.constraints

    def encode_rules(self):
        self.constraints = []
        self._cell_contraints()
        self._loop_contraints()

        return self.constraints

    def _solve(self):
        clauses = self.encode_rules()
        ans = []

        utils.DEBUG(len(clauses))

        test_solution = pycosat.solve(clauses)

        if test_solution in ["UNSAT", "UNKNOWN"]:
            utils.DEBUG("unsat")
            ans = []
        else:
            ans = test_solution

        return ans

    def new_board_cmd(self, size: str, difficulty: str):
        """size in one of BOARD_SIZE. difficulty in one of DIFFICULTY"""
        assert size in BoardViewModel.BOARD_SIZES
        assert difficulty in BoardViewModel.DIFFICULTY

        rows, columns = [int(x) for x in size.split("x")]

        for board in self.puzzles:
            if board.rows == rows and board.columns == columns:
                self.board = board
                break

        # print("new board cmd")

        # self.board = sample_board()

        self.board_changed()
        pass

    def _extract_solution(self, model: List[int]):
        nodes = self.board.nodes
        clean_model = [x for x in model if x > 0]
        m = self.board.rows
        n = self.board.columns

        for i in range(m):
            for j in range(n):
                top = i * n + j + 1
                bottom = (i + 1) * n + j + 1
                left = (m + 1) * n + j * m + i + 1
                right = (m + 1) * n + (j + 1) * m + i + 1

                if top in clean_model:
                    self.board.edges.append(Edge(nodes[i][j], nodes[i][j + 1]))
                if bottom in clean_model:
                    self.board.edges.append(Edge(nodes[i + 1][j], nodes[i + 1][j + 1]))
                    pass
                if left in clean_model:
                    self.board.edges.append(Edge(nodes[i][j], nodes[i + 1][j]))
                    pass
                if right in clean_model:
                    self.board.edges.append(Edge(nodes[i][j + 1], nodes[i + 1][j + 1]))
                    pass

    def solve_board_cmd(self):
        print("solve board cmd")
        self.assign_edges_index()
        print("assign done")
        self.encode_rules()
        model = self._solve()
        self._extract_solution(model)

        self.board_changed()
        pass


def load_puzzles(filepath: Path | str) -> List[Board]:
    boards = []

    with open(filepath, "r") as f:
        lines = f.readlines()

        for line in lines:
            rows, columns, *cells_flat = [int(x) for x in line.split(" ")]
            cell_vals = [cells_flat[slice(i, i + columns)] for i in range(rows)]

            cells = []
            for row in cell_vals:
                rows_cell = []
                for item in row:
                    rows_cell.append(Cell(item))
                cells.append(rows_cell)

            board = Board(rows, columns, cells)
            boards.append(board)

    return boards


def sample_board():
    size = 5
    cell_vals = [
        [-1, 2, 0, 2, -1],
        [-1, -1, 2, -1, -1],
        [-1, 2, 3, 2, -1],
        [-1, -1, 1, -1, -1],
        [3, -1, 3, 3, -1],
    ]

    cells = [[Cell(val) for val in row_vals] for row_vals in cell_vals]

    return Board(size, size, cells)
