import time

import requests

RATE_LIMIT_COOLDOWN = 180  # 3 minutes based on empirical testing
MAX_RATE_LIMIT_RETRIES = 3


def fetch(
    session: requests.Session,
    url: str,
    follow_redirects: bool = True,
    timeout: int = 30,
) -> requests.Response:
    """
    Make HTTP request with rate limit handling.

    Handles 406/429 with 180s cooldown (based on empirical testing).
    Raises RuntimeError if rate limit persists after retries.
    """
    try:
        response = session.get(url, timeout=timeout, allow_redirects=follow_redirects)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        if status in (406, 429):
            return _handle_rate_limit(session, url, status, follow_redirects, timeout)
        raise


def _handle_rate_limit(
    session: requests.Session,
    url: str,
    status: int,
    follow_redirects: bool,
    timeout: int,
) -> requests.Response:
    """Handle rate limiting with cooldown period. Raises on failure."""
    for attempt in range(1, MAX_RATE_LIMIT_RETRIES + 1):
        print(
            f"  Rate limited ({status}), cooling down {RATE_LIMIT_COOLDOWN}s... (attempt {attempt}/{MAX_RATE_LIMIT_RETRIES})"
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
