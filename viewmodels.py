from models import Board, Edge, Node
from typing import List, Callable

from pathlib import Path


class BoardViewModel:
    board: Board
    puzzles: List[Board]
    subcribers: List[Callable]

    BOARD_SIZES = [f"{x}x{x}" for x in [5, 7, 10, 15, 20, 30]]
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

    def new_board_cmd(self, size: str, difficulty: str):
        """size in one of BOARD_SIZE. difficulty in one of DIFFICULTY"""
        assert size in BoardViewModel.BOARD_SIZES
        assert difficulty in BoardViewModel.DIFFICULTY

        size_int = int(size.split("x")[0])

        for board in self.puzzles:
            if board.size == size_int:
                self.board = board
                break

        print("new board cmd")
        self.board_changed()
        pass

    def solve_board_cmd(self):
        print("solve board cmd")
        pass


def load_puzzles(filepath: Path | str) -> List[Board]:
    boards = []

    with open(filepath, "r") as f:
        lines = f.readlines()

        for line in lines:
            size, *cells_flat = [int(x) for x in line.split(" ")]
            cells = [cells_flat[slice(i, i + size)] for i in range(size)]

            board = Board(size, cells)
            boards.append(board)

    return boards


def sample_board():
    size = 6
    cells = [
        [-1, 2, 0, 2, -1],
        [-1, -1, 2, -1, -1],
        [-1, 2, 3, 2, -1],
        [-1, -1, 1, -1, -1],
        [3, -1, 3, 3, -1],
    ]

    edges = [
        Edge(Node(0, 0), Node(0, 1)),
        Edge(Node(0, 1), Node(1, 1)),
        Edge(Node(1, 1), Node(1, 2)),
        Edge(Node(1, 2), Node(2, 2)),
    ]

    return Board(size, cells, edges)
