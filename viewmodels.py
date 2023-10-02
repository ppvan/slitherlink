from models import Board, Edge, Node, Cell
from typing import List, Callable
import utils
from pysat.solvers import Glucose42
from pysat.card import EncType, CardEnc
from pysat.formula import CNF, IDPool

from pathlib import Path


class BoardViewModel:
    board: Board
    puzzles: List[Board]
    subcribers: List[Callable]

    BOARD_SIZES = ["5x5", "7x7", "10x10", "15x15", "20x20", "25x30"]
    DIFFICULTY = ["easy", "medium", "hard"]

    def __init__(self, board: Board = None):
        self.board = board
        self.subcribers = []
        self.puzzles = load_puzzles("puzzles.txt")

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

    def _add_rules(self) -> CNF:
        clauses = CNF()
        self.aux_start = (
            (self.board.rows + 1) * self.board.columns
            + (self.board.columns + 1) * self.board.rows
            + 1
        )
        vpool = IDPool(start_from=self.aux_start)
        for i in range(self.board.rows):
            for j in range(self.board.columns):
                cell = self.board.cells[i][j]
                if cell.value == -1:
                    continue
                else:
                    lits = [cell.top, cell.bottom, cell.left, cell.right]
                    cnf = CardEnc.equals(
                        list(lits),
                        bound=cell.value,
                        encoding=EncType.seqcounter,
                        vpool=vpool,
                    )
                    clauses.extend(cnf.clauses)

        # return clauses

        # inner nodes
        for i in range(1, self.board.rows):
            for j in range(1, self.board.columns):
                node = self.board.nodes[i][j]
                e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]

                clauses.extend(
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
            clauses.extend(
                [
                    [-e2, e3, e4],
                    [e2, -e3, e4],
                    [e2, e3, -e4],
                    [-e2, -e3, -e4],
                ]
            )

            node = self.board.nodes[self.board.rows][j]
            e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]
            # utils.DEBUG(f"node[{node.row},{node.column}]", e1, e2, e3, e4)
            clauses.extend(
                [
                    [-e1, e2, e4],
                    [e1, -e2, e4],
                    [e1, e2, -e4],
                    [-e1, -e2, -e4],
                ]
            )

        for i in range(1, self.board.rows):
            node = self.board.nodes[i][0]
            e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]
            clauses.extend(
                [
                    [-e1, e2, e3],
                    [e1, -e2, e3],
                    [e1, e2, -e3],
                    [-e1, -e2, -e3],
                ]
            )

            node = self.board.nodes[i][self.board.columns]
            e1, e2, e3, e4 = [node.top, node.right, node.bottom, node.left]
            clauses.extend(
                [
                    [-e1, e3, e4],
                    [e1, -e3, e4],
                    [e1, e3, -e4],
                    [-e1, -e3, -e4],
                ]
            )

        # conner nodes
        topleft = self.board.nodes[0][0]
        topright = self.board.nodes[0][self.board.columns]
        bottomleft = self.board.nodes[self.board.rows][0]
        bottomright = self.board.nodes[self.board.rows][self.board.columns]

        e1, e2, e3, e4 = [topleft.top, topleft.right, topleft.bottom, topleft.left]
        cnf.clauses.extend([[-e2, e3], [e2, -e3]])

        e1, e2, e3, e4 = [topright.top, topright.right, topright.bottom, topright.left]
        cnf.clauses.extend([[-e4, e3], [e4, -e3]])

        e1, e2, e3, e4 = [
            bottomleft.top,
            bottomleft.right,
            bottomleft.bottom,
            bottomleft.left,
        ]
        cnf.clauses.extend([[-e2, e1], [e2, -e1]])

        e1, e2, e3, e4 = [
            bottomright.top,
            bottomright.right,
            bottomright.bottom,
            bottomright.left,
        ]
        cnf.clauses.extend([[-e4, e1], [e4, -e1]])

        return clauses

    def _solve(self):
        cnf = self._add_rules()
        ans = []

        utils.DEBUG(len(cnf.clauses))

        with Glucose42(bootstrap_with=cnf.clauses) as s:
            if s.solve():
                ans = s.get_model()

        return ans

    def new_board_cmd(self, size: str, difficulty: str):
        """size in one of BOARD_SIZE. difficulty in one of DIFFICULTY"""
        # assert size in BoardViewModel.BOARD_SIZES
        # assert difficulty in BoardViewModel.DIFFICULTY

        # rows, columns = [int(x) for x in size.split("x")]

        # for board in self.puzzles:
        #     if board.rows == rows and board.columns == columns:
        #         self.board = board
        #         break

        # print("new board cmd")

        self.board = sample_board()

        self.board_changed()
        pass

    def _extract_solution(self, model: List[int]):
        nodes = self.board.nodes
        clean_model = [x for x in model[slice(0, self.aux_start)] if x > 0]
        m = self.board.rows
        n = self.board.columns

        utils.DEBUG(clean_model)

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
        self._add_rules()
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
