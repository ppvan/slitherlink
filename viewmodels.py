from models import Board, Edge, Node
from typing import List, Callable


class BoardViewModel:
    board: Board
    subcribers: List[Callable]

    BOARD_SIZES = [f"{x}x{x}" for x in range(6, 31)]
    DIFFICULTY = ["easy", "medium", "hard"]

    def __init__(self, board: Board):
        self.board = board
        self.subcribers = []

    def subcribe(self, callback):
        self.subcribers.append(callback)

    def board_changed(self):
        for subscriber in self.subcribers:
            subscriber()

    def new_board_cmd(self, size: str, difficulty: str):
        """size in one of BOARD_SIZE. difficulty in one of DIFFICULTY"""
        print("new board cmd")
        self.board_changed()
        pass

    def solve_board_cmd(self):
        print("solve board cmd")
        pass


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
