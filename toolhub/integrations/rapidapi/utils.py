from urllib.parse import urlparse

from toolhub.lib.utils import not_none


def sanitize_url(url: str) -> str:
    return url.strip().rstrip("/")


def url_hostname(url: str) -> str:
    return not_none(urlparse(url).hostname)
