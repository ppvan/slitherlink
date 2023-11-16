from solver import zero_or_two


ans = zero_or_two(-1, 2, 3, -1)

for item in ans:
    print(item)

"""
[[-1, -2, -3],
[-1, -2, -4],
[-1, -3, -4],
[-2, -3, -4],
[-1, 2, 3, 4],
[1, -2, 3, 4],
[1, 2, -3, 4],
[1, 2, 3, -4]]
"""
