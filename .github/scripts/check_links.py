#!/usr/bin/env python3
"""
Check every external URL in README.md still resolves.

The profile depends on a number of third-party hosts — shields.io badges, the
project sites, and personally-hosted stats widgets. When one goes cold the
README quietly renders broken images with nothing to signal it, so this runs on
a schedule and fails the job instead.

Exit codes:
    0 - every URL resolved
    1 - at least one URL failed
"""

import re
import sys
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen

README_PATH = "README.md"
TIMEOUT = 25
ATTEMPTS = 3

# github.com closes the connection on a bare urllib request, so the headers
# below mirror a normal browser. A checker that cries wolf weekly is worse than
# no checker, which is also why connection-level failures are retried.
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Hosts that answer bots with a non-200 while working fine in a browser.
# LinkedIn returns 999 to any non-browser agent.
TOLERATED = {
    "www.linkedin.com": {999, 403, 405},
    "linkedin.com": {999, 403, 405},
    "discord.com": {403, 405},
}

URL_RE = re.compile(r'https://[^\s"\')<>]+')


def urls_in_readme():
    with open(README_PATH, encoding='utf-8') as f:
        content = f.read()
    found = {u.rstrip('.,)') for u in URL_RE.findall(content)}
    return sorted(found)


def host_of(url):
    return url.split('/')[2] if '://' in url else ''


def check(url):
    """Return (url, status, ok). Retries connection-level failures."""
    req = Request(url, headers=HEADERS)
    last = None
    for attempt in range(ATTEMPTS):
        try:
            with urlopen(req, timeout=TIMEOUT) as r:
                return url, r.status, True
        except urllib.error.HTTPError as e:
            # An HTTP response is a real answer, so do not retry it.
            tolerated = TOLERATED.get(host_of(url), set())
            return url, e.code, e.code in tolerated
        except Exception as e:
            last = type(e).__name__
            if attempt < ATTEMPTS - 1:
                time.sleep(2 * (attempt + 1))
    return url, last, False


def main():
    urls = urls_in_readme()
    if not urls:
        print("No URLs found in README - nothing to check", file=sys.stderr)
        return 1

    print(f"Checking {len(urls)} URLs from {README_PATH}\n")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check, urls))

    failures = [(u, s) for u, s, ok in results if not ok]
    for url, status, ok in sorted(results, key=lambda r: (r[2], r[0])):
        print(f"{'ok  ' if ok else 'FAIL'}  {status}  {url}")

    print()
    if failures:
        print(f"{len(failures)} of {len(urls)} URLs failed:")
        for url, status in failures:
            print(f"  {status}  {url}")
        return 1

    print(f"All {len(urls)} URLs resolved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
