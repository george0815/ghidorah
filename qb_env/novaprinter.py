"""
Lightweight result collector used by qBittorrent-style search plugins.

Plugins call `prettyPrinter()` to emit results, which are stored
in a module-level buffer. Call `get_results()` to retrieve and
clear the buffer.
"""

_RESULTS = []


def prettyPrinter(data):
    """
    Collect a single result entry.

    This function mimics qBittorrent's expected novaprinter API.
    Plugins call this repeatedly to emit search results.

    Args:
        data: A dictionary representing a single search result.
    """
    _RESULTS.append(data)


def get_results():
    """
    Retrieve and clear all collected results.

    Returns:
        A list of result dictionaries accumulated since the last call.
    """
    global _RESULTS
    out = _RESULTS
    _RESULTS = []
    return out
