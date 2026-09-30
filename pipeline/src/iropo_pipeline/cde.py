"""Minimal, polite client for the FBI Crime Data Explorer (CDE).

Two interchangeable backends serve the same data:

* ``https://api.usa.gov/crime/fbi/cde`` - the documented API gateway. Requires a free
  api.data.gov key, supplied through the ``FBI_API_KEY`` environment variable and sent in the
  ``X-Api-Key`` header.
* ``https://cde.ucr.cjis.gov/LATEST`` - the public backend used by the CDE website. No key is
  needed, so contributors can run the pipeline without signing up. Requests are throttled.

Bulk NIBRS table downloads are only exposed through the public backend's signed-URL endpoint.
"""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from iropo_pipeline.config import USER_AGENT

OFFICIAL_BASE = "https://api.usa.gov/crime/fbi/cde"
PUBLIC_BASE = "https://cde.ucr.cjis.gov/LATEST"
RETRY_STATUSES = {429, 500, 502, 503, 504}


class NotAvailable(Exception):
    """Raised when a requested file has not been published (yet)."""


@dataclass
class CdeClient:
    base_url: str = PUBLIC_BASE
    api_key: str | None = None
    min_interval: float = 0.75
    max_retries: int = 5
    session: requests.Session = field(default_factory=requests.Session)
    _last_request: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    @classmethod
    def from_env(cls) -> CdeClient:
        key = os.environ.get("FBI_API_KEY", "").strip() or None
        base = os.environ.get("CDE_API_BASE", "").strip() or (OFFICIAL_BASE if key else PUBLIC_BASE)
        return cls(base_url=base, api_key=key)

    def url_for(self, path: str, params: dict[str, Any] | None = None) -> str:
        """Public URL for a request (never includes the API key)."""
        query = f"?{urlencode(params)}" if params else ""
        return f"{self.base_url}/{path.lstrip('/')}{query}"

    def _throttle(self) -> None:
        wait = self.min_interval - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def _request(
        self,
        url: str,
        params: dict[str, Any] | None,
        *,
        stream: bool = False,
        timeout: float = 90,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        for attempt in range(self.max_retries):
            self._throttle()
            try:
                response = self.session.get(
                    url, params=params, timeout=timeout, stream=stream, headers=headers
                )
            except (requests.ConnectionError, requests.Timeout):
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** (attempt + 1))
                continue
            if response.status_code in RETRY_STATUSES and attempt < self.max_retries - 1:
                retry_after = response.headers.get("Retry-After", "")
                time.sleep(int(retry_after) if retry_after.isdigit() else 2 ** (attempt + 1))
                continue
            return response
        raise RuntimeError(f"Exhausted retries for {url}")

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        # The key travels only in a header, and only to the official gateway, so it never appears
        # in URLs, logs or exception messages.
        headers = (
            {"X-Api-Key": self.api_key} if self.api_key and self.base_url != PUBLIC_BASE else None
        )
        public_url = self.url_for(path, params)
        try:
            response = self._request(f"{self.base_url}/{path.lstrip('/')}", params, headers=headers)
        except requests.RequestException as exc:
            raise RuntimeError(f"Request failed for {public_url}: {type(exc).__name__}") from None
        if response.status_code == 404:
            raise NotAvailable(public_url)
        if not response.ok:
            raise RuntimeError(f"HTTP {response.status_code} for {public_url}")
        return response.json()

    def signed_url(self, key: str) -> str:
        response = self._request(f"{PUBLIC_BASE}/s3/signedurl", {"key": key})
        response.raise_for_status()
        url = (response.json() or {}).get(key)
        if not url:
            raise NotAvailable(key)
        return url

    def download(self, url: str, dest: Path) -> str:
        """Stream ``url`` to ``dest`` and return its SHA-256 digest."""
        response = self._request(url, None, stream=True, timeout=300)
        if response.status_code in (403, 404):
            raise NotAvailable(url.split("?", 1)[0])
        response.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with tmp.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1 << 16):
                handle.write(chunk)
                digest.update(chunk)
        tmp.replace(dest)
        return digest.hexdigest()
