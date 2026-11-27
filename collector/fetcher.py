"""
A deliberately polite HTTP fetcher.

Collection rules this enforces:

* robots.txt is read once per host and honoured. A URL it disallows is never
  fetched. (robots.txt is not the whole story: each retailer's terms of use
  also apply, and are the operator's responsibility to check.)
* Requests to the same host are spaced out, with jitter, so a run of six
  product pages looks like one person browsing rather than a burst.
* Server errors are retried with exponential backoff. Throttling (429/503) and
  bot challenges are not retried within the run: the host is marked "backing
  off" and skipped until the next scheduled run.
* There is no proxy rotation, no CAPTCHA solving and no fingerprint spoofing.
  When a site says stop, the collector stops.
"""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from urllib import robotparser
from urllib.parse import urlparse

import requests


@dataclass
class FetchResult:
    url: str
    status: str            # ok | blocked | throttled | disallowed | http_error | network_error
    http_status: int | None = None
    html: str | None = None
    message: str = ""
    elapsed_ms: int = 0


class PoliteFetcher:
    def __init__(
        self,
        user_agent: str,
        min_delay_seconds: float = 4.0,
        timeout_seconds: float = 20.0,
        respect_robots: bool = True,
        max_retries: int = 2,
        session: requests.Session | None = None,
    ):
        self.user_agent = user_agent
        self.min_delay = max(0.0, min_delay_seconds)
        self.timeout = timeout_seconds
        self.respect_robots = respect_robots
        self.max_retries = max_retries
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-IN,en;q=0.9",
            }
        )
        self._robots: dict[str, robotparser.RobotFileParser | None] = {}
        self._last_request: dict[str, float] = {}
        self._backing_off: set[str] = set()
        self._lock = threading.Lock()

    # ---- robots.txt --------------------------------------------------------

    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parts = urlparse(url)
        host = f"{parts.scheme}://{parts.netloc}"
        if host not in self._robots:
            parser = robotparser.RobotFileParser()
            try:
                response = self.session.get(f"{host}/robots.txt", timeout=self.timeout)
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                    self._robots[host] = parser
                else:
                    # No readable robots.txt: the standard treats that as allow.
                    self._robots[host] = None
            except requests.RequestException:
                self._robots[host] = None
        parser = self._robots[host]
        return True if parser is None else parser.can_fetch(self.user_agent, url)

    # ---- Pacing --------------------------------------------------------------

    def _wait_turn(self, host: str) -> None:
        with self._lock:
            last = self._last_request.get(host)
            if last is not None:
                gap = self.min_delay + random.uniform(0, self.min_delay * 0.5)
                remaining = gap - (time.monotonic() - last)
                if remaining > 0:
                    time.sleep(remaining)
            self._last_request[host] = time.monotonic()

    # ---- Fetch ---------------------------------------------------------------

    def fetch(self, url: str) -> FetchResult:
        host = urlparse(url).netloc
        if host in self._backing_off:
            return FetchResult(url, "throttled", message="host asked us to slow down earlier in this run")
        if not self.allowed(url):
            return FetchResult(url, "disallowed", message="robots.txt disallows this URL for our user agent")

        for attempt in range(self.max_retries + 1):
            self._wait_turn(host)
            started = time.monotonic()
            try:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            except requests.RequestException as error:
                if attempt < self.max_retries:
                    time.sleep(self.min_delay * (2 ** attempt))
                    continue
                return FetchResult(url, "network_error", message=str(error)[:300])

            elapsed = int((time.monotonic() - started) * 1000)
            code = response.status_code

            if code in (429, 503):
                self._backing_off.add(host)
                return FetchResult(url, "throttled", code, message=f"HTTP {code}; skipping host until next run", elapsed_ms=elapsed)
            if code in (403,):
                self._backing_off.add(host)
                return FetchResult(url, "blocked", code, message="HTTP 403 from host", elapsed_ms=elapsed)
            if 500 <= code < 600 and attempt < self.max_retries:
                time.sleep(self.min_delay * (2 ** attempt))
                continue
            if code != 200:
                return FetchResult(url, "http_error", code, message=f"HTTP {code}", elapsed_ms=elapsed)
            return FetchResult(url, "ok", code, html=response.text, elapsed_ms=elapsed)

        return FetchResult(url, "http_error", message="retries exhausted")

    def mark_blocked(self, url: str) -> None:
        """Called when a 200 response turns out to be a challenge page."""
        self._backing_off.add(urlparse(url).netloc)
