import unittest
from models import Board, Cell, Node


class TestBoardMethods(unittest.TestCase):
    def test_deep_copy(self):
        # Create a sample board
        cells = [
            [Cell(1), Cell(2), Cell(3)],
            [Cell(4), Cell(5), Cell(6)],
            [Cell(7), Cell(8), Cell(9)],
        ]

        original_board = Board(rows=3, columns=3, cells=cells)

        # Make a deep copy
        copied_board = original_board.deep_copy()

        # Ensure they are not the same object
        self.assertIsNot(original_board, copied_board)

        # Ensure attributes are equal
        self.assertEqual(original_board.rows, copied_board.rows)
        self.assertEqual(original_board.columns, copied_board.columns)
        self.assertEqual(original_board.cells, copied_board.cells)


if __name__ == "__main__":
    unittest.main()
