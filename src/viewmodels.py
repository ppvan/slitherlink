from models import Board
from solver import Solver
from typing import List, Callable
from utils import load_puzzles
import random


class BoardViewModel:
    board: Board
    puzzles: List[Board]
    subcribers: List[Callable]
    constraints: List[List[int]]

    BOARD_SIZES = ["5x5", "7x7", "10x10", "15x15", "20x20", "25x30"]
    DIFFICULTY = ["easy", "hard"]

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

        rows, columns = [int(x) for x in size.split("x")]
        candiates = []

        for board in self.puzzles:
            if board.rows == rows and board.columns == columns:
                candiates.append(board)

        self.board = random.choice(candiates)

        # print("new board cmd")

        # self.board = sample_board()

        self.board_changed()
        pass

    def solve_board_cmd(self):
        solver = Solver(self.board)
        solver.solve()

        # print("solve board cmd")
        # self.assign_edges_index()
        # print("assign done")
        # self.encode_rules()
        # model = self._solve()
        # self._extract_solution(model)

        self.board_changed()
        pass
