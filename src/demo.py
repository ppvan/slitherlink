from solver import Solver, Statistics
from viewmodels import BoardViewModel
from models import Board
from typing import Tuple
import concurrent.futures

# Your existing code for Solver and Board classes
if __name__ == "__main__":
    viewmodel = BoardViewModel()
    viewmodel.new_board_cmd("15x15")

    slaves = [Solver(viewmodel.board.deep_copy()) for _ in range(8)]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        solver_futures = {executor.submit(solver.solve): solver for solver in slaves}

        for future in concurrent.futures.as_completed(solver_futures):
            completed_board = future.result()
            if completed_board.solved:
                print(completed_board.stats)
            else:
                pass

            # Cancel the remaining futures
            for remaining_future in solver_futures:
                if remaining_future != future:
                    remaining_future.cancel()

            break
