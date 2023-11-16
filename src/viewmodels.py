from models import Board
from solver import Solver, Statistics
from typing import List, Callable
from repository import BoardRepository
import random
from collections import defaultdict
from threading import Thread
import time


class BoardViewModel:
    board: Board
    puzzles: List[Board]
    subcribers: List[Callable]

    stats: Statistics

    BOARD_SIZES = ["5x5", "7x7", "10x10", "15x15", "20x20", "25x30"]
    DIFFICULTY = ["normal", "hard"]
    NO_PUZZLES = ["Random"] + [str(i + 1) for i in range(10)]

    def __init__(self, repo: BoardRepository, board: Board = None):  # type: ignore
        self.repo = repo
        self.board = board

        self.subcribers = []
        self.puzzles = repo.find_all(size="5x5", diff="normal")
        self.stats = Statistics()

    def subcribe(self, callback):
        self.subcribers.append(callback)

    def board_changed(self):
        for subscriber in self.subcribers:
            subscriber()

    def new_board_cmd(
        self, size: str, difficulty: str, index="Random", done_callback: Callable = None
    ):
        """size in one of BOARD_SIZE."""
        assert size in BoardViewModel.BOARD_SIZES
        assert difficulty in BoardViewModel.DIFFICULTY
        assert index in BoardViewModel.NO_PUZZLES

        columns, rows = [int(x) for x in size.split("x")]
        candiates = self.repo.find_all(size=size, diff=difficulty)

        if index == "Random":
            index = random.randint(0, len(candiates) - 1)
        else:
            index = int(index) - 1

        self.board = candiates[index]
        self.board.graph = defaultdict(list)
        self.board.solved = False
        self.stats.reset()

        self.board_changed()

    def do_solve(self, done_callback: Callable = None):
        def update_ui(board: Board, stats: Statistics):
            self.board = board
            self.stats = solver.stats
            self.board_changed()
            time.sleep(1)

        solver = Solver(self.board, on_partial_solution=update_ui)
        completed_board = solver.solve()

        self.stats = solver.stats
        self.board = completed_board

        self.board_changed()
        done_callback()

    def solve_board_cmd(self, done_callback: Callable = None):
        t = Thread(target=self.do_solve, args=(done_callback,))
        t.daemon = True
        t.start()

    def _profile_solve(self):
        solver = Solver(self.board)
        solver.solve()
