def binary_search(sorted_list, x):
    lo, hi = 0, len(sorted_list) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if sorted_list[mid] == x:
            return mid
        if sorted_list[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
