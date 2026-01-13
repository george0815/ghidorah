import urllib.request
import requests
import tempfile
import os
import gzip
import io
import html

HEADERS = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }

def retrieve_url(url, timeout=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return html.unescape(r.text)
    except Exception:
        return ""


def download_file(url: str, referer=None, ssl_context=None) -> str:
    # Build request
    request = urllib.request.Request(url, headers=HEADERS)
    if referer:
        request.add_header("Referer", referer)

    # Download
    with urllib.request.urlopen(request, context=ssl_context) as response:
        data = response.read()

    # Handle gzip
    if data[:2] == b"\x1f\x8b":
        with io.BytesIO(data) as bio:
            with gzip.GzipFile(fileobj=bio) as gz:
                data = gz.read()

    # Write to temp file
    fd, path = tempfile.mkstemp(suffix=".torrent")
    with os.fdopen(fd, "wb") as f:
        f.write(data)

    # IMPORTANT: return "path url"
    return f"{path} {url}"
