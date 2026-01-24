import urllib.request
import requests
import tempfile
import os
import gzip
import io
import html


# ---------------------------------------------------------------------------
# HTTP defaults
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


# ---------------------------------------------------------------------------
# Simple URL retrieval
# ---------------------------------------------------------------------------

def retrieve_url(url, timeout=10):
    """
    Retrieve a URL and return its decoded HTML content.

    Uses requests with a standard browser-like User-Agent and
    unescapes HTML entities in the response.

    Args:
        url: URL to retrieve.
        timeout: Request timeout in seconds.

    Returns:
        The response text with HTML entities unescaped, or an empty
        string if any error occurs.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return html.unescape(r.text)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Torrent file downloader
# ---------------------------------------------------------------------------

def download_file(url: str, referer=None, ssl_context=None) -> str:
    """
    Download a file from a URL and write it to a temporary .torrent file.

    Supports optional Referer headers, custom SSL contexts, and
    transparently handles gzip-compressed responses.

    Args:
        url: URL of the file to download.
        referer: Optional HTTP Referer header.
        ssl_context: Optional SSL context for urllib.

    Returns:
        A string containing "<temp_path> <original_url>".
        This format matches qBittorrent plugin expectations.
    """

    # Build request
    request = urllib.request.Request(url, headers=HEADERS)
    if referer:
        request.add_header("Referer", referer)

    # Download raw data
    with urllib.request.urlopen(request, context=ssl_context) as response:
        data = response.read()

    # Detect and decompress gzip responses
    if data[:2] == b"\x1f\x8b":
        with io.BytesIO(data) as bio:
            with gzip.GzipFile(fileobj=bio) as gz:
                data = gz.read()

    # Write to temporary .torrent file
    fd, path = tempfile.mkstemp(suffix=".torrent")
    with os.fdopen(fd, "wb") as f:
        f.write(data)

    # IMPORTANT: return "path url"
    return f"{path} {url}"
