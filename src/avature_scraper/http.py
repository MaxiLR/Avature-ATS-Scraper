import threading
import time

import requests

RATE_LIMIT_COOLDOWN = 180  # 3 minutes based on empirical testing
MAX_RATE_LIMIT_RETRIES = 3

_rate_limit_lock = threading.Lock()
_rate_limit_until = 0.0


def fetch(
    session: requests.Session,
    url: str,
    follow_redirects: bool = True,
    timeout: int = 30,
) -> requests.Response:
    """
    Make HTTP request with rate limit handling.

    Handles 406/429 with 180s cooldown (based on empirical testing).
    All workers pause when any worker hits rate limit.
    Raises RuntimeError if rate limit persists after retries.
    """
    global _rate_limit_until

    _wait_for_rate_limit()

    try:
        response = session.get(url, timeout=timeout, allow_redirects=follow_redirects)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        if status in (406, 429):
            return _handle_rate_limit(session, url, status, follow_redirects, timeout)
        raise


def _wait_for_rate_limit():
    """Wait if a global rate limit cooldown is active."""
    global _rate_limit_until

    with _rate_limit_lock:
        wait_time = _rate_limit_until - time.time()
        if wait_time > 0:
            print(f"  Waiting {wait_time:.0f}s for global rate limit cooldown...")

    if wait_time > 0:
        time.sleep(wait_time)


def _handle_rate_limit(
    session: requests.Session,
    url: str,
    status: int,
    follow_redirects: bool,
    timeout: int,
) -> requests.Response:
    """Handle rate limiting with cooldown period. All workers pause."""
    global _rate_limit_until

    for attempt in range(1, MAX_RATE_LIMIT_RETRIES + 1):
        with _rate_limit_lock:
            _rate_limit_until = time.time() + RATE_LIMIT_COOLDOWN
            print(
                f"  Rate limited ({status}), ALL workers cooling down {RATE_LIMIT_COOLDOWN}s... (attempt {attempt}/{MAX_RATE_LIMIT_RETRIES})"
            )

        time.sleep(RATE_LIMIT_COOLDOWN)

        try:
            response = session.get(
                url, timeout=timeout, allow_redirects=follow_redirects
            )
            response.raise_for_status()
            print(f"  Rate limit recovered after {attempt} cooldown(s)")
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code not in (406, 429):
                raise

    raise RuntimeError(
        f"Rate limit not recovered after {MAX_RATE_LIMIT_RETRIES} cooldowns. Aborting."
    )
