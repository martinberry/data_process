import os


def count_lines_of_file(filename):
    if not os.path.exists(filename):
        return 0
    f = open(filename)
    lines = 0
    for line in f:
        lines += 1
    f.close()
    return lines


def count_blocks_of_file(filename):
    if not os.path.exists(filename):
        return 0
    f = open(filename)
    items = 0
    for item in f.read().split('\n\n'):
        items += 1
    f.close()
    return items - 1
