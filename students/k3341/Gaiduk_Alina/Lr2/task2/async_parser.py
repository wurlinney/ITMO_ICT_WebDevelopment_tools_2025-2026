import argparse
import asyncio
import os
import time

from common import DEFAULT_TIMEOUT, chunked, extract_title, fetch_html, init_database, parse_urls_argument, save_page_title


APPROACH = "asyncio"
DEFAULT_WORKERS = min(8, os.cpu_count() or 4)


try:
    import aiohttp
except ModuleNotFoundError as error:
    aiohttp = None
    AIOHTTP_IMPORT_ERROR = error
else:
    AIOHTTP_IMPORT_ERROR = None


async def fetch_html_async(session: "aiohttp.ClientSession", url: str) -> str:
    if url.lower().startswith("file://"):
        # aiohttp does not support file:// URLs, so load local files in a worker thread.
        return await asyncio.to_thread(fetch_html, url, DEFAULT_TIMEOUT)

    try:
        async with session.get(url, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            return await response.text(errors="replace")
    except aiohttp.ClientResponseError as error:
        if error.status == 403:
            # Некоторые сайты блокируют aiohttp, поэтому пробуем urllib как резервный вариант.
            return await asyncio.to_thread(fetch_html, url, DEFAULT_TIMEOUT)
        raise


async def parse_and_save(
    url: str,
    session: "aiohttp.ClientSession | None" = None,
) -> tuple[str, str, int]:
    if session is None:
        if aiohttp is None:
            raise RuntimeError(
                "aiohttp is required for async_parser.py. Install it with: pip install aiohttp"
            ) from AIOHTTP_IMPORT_ERROR
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as temporary_session:
            return await parse_and_save(url, temporary_session)

    html = await fetch_html_async(session, url)
    title = extract_title(html)
    task_id = await asyncio.to_thread(save_page_title, url, title, APPROACH)
    print(f"[{APPROACH}] saved task #{task_id}: {title} ({url})")
    return url, title, task_id


async def parse_group(
    session: "aiohttp.ClientSession",
    url_group: list[str],
) -> list[tuple[str, str, int]]:
    results: list[tuple[str, str, int]] = []
    errors: list[tuple[str, str]] = []

    parsed = await asyncio.gather(
        *(parse_and_save(url, session) for url in url_group),
        return_exceptions=True,
    )
    for url, item in zip(url_group, parsed):
        if isinstance(item, Exception):
            errors.append((url, str(item)))
        else:
            results.append(item)

    if errors:
        details = "; ".join(f"{url}: {error}" for url, error in errors)
        raise RuntimeError(f"Failed to parse {len(errors)} URL(s): {details}")

    return results


async def run(urls: list[str], workers: int) -> list[tuple[str, str, int]]:
    if aiohttp is None:
        raise RuntimeError("aiohttp is required for async_parser.py. Install it with: pip install aiohttp") from AIOHTTP_IMPORT_ERROR

    groups = chunked(urls, workers)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; LR2Parser/1.0)",
        "Accept": "text/html,application/xhtml+xml",
    }
    timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)

    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        group_results = await asyncio.gather(*(parse_group(session, group) for group in groups))

    return [item for group in group_results for item in group]


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse page titles using asyncio and aiohttp.")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--urls", help="Comma-separated URL list")
    args = parser.parse_args()

    urls = parse_urls_argument(args.urls)
    init_database()

    started_at = time.perf_counter()
    results = asyncio.run(run(urls, args.workers))
    elapsed = time.perf_counter() - started_at

    print(f"Approach: {APPROACH}")
    print(f"Workers: {min(args.workers, len(urls))}")
    print(f"Saved pages: {len(results)}")
    print(f"Elapsed: {elapsed:.6f} seconds")


if __name__ == "__main__":
    main()
