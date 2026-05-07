def find_all(hay, needle):
    out = []
    start = 0
    while True:
        i = hay.find(needle, start)
        if i == -1:
            break
        out.append(i)
        start = i + 1
    return out
