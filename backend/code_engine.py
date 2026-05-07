"""
RAG-style code similarity: embed dataset .py files with MiniLM, search with FAISS.
"""

from __future__ import annotations

from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
DATASET_DIR = Path(__file__).resolve().parent / "dataset" / "code"

_model: SentenceTransformer | None = None
_faiss_index: faiss.Index | None = None
_file_paths: list[str] = []
_file_contents: list[str] = []


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _generate_sample_programs() -> None:
    """Create 30 simple Python programs if dataset is empty."""
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    programs: list[tuple[str, str]] = []

    # Sorting (1–6)
    programs.append(
        (
            "sort_bubble.py",
            '''def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
''',
        )
    )
    programs.append(
        (
            "sort_selection.py",
            '''def selection_sort(items):
    for i in range(len(items)):
        min_idx = i
        for j in range(i + 1, len(items)):
            if items[j] < items[min_idx]:
                min_idx = j
        items[i], items[min_idx] = items[min_idx], items[i]
    return items
''',
        )
    )
    programs.append(
        (
            "sort_insertion.py",
            '''def insertion_sort(a):
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and key < a[j]:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a
''',
        )
    )
    programs.append(
        (
            "sort_merge.py",
            '''def merge_sort(lst):
    if len(lst) <= 1:
        return lst
    mid = len(lst) // 2
    left = merge_sort(lst[:mid])
    right = merge_sort(lst[mid:])
    return _merge(left, right)

def _merge(left, right):
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out
''',
        )
    )
    programs.append(
        (
            "sort_quick.py",
            '''def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + mid + quick_sort(right)
''',
        )
    )
    programs.append(
        (
            "heap_sort.py",
            '''def heapify(data, n, i):
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
''',
        )
    )

    # Searching (7–10)
    programs.append(
        (
            "search_linear.py",
            '''def linear_search(seq, target):
    for index, value in enumerate(seq):
        if value == target:
            return index
    return -1
''',
        )
    )
    programs.append(
        (
            "search_binary.py",
            '''def binary_search(sorted_list, x):
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
''',
        )
    )
    programs.append(
        (
            "search_binary_recursive.py",
            '''def binary_search_rec(arr, target, lo, hi):
    if lo > hi:
        return -1
    mid = (lo + hi) // 2
    if arr[mid] == target:
        return mid
    if arr[mid] < target:
        return binary_search_rec(arr, target, mid + 1, hi)
    return binary_search_rec(arr, target, lo, mid - 1)
''',
        )
    )
    programs.append(
        (
            "search_jump.py",
            '''import math

def jump_search(arr, x):
    n = len(arr)
    step = int(math.sqrt(n))
    prev = 0
    while arr[min(step, n) - 1] < x:
        prev = step
        step += int(math.sqrt(n))
        if prev >= n:
            return -1
    while arr[prev] < x:
        prev += 1
        if prev == min(step, n):
            return -1
    if arr[prev] == x:
        return prev
    return -1
''',
        )
    )

    # Factorial / Fibonacci (11–16)
    programs.append(
        (
            "factorial_iter.py",
            '''def factorial(n):
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
''',
        )
    )
    programs.append(
        (
            "factorial_rec.py",
            '''def factorial_rec(n):
    if n <= 1:
        return 1
    return n * factorial_rec(n - 1)
''',
        )
    )
    programs.append(
        (
            "fibonacci_iter.py",
            '''def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
''',
        )
    )
    programs.append(
        (
            "fibonacci_rec.py",
            '''def fib_rec(n):
    if n <= 1:
        return n
    return fib_rec(n - 1) + fib_rec(n - 2)
''',
        )
    )
    programs.append(
        (
            "fibonacci_memo.py",
            '''def fib_memo(n, cache=None):
    if cache is None:
        cache = {}
    if n in cache:
        return cache[n]
    if n <= 1:
        return n
    cache[n] = fib_memo(n - 1, cache) + fib_memo(n - 2, cache)
    return cache[n]
''',
        )
    )
    programs.append(
        (
            "gcd_euclid.py",
            '''def gcd(a, b):
    while b:
        a, b = b, a % b
    return a
''',
        )
    )

    # String ops (17–30)
    snippets = [
        ("str_reverse.py", "def reverse_string(s):\n    return s[::-1]\n"),
        ("str_palindrome.py", "def is_palindrome(s):\n    t = ''.join(c.lower() for c in s if c.isalnum())\n    return t == t[::-1]\n"),
        ("str_count_vowels.py", "def count_vowels(text):\n    vowels = 'aeiouAEIOU'\n    return sum(1 for c in text if c in vowels)\n"),
        ("str_title_case.py", "def to_title(words):\n    return ' '.join(w.capitalize() for w in words.split())\n"),
        ("str_anagram.py", "def is_anagram(a, b):\n    return sorted(a.lower()) == sorted(b.lower())\n"),
        ("str_remove_spaces.py", "def remove_spaces(s):\n    return ''.join(s.split())\n"),
        ("str_find_substring.py", "def find_all(hay, needle):\n    out = []\n    start = 0\n    while True:\n        i = hay.find(needle, start)\n        if i == -1:\n            break\n        out.append(i)\n        start = i + 1\n    return out\n"),
        ("str_char_frequency.py", "def char_frequency(s):\n    d = {}\n    for c in s:\n        d[c] = d.get(c, 0) + 1\n    return d\n"),
        ("list_unique.py", "def unique_preserve(seq):\n    seen = set()\n    out = []\n    for x in seq:\n        if x not in seen:\n            seen.add(x)\n            out.append(x)\n    return out\n"),
        ("list_flatten.py", "def flatten(nested):\n    out = []\n    for item in nested:\n        if isinstance(item, list):\n            out.extend(flatten(item))\n        else:\n            out.append(item)\n    return out\n"),
        ("dict_merge.py", "def merge_dicts(a, b):\n    out = dict(a)\n    out.update(b)\n    return out\n"),
        ("file_read_lines.py", "def read_lines(path):\n    with open(path, 'r', encoding='utf-8') as f:\n        return f.read().splitlines()\n"),
        ("math_primes.py", "def primes_up_to(n):\n    sieve = [True] * (n + 1)\n    sieve[0:2] = [False, False]\n    for i in range(2, int(n ** 0.5) + 1):\n        if sieve[i]:\n            for j in range(i * i, n + 1, i):\n                sieve[j] = False\n    return [i for i, v in enumerate(sieve) if v]\n"),
        ("stack_class.py", "class Stack:\n    def __init__(self):\n        self._items = []\n    def push(self, x):\n        self._items.append(x)\n    def pop(self):\n        return self._items.pop()\n    def peek(self):\n        return self._items[-1] if self._items else None\n"),
    ]
    programs.extend(snippets)

    for name, body in programs[:30]:
        path = DATASET_DIR / name
        path.write_text(body, encoding="utf-8")


