import argparse
import multiprocessing as mp
import os
import time

from common import chunked, extract_title, fetch_html, init_database, parse_urls_argument, save_page_title


APPROACH = "multiprocessing"
DEFAULT_WORKERS = min(8, os.cpu_count() or 4)


def parse_and_save(url: str) -> tuple[str, str, int]:
    html = fetch_html(url)
    title = extract_title(html)
    task_id = save_page_title(url, title, APPROACH)
    print(f"[{APPROACH}] saved task #{task_id}: {title} ({url})")
    return url, title, task_id


def parse_group(url_group: list[str]) -> list[tuple[str, str, int]]:
    results: list[tuple[str, str, int]] = []
    errors: list[tuple[str, str]] = []

    for url in url_group:
        try:
            results.append(parse_and_save(url))
        except Exception as error:
            errors.append((url, str(error)))

    if errors:
        details = "; ".join(f"{url}: {error}" for url, error in errors)
        raise RuntimeError(f"Failed to parse {len(errors)} URL(s): {details}")

    return results


def run(urls: list[str], workers: int) -> list[tuple[str, str, int]]:
    groups = chunked(urls, workers)

    with mp.Pool(processes=len(groups)) as pool:
        group_results = pool.map(parse_group, groups)

    return [item for group in group_results for item in group]


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse page titles using multiprocessing.")
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
