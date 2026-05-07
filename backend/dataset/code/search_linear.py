def linear_search(seq, target):
    for index, value in enumerate(seq):
        if value == target:
            return index
    return -1
