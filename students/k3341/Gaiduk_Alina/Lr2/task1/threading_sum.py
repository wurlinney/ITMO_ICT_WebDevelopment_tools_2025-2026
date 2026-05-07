import argparse
import os
import threading
import time


START = 1
END = 10_000_000_000_000
DEFAULT_WORKERS = min(8, os.cpu_count() or 4)


def calculate_sum(start: int, end: int) -> int:
    # Сумма диапазона считается по формуле арифметической прогрессии.
    """Return the sum of all integers from start to end, inclusive."""
    return (start + end) * (end - start + 1) // 2


def split_range(start: int, end: int, parts: int) -> list[tuple[int, int]]:
    # Делим общий диапазон на почти равные части для потоков.
    total_numbers = end - start + 1
    chunk_size, remainder = divmod(total_numbers, parts)

    ranges = []
    current = start
    for index in range(parts):
        current_size = chunk_size + (1 if index < remainder else 0)
        chunk_end = current + current_size - 1
        ranges.append((current, chunk_end))
        current = chunk_end + 1

    return ranges


def run(workers: int) -> int:
    # Каждый поток считает сумму в своей части диапазона.
    ranges = split_range(START, END, workers)
    partial_sums = [0] * workers
    threads = []

    def worker(index: int, start: int, end: int) -> None:
        partial_sums[index] = calculate_sum(start, end)

    for index, (start, end) in enumerate(ranges):
        thread = threading.Thread(target=worker, args=(index, start, end))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Складываем частичные суммы и получаем итог.
    return sum(partial_sums)


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate sum using threading.")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS)
    args = parser.parse_args()

    if args.workers < 1:
        raise ValueError("workers must be greater than zero")

    started_at = time.perf_counter()
    result = run(args.workers)
    elapsed = time.perf_counter() - started_at

    expected = calculate_sum(START, END)
    print(f"Approach: threading")
    print(f"Workers: {args.workers}")
    print(f"Result: {result}")
    print(f"Expected: {expected}")
    print(f"Correct: {result == expected}")
    print(f"Elapsed: {elapsed:.6f} seconds")


if __name__ == "__main__":
    main()
