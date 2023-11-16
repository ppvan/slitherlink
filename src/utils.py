import inspect
import pathlib
from models import Board, Cell


def DEBUG(*args, **kwargs):
    cf = inspect.currentframe()
    cwd = pathlib.Path.cwd()
    filename = pathlib.Path(inspect.stack()[1].filename)

    print(f"{filename.relative_to(cwd)}:{cf.f_back.f_lineno}", *args, **kwargs)


def sample_board():
    size = 5
    cell_vals = [
        [-1, 2, 0, 2, -1],
        [-1, -1, 2, -1, -1],
        [-1, 2, 3, 2, -1],
        [-1, -1, 1, -1, -1],
        [3, -1, 3, 3, -1],
    ]

    cells = [[Cell(val) for val in row_vals] for row_vals in cell_vals]

    return Board(size, size, cells)
