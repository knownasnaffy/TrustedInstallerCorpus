"""URL splitting utility for the Trusted Installer Corpus.

Pure function, no side effects. Uses stdlib only.
"""

from urllib.parse import urlparse


def split_url(url: str) -> tuple[str, str]:
    """Split *url* into ``(domain, path)`` where *domain* includes port
    and *path* preserves query string, fragment, and trailing slash.

    Bare domains return ``'/'`` as path.
    """
    parsed = urlparse(url)
    domain = parsed.netloc  # includes port if present

    # Reconstruct full path portion (path + query + fragment)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    if parsed.fragment:
        path = f"{path}#{parsed.fragment}"

    return domain, path
