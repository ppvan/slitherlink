from models import Board, Worker
from solver import Solver, Statistics
from typing import List, Callable
from utils import load_puzzles
import random


class BoardViewModel:
    board: Board
    puzzles: List[Board]
    subcribers: List[Callable]

    stats: Statistics

    BOARD_SIZES = ["5x5", "7x7", "10x10", "15x15", "20x20", "25x30"]

    def __init__(self, board: Board = None):
        self.board = board
        self.subcribers = []
        self.puzzles = load_puzzles("puzzles.txt")
        self.stats = Statistics()

    def subcribe(self, callback):
        self.subcribers.append(callback)

    def board_changed(self):
        for subscriber in self.subcribers:
            subscriber()

    def new_board_cmd(self, size: str):
        """size in one of BOARD_SIZE."""
        assert size in BoardViewModel.BOARD_SIZES

        rows, columns = [int(x) for x in size.split("x")]
        candiates = []

        for board in self.puzzles:
            if board.rows == rows and board.columns == columns:
                candiates.append(board)

        self.board = random.choice(candiates)
        self.stats.reset()

        self.board_changed()
        pass

    def solve_board_cmd(self):
        def callback(worker):
            print(self.stats)
            self.board_changed()

        def task():
            solver = Solver(self.board)
            solver.solve()
            self.stats = solver.stats

        worker = Worker(task, callback)
        worker.start()
