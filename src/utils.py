import inspect
import pathlib
from models import Board, Cell
from typing import List
from pathlib import Path


def DEBUG(*args, **kwargs):
    cf = inspect.currentframe()
    cwd = pathlib.Path.cwd()
    filename = pathlib.Path(inspect.stack()[1].filename)

    print(f"{filename.relative_to(cwd)}:{cf.f_back.f_lineno}", *args, **kwargs)


def load_puzzles(filepath: Path | str) -> List[Board]:
    boards = []

    with open(filepath, "r") as f:
        lines = f.readlines()

        for line in lines:
            rows, columns, *cells_flat = [int(x) for x in line.split(" ")]
            cell_vals = [
                cells_flat[slice(rows * i, rows * i + columns)] for i in range(rows)
            ]

            cells = []
            for row in cell_vals:
                rows_cell = []
                for item in row:
                    rows_cell.append(Cell(item))
                cells.append(rows_cell)
            board = Board(rows, columns, cells)
            boards.append(board)

    return boards


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
