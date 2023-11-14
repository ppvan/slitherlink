from models import Board, Worker
from solver import Solver, Statistics
from typing import List, Callable
from utils import load_puzzles
import random
import concurrent.futures


class BoardViewModel:
    board: Board
    puzzles: List[Board]
    subcribers: List[Callable]

    stats: Statistics

    BOARD_SIZES = ["5x5", "7x7", "10x10", "15x15", "20x20", "25x30"]

    def __init__(self, board: Board = None):  # type: ignore
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
        slaves = [Solver(self.board.deep_copy()) for _ in range(8)]
        with concurrent.futures.ProcessPoolExecutor() as executor:
            solver_futures = {
                executor.submit(solver.solve): solver for solver in slaves
            }

            for future in concurrent.futures.as_completed(solver_futures):
                completed_board = future.result()
                self.stats = completed_board.stats
                self.board = completed_board

                # Cancel the remaining futures
                for remaining_future in solver_futures:
                    if remaining_future != future:
                        remaining_future.cancel()

                break

        self.board_changed()

    def _profile_solve(self):
        solver = Solver(self.board)
        solver.solve()
