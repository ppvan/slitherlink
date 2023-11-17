from solver import Solver, Statistics
from viewmodels import BoardViewModel
from models import Board
from repository import BoardRepository
import concurrent.futures
from threading import Event
import csv

BOARD_SIZES = ["5x5", "7x7", "10x10", "15x15", "20x20", "25x30"]
DIFFICULTY = ["normal", "hard"]
PUZZLES = [str(i + 1) for i in range(10)]
TIMEOUT = 30


def evaluate_boards():
    repository = BoardRepository()
    viewmodel = BoardViewModel(repository)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        with open("reports.csv", "w") as f:
            writer = csv.writer(f)
            # write headers
            writer.writerow(
                ["Index", "Size", "Hints", "Diff", "Time", "Vars", "Clause", "Retried"]
            )
            for size in BOARD_SIZES[:5]:
                for diff in DIFFICULTY:
                    for i in PUZZLES:
                        viewmodel.new_board_cmd(size, diff, i)
                        cancel = Event()
                        solver = Solver(viewmodel.board, cancel)

                        future = executor.submit(do_solve, solver)

                        done, not_done = concurrent.futures.wait(
                            [future], timeout=TIMEOUT
                        )

                        if future.done():
                            board = future.result()
                            viewmodel.stats = solver.stats
                            viewmodel.board = board

                            write_info(
                                writer,
                                size,
                                diff,
                                viewmodel.board,
                                viewmodel.stats,
                                i,
                            )
                        else:
                            cancel.set()
                            stats = Statistics(time=TIMEOUT)
                            write_info(
                                writer,
                                size,
                                diff,
                                viewmodel.board,
                                stats,
                                i,
                            )


def write_info(
    writer: csv.writer,
    size: str,
    diff: str,
    board: Board,
    stats: Statistics,
    i: int,
):
    print(f"{size=} {diff=} {i=}")
    writer.writerow(
        [
            i,
            size,
            board.hints,
            diff,
            stats.time,
            stats.clauses,
            stats.variables,
            stats.retried,
        ]
    )


def do_solve(solver: Solver):
    return solver.solve()


if __name__ == "__main__":
    evaluate_boards()

# $ python src/evaluation.py
# Statistics(time=0.0009233029995812103, clauses=282, variables=60, retried=3) 5 5
# Statistics(time=0.005000219000066863, clauses=571, variables=112, retried=1) 7 7
# Statistics(time=0.06793184300113353, clauses=1103, variables=220, retried=102) 10 10
# Statistics(time=0.6539051649997418, clauses=2595, variables=480, retried=563) 15 15
# Statistics(time=26.463703015000647, clauses=4587, variables=840, retried=6803) 20 20
