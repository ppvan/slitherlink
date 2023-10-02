grid = [
    [1, 2, 3, 4, 5],
    [6, 7, 8, 9, 10],
    [11, 12, 13, 14, 15],
    [16, 17, 18, 19, 20],
    [21, 22, 23, 24, 25],
]
size = 5

for i in range(size):
    for j in range(size - 1):
        edge_id = i * (size - 1) + j
        print(edge_id)

for j in range(size):
    for i in range(size - 1):
        edge_id = i * (size) + j
        print(edge_id)
