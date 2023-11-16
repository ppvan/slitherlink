from solver import Solver, Statistics
from viewmodels import BoardViewModel
from models import Board
from repository import BoardRepository
from typing import Tuple
import concurrent.futures

BOARD_SIZES = ["5x5", "7x7", "10x10", "15x15", "20x20", "25x30"]


def do_word(size: str):
    repository = BoardRepository()
    viewmodel = BoardViewModel(repository)
    viewmodel.new_board_cmd(size)

    solver = Solver(viewmodel.board)

    board = solver.solve()

    if board.solved:
        print(board.stats)
    else:
        print("UNSATSISFIED")


if __name__ == "__main__":
    do_word("20x20")

# $ python src/evaluation.py
# Statistics(time=0.0009233029995812103, clauses=282, variables=60, retried=3) 5 5
# Statistics(time=0.005000219000066863, clauses=571, variables=112, retried=1) 7 7
# Statistics(time=0.06793184300113353, clauses=1103, variables=220, retried=102) 10 10
# Statistics(time=0.6539051649997418, clauses=2595, variables=480, retried=563) 15 15
# Statistics(time=26.463703015000647, clauses=4587, variables=840, retried=6803) 20 20
