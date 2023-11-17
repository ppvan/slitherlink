from solver import MySolver
from viewmodels import BoardViewModel
from repository import BoardRepository

BOARD_SIZES = ["5x5", "7x7", "10x10", "15x15", "20x20", "25x30"]
DIFFICULTY = ["normal", "hard"]
PUZZLES = [str(i + 1) for i in range(10)]
TIMEOUT = 30


def profile_boards():
    repository = BoardRepository()
    viewmodel = BoardViewModel(repository)

    for size in BOARD_SIZES[:4]:
        for diff in DIFFICULTY:
            for i in PUZZLES[:5]:
                viewmodel.new_board_cmd(size, diff, i)
                solver = MySolver(viewmodel.board)
                do_solve(solver)


def do_solve(solver: MySolver):
    return solver.solve()


if __name__ == "__main__":
    profile_boards()
