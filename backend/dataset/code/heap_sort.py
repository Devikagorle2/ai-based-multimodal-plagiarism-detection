def heapify(data, n, i):
    largest = i
    l = 2 * i + 1
    r = 2 * i + 2
    if l < n and data[l] > data[largest]:
        largest = l
    if r < n and data[r] > data[largest]:
        largest = r
    if largest != i:
        data[i], data[largest] = data[largest], data[i]
        heapify(data, n, largest)

def heap_sort(arr):
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)
    return arr
