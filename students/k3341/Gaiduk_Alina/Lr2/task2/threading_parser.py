import argparse
import os
import threading
import time

from common import chunked, extract_title, fetch_html, init_database, parse_urls_argument, save_page_title


APPROACH = "threading"
DEFAULT_WORKERS = min(8, os.cpu_count() or 4)


def parse_and_save(url: str) -> tuple[str, str, int]:
    html = fetch_html(url)
    title = extract_title(html)
    task_id = save_page_title(url, title, APPROACH)
    print(f"[{APPROACH}] saved task #{task_id}: {title} ({url})")
    return url, title, task_id


def run(urls: list[str], workers: int) -> list[tuple[str, str, int]]:
    results: list[tuple[str, str, int]] = []
    errors: list[tuple[str, Exception]] = []
    results_lock = threading.Lock()

    def worker(url_group: list[str]) -> None:
        for url in url_group:
            try:
                result = parse_and_save(url)
            except Exception as error:
                with results_lock:
                    errors.append((url, error))
            else:
                with results_lock:
                    results.append(result)

    threads = [
        threading.Thread(target=worker, args=(url_group,))
        for url_group in chunked(urls, workers)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    if errors:
        details = "; ".join(f"{url}: {error}" for url, error in errors)
        raise RuntimeError(f"Failed to parse {len(errors)} URL(s): {details}")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse page titles using threading.")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--urls", help="Comma-separated URL list")
    args = parser.parse_args()

    urls = parse_urls_argument(args.urls)
    init_database()

    started_at = time.perf_counter()
    results = run(urls, args.workers)
    elapsed = time.perf_counter() - started_at

    print(f"Approach: {APPROACH}")
    print(f"Workers: {min(args.workers, len(urls))}")
    print(f"Saved pages: {len(results)}")
    print(f"Elapsed: {elapsed:.6f} seconds")


if __name__ == "__main__":
    main()
