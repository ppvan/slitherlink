from models import Board
from solver import Solver, Statistics
from typing import List, Callable
from repository import BoardRepository
import random
import concurrent.futures


class BoardViewModel:
    board: Board
    puzzles: List[Board]
    subcribers: List[Callable]

    stats: Statistics

    BOARD_SIZES = ["5x5", "7x7", "10x10", "15x15", "20x20", "25x30"]

    def __init__(self, repo: BoardRepository, board: Board = None):  # type: ignore
        self.repo = repo
        self.board = board

        self.subcribers = []
        self.puzzles = repo.find_all()
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

            concurrent.futures.wait(
                solver_futures.keys(),
                timeout=3,
                return_when=concurrent.futures.FIRST_COMPLETED,
            )

            for future in concurrent.futures.as_completed(solver_futures):
                completed_board = future.result()
                self.stats = completed_board.stats
                self.board = completed_board

                # Cancel the remaining futures
                for _ in concurrent.futures.as_completed(solver_futures.keys()):
                    executor.shutdown(wait=False, cancel_futures=True)

                break

        self.board_changed()

    def _profile_solve(self):
        solver = Solver(self.board)
        solver.solve()
