# This is a special module to create and test deduction rules
from models import Node, Cell
from typing import List
from enum import IntEnum
from solver import one, two, three, zero


class SubBoard:
    """Sub Board size is 2x2 and 12 edges
         e1       e2
    e7  [1]  e8  [2]  e9
         e3      e4
    e10 [3]  e11  [4] e12
         e5       e6
    """

    values: List[int]
    edges: List[int]

    class EdgeType(IntEnum):
        POSITIVE = 1
        NEGATIVE = 0
        UNKNOWN = 2

    def __init__(self, hints: List[int], edges: List[int]):
        self.cells = [
            [
                Cell(value=hints[0], row=0, column=0),
                Cell(value=hints[1], row=0, column=1),
            ],
            [
                Cell(value=hints[2], row=1, column=0),
                Cell(value=hints[3], row=1, column=1),
            ],
        ]

        pass

        return output

    def rules(self):
        contraints = []
        equal_fn = [zero, one, two, three]
        for hint in self.values:
            if hint == -1:
                continue
            else:
                contraints.extend(
                    equal_fn[hint](
                        self.edges[0], self.edges[1], self.edges[2], self.edges[3]
                    )
                )

        pass


if __name__ == "__main__":
    print(SubBoard())
