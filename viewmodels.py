from models import Board


class BoardViewModel:
    board: Board

    def __init__(self, board: Board):
        self.board = board


def sample_board():
    size = 6
    cells = [
        [-1, 2, 0, 2, -1],
        [-1, -1, 2, -1, -1],
        [-1, 2, 3, 2, -1],
        [-1, -1, 1, -1, -1],
        [3, -1, 3, 3, -1],
    ]

    edges = []

    return Board(size, cells, edges)
