from models import Board
from solver import Solver, Statistics
from typing import List, Callable
from repository import BoardRepository
import random
from collections import defaultdict
from threading import Thread, Event
import time


class BoardViewModel:
    board: Board
    puzzles: List[Board]
    subcribers: List[Callable]

    stats: Statistics

    BOARD_SIZES = ["5x5", "7x7", "10x10", "15x15", "20x20", "25x30"]
    DIFFICULTY = ["normal", "hard"]
    NO_PUZZLES = ["Random"] + [str(i + 1) for i in range(10)]
    ANIMATION = [True, False]

    def __init__(self, repo: BoardRepository, board: Board = None):  # type: ignore
        self.repo = repo
        self.board = board

        self.board_subcribers = []
        self.graph_subcribers = []
        self.puzzles = repo.find_all(size="5x5", diff="normal")
        self.stats = Statistics()

    def add_board_changed_callback(self, callback):
        self.board_subcribers.append(callback)

    def add_graph_changed_callback(self, callback):
        self.graph_subcribers.append(callback)

    def board_changed(self):
        for subscriber in self.board_subcribers:
            subscriber()

    def graph_changed(self):
        for subscriber in self.graph_subcribers:
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

    def do_solve(
        self, done_callback: Callable = None, animation=False, cancel: Event = None
    ):
        def update_ui(board: Board, stats: Statistics):
            self.board = board
            self.stats = solver.stats
            self.graph_changed()
            time.sleep(1)

        solver = Solver(board=self.board, cancel_event=cancel)
        if animation:
            solver.add_partial_solution_callback(update_ui)

        completed_board = solver.solve()

        done_callback()
        if not animation:
            self.stats = solver.stats
            self.board = completed_board
            self.board_changed()

    def solve_board_cmd(self, done_callback: Callable = None, animation=False):
        self.stop_solving = Event()
        t = Thread(
            target=self.do_solve,
            args=(done_callback, animation, self.stop_solving),
        )
        t.daemon = True
        t.start()

    def cancel_cmd(self, done_callback: Callable = None):
        if self.stop_solving:
            self.stop_solving.set()

        done_callback()

    def _profile_solve(self):
        solver = Solver(self.board)
        solver.solve()
