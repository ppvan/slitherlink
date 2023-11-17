from solver import MySolver, Statistics
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
            for size in BOARD_SIZES[2:4]:
                for diff in DIFFICULTY:
                    for i in PUZZLES:
                        viewmodel.new_board_cmd(size, diff, i)
                        cancel = Event()
                        solver = MySolver(viewmodel.board, cancel)

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
                            stats = Statistics(acum_time=TIMEOUT)
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
            stats.acum_time,
            stats.clauses,
            stats.variables,
            stats.retried,
        ]
    )


def do_solve(solver: MySolver):
    return solver.solve()


if __name__ == "__main__":
    evaluate_boards()

# python src/evaluation.py && cut -d',' -f5 reports.csv > dralf.txt
# Index,Size,Hints,Diff,Time,Vars,Clause,Retried
# 1,5x5,10,normal,0.0013117890011926647,87,60,3
# 2,5x5,11,normal,0.0006916440015629632,137,60,1
# 3,5x5,9,normal,0.0009358289989904733,80,60,3
# 4,5x5,12,normal,0.0007510850009566639,57,60,2
# 5,5x5,15,normal,0.0006576939995284192,15,60,1
# 1,5x5,12,hard,0.0007420550009555882,282,60,1
# 2,5x5,9,hard,0.0009338290001323912,274,60,3
# 3,5x5,11,hard,0.001342300000032992,159,60,1
# 4,5x5,10,hard,0.0016782109978521476,280,60,2
# 5,5x5,14,hard,0.0017959060005523497,298,60,2
# 1,7x7,21,normal,0.0019823059992631897,54,112,3
# 2,7x7,18,normal,0.0017005220015562372,75,112,5
# 3,7x7,26,normal,0.0009333300004072953,26,112,1
# 4,7x7,25,normal,0.0010673090000636876,219,112,2
# 5,7x7,19,normal,0.0055003440011205385,204,112,30
# 1,7x7,24,hard,0.003451089000009233,585,112,10
# 2,7x7,21,hard,0.0012798019997717347,552,112,2
# 3,7x7,18,hard,0.002398409000306856,493,112,1
# 4,7x7,24,hard,0.0015816340001038043,573,112,1
# 5,7x7,22,hard,0.0018241980014863657,570,112,1
# 1,10x10,45,normal,0.004551318999801879,872,220,4
# 2,10x10,47,normal,0.003656471000795136,487,220,2
# 3,10x10,48,normal,0.0021104590014147107,601,220,2
# 4,10x10,56,normal,0.0020175809986540116,425,220,2
# 5,10x10,53,normal,0.005755674997999449,757,220,12
# 1,10x10,44,hard,0.0212278359940683,913,220,58
# 2,10x10,41,hard,0.0072928499976114836,1065,220,17
# 3,10x10,50,hard,0.002977649999593268,1211,220,3
# 4,10x10,47,hard,0.0030025900014152285,1184,220,2
# 5,10x10,43,hard,0.002824696002790006,1036,220,4
# 1,15x15,115,normal,0.5359881579224748,1318,480,935
# 2,15x15,112,normal,0.15418138901259226,961,480,186
# 3,15x15,130,normal,0.005862488998900517,997,480,5
# 4,15x15,114,normal,0.023369541004285566,1489,480,31
# 5,15x15,107,normal,3.6599733668954286,7795,480,5372
# 1,15x15,106,hard,0.009726513000714476,2658,480,3
# 2,15x15,103,hard,2.5514478370350844,6404,480,3725
# 3,15x15,100,hard,2.1343539669524034,5595,480,3521
# 4,15x15,96,hard,0.06443027300883841,2440,480,109
# 5,15x15,93,hard,0.09055706298568111,1972,480,152
