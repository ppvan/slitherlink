from models import Board, Cell
from pathlib import Path
from typing import List
from functools import cache


class BoardRepository:
    def __init__(self):
        self.database_path = "puzzles.txt"

    def config(self, filepath: Path | str):
        self.database_path = filepath

    def find_all(self):
        all_puzzles = load_puzzles(self.database_path)
        return all_puzzles


@cache
def load_puzzles(filepath: Path | str) -> List[Board]:
    boards = []

    with open(filepath, "r") as f:
        lines = f.readlines()

        for line in lines:
            rows, columns, *cells_flat = [int(x) for x in line.split(" ")]
            cell_vals = [
                cells_flat[slice(columns * i, columns * i + columns)]
                for i in range(rows)
            ]

            cells = []
            for i, row in enumerate(cell_vals):
                rows_cell = []
                for j, item in enumerate(row):
                    rows_cell.append(Cell(value=item, row=i, column=j))
                cells.append(rows_cell)
            board = Board(rows, columns, cells)
            boards.append(board)

    return boards
