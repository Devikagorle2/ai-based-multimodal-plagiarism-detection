def selection_sort(items):
    for i in range(len(items)):
        min_idx = i
        for j in range(i + 1, len(items)):
            if items[j] < items[min_idx]:
                min_idx = j
        items[i], items[min_idx] = items[min_idx], items[i]
    return items