def ensure_dataset() -> None:
    """Ensure dataset directory exists and contains at least one .py file."""
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    py_files = list(DATASET_DIR.glob("*.py"))
    if not py_files:
        _generate_sample_programs()


def _load_corpus() -> tuple[list[str], list[str]]:
    ensure_dataset()
    paths: list[str] = []
    contents: list[str] = []
    for p in sorted(DATASET_DIR.glob("*.py")):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if text.strip():
            paths.append(str(p.as_posix()))
            contents.append(text)
    if not contents:
        _generate_sample_programs()
        for p in sorted(DATASET_DIR.glob("*.py")):
            text = p.read_text(encoding="utf-8", errors="replace")
            if text.strip():
                paths.append(str(p.as_posix()))
                contents.append(text)
    return paths, contents


def _build_index() -> None:
    global _faiss_index, _file_paths, _file_contents
    paths, contents = _load_corpus()
    _file_paths = paths
    _file_contents = contents
    model = _get_model()
    emb = model.encode(contents, normalize_embeddings=True, show_progress_bar=False)
    emb = np.asarray(emb, dtype=np.float32)
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)
    _faiss_index = index


def ensure_code_index() -> None:
    global _faiss_index
    if _faiss_index is None:
        _build_index()


def reset_code_index_for_tests() -> None:
    """Clear in-memory index (e.g. after dataset changes)."""
    global _faiss_index, _file_paths, _file_contents
    _faiss_index = None
    _file_paths = []
    _file_contents = []


def analyze_code(user_code: str) -> dict[str, float | str | list[str]]:
    """
    Return max similarity, average of top-3, best file path, top-3 paths.
    Similarities in [0, 1] (cosine on normalized embeddings).
    """
    ensure_code_index()
    if not user_code or not user_code.strip():
        return {
            "max_similarity": 0.0,
            "avg_similarity": 0.0,
            "matched_file": "",
            "top_matches": [],
        }
    model = _get_model()
    q = model.encode([user_code], normalize_embeddings=True, show_progress_bar=False)
    q = np.asarray(q, dtype=np.float32)
    k = min(3, len(_file_paths))
    if k == 0 or _faiss_index is None:
        return {
            "max_similarity": 0.0,
            "avg_similarity": 0.0,
            "matched_file": "",
            "top_matches": [],
        }
    sims, idxs = _faiss_index.search(q, k)
    sims_row = sims[0].astype(np.float64)
    idxs_row = idxs[0]
    max_sim = float(np.max(sims_row))
    avg_sim = float(np.mean(sims_row))
    best_i = int(idxs_row[0]) if len(idxs_row) else 0
    matched = _file_paths[best_i] if 0 <= best_i < len(_file_paths) else ""
    top_paths = [_file_paths[int(i)] for i in idxs_row if 0 <= int(i) < len(_file_paths)]
    return {
        "max_similarity": max(0.0, min(1.0, max_sim)),
        "avg_similarity": max(0.0, min(1.0, avg_sim)),
        "matched_file": matched,
        "top_matches": top_paths,
    }


def get_matched_source(matched_path: str) -> str:
    """Return file contents for highlighting."""
    ensure_code_index()
    try:
        for p, c in zip(_file_paths, _file_contents):
            if p.replace("\\", "/") == matched_path.replace("\\", "/"):
                return c
    except Exception:
        pass
    if matched_path:
        mp = Path(matched_path)
        if mp.is_file():
            return mp.read_text(encoding="utf-8", errors="replace")
    return ""
