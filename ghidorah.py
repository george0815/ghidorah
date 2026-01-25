"""
Ghidorah - A multi-source torrent search tool 

Author: George Hunter S.
Created: Jan, 2026

"""

# ---------------------------------------------------------------------------
# PROGRAM OVERVIEW
#
# The main script (this file) imports the default sources (from /sources) and
# calls functions from ghidorah_qb to import qBittorrent plugin sources. It also
# handles both headless CLI entry and the interactive CLI interface.
#
# If the program is run without arguments, the main interactive CLI is started.
# If the program is run with arguments, it operates in headless mode.
#
# Searching is handled by the main search function, which collects results from
# all sources and normalizes them into a common format.
# ---------------------------------------------------------------------------


from InquirerPy import prompt
from InquirerPy.separator import Separator
from sources.thepiratebay import ThePirateBay
from sources.kickasstorrents import KickAssTorrents
from sources.limetorrents import LimeTorrents
from sources.yts import YTS
from sources.x1337 import X1337
from sources.torrentgalaxy import TorrentGalaxy
from tabulate import tabulate
from qb_env.ghidorah_qb import print_path_debug
from qb_env.ghidorah_qb import detect_qb_plugins, run_qb_plugin
from colorama import Fore
import contextlib
import os
from datetime import datetime
from termcolor import colored
import json
import re
import argparse
import sys



# Handle both PyInstaller-frozen and normal script execution by resolving the
# correct runtime directory, ensuring the external `qb_env` directory is on
# sys.path, and forcing UTF-8 stdout/stderr to avoid encoding issues in packaged
# builds.

RUNTIME_ROOT = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)

QB_ENV_DIR = os.path.join(RUNTIME_ROOT, "qb_env")
if QB_ENV_DIR not in sys.path:
    sys.path.insert(0, QB_ENV_DIR)

    
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

external_qb_env = os.path.join(base_dir, "qb_env")
if external_qb_env not in sys.path:
    sys.path.insert(0, external_qb_env)



# -------------------
# Helper functions
# -------------------


def normalize_category(category: str | None) -> str:
    """
    Normalize custom categories to valid qBittorrent plugin categories.

    Valid qB categories:
    all, anime, books, games, movies, music, pictures, software, tv
    """

    if not category:
        return "all"

    category = category.strip().lower()

    CATEGORY_MAP = {
        "movies": "movies",
        "movie": "movies",

        "tv shows": "tv",
        "tv": "tv",
        "television": "tv",

        "application": "software",
        "app": "software",
        "apps": "software",
        "software": "software",

        "games": "games",
        "game": "games",

        "music": "music",

        "anime": "anime",
        "books": "books",
        "pictures": "pictures",

        "other": "all",
        "misc": "all",
        "unknown": "all",
    }

    return CATEGORY_MAP.get(category, "all")


def qb_missing(value):
    """Return True if a qBittorrent-style field should be treated as missing."""
    return value in (None, "", -1)


def safe_int(value, default=0):
    """
    Safely convert a value to int.

    Returns the provided default if the value is missing or cannot be converted.
    """
    try:
        if qb_missing(value):
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_date(unix_ts):
    """
    Convert a UNIX timestamp to a human-readable date string (MM/DD/YYYY).

    Returns 'N/A' if the timestamp is missing, invalid, or out of range.
    """
    try:
        if qb_missing(unix_ts):
            return "N/A"
        return datetime.fromtimestamp(int(unix_ts)).strftime("%m/%d/%Y")
    except (ValueError, TypeError, OSError):
        return "N/A"


# ---------------------------------------------------------------------------
# Source registry and source lists
# ---------------------------------------------------------------------------

# Mapping of source identifiers to their corresponding source classes
SOURCE_REGISTRY = {
    "kickasstorrents": KickAssTorrents,
    "thepiratebay": ThePirateBay,
    "limetorrents": LimeTorrents,
    "yts": YTS,
    "x1337": X1337,
    "torrentgalaxy": TorrentGalaxy,
}

# Built-in sources always available to the application
BASE_SOURCE_LIST = [
    "kickasstorrents",
    "thepiratebay",
    "limetorrents",
    "yts",
    "x1337",
    "torrentgalaxy",
]

# Detect externally installed qBittorrent search plugins
engines = detect_qb_plugins()

# Plugin-provided source names
QB_SOURCE_LIST = engines.keys()

# Final list of all enabled sources (plugins + built-ins)
SOURCES = list(QB_SOURCE_LIST) + list(BASE_SOURCE_LIST)


# ---------------------------------------------------------------------------
# Sorting configuration
# ---------------------------------------------------------------------------

# Mapping of UI sort options to sort keys and direction
SORT_MAP = {
    "Name": {
        "key": lambda x: x["name"].lower(),
        "reverse": False,
    },
    "Size": {
        "key": lambda x: x["size"],
        "reverse": True,
    },
    "Seeders": {
        "key": lambda x: int(x["seeders"]) if str(x["seeders"]).isdigit() else 0,
        "reverse": True,
    },
    "Source": {
        "key": lambda x: x["source"].lower(),
        "reverse": False,
    },
}


# ---------------------------------------------------------------------------
# Normalized result schema
# ---------------------------------------------------------------------------

# Default values for normalized search result fields
NORMALIZED_FIELDS = {
    "name": "N/A",
    "size": "N/A",
    "seeders": 0,
    "leechers": 0,
    "category": "N/A",
    "url": "N/A",
    "date": "N/A",
    "hash": "N/A",
    "magnet": "N/A",
    "source": "N/A",
}




# ---------------------------------------------------------------------------
# Output suppression utilities
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def suppress_stdout():
    """
    Temporarily suppress stdout output.

    Useful for silencing noisy third-party libraries or plugins during
    execution without permanently redirecting stdout.
    """
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout


# ---------------------------------------------------------------------------
# Search execution
# ---------------------------------------------------------------------------

def run_search(query, settings):
    """
    Execute a search across enabled sources and normalize the results.

    Depending on configuration, searches are performed either via built-in
    sources or via detected qBittorrent plugins. Results from all sources
    are normalized into a common schema and optionally sorted based on
    user-defined settings.

    Args:
        query: Search query string.
        settings: Dictionary of runtime configuration options.

    Returns:
        A dictionary containing:
            - "data": A list of normalized search results.
            - "errors": A list of error messages encountered per source.
    """
    results = {
        "data": [],
        "errors": [],
    }

    # -----------------------------------------------------------------------
    # Built-in source search path
    # -----------------------------------------------------------------------

    if not settings["use_qb_plugins"]:

        for source_name in settings["sources"]:
            source_class = SOURCE_REGISTRY.get(source_name)

            # Skip unknown or unsupported sources
            if not source_class:
                continue

            try:
                instance = source_class(settings)
                response = instance.search(query)

                for item in response.get("data", []):
                    normalized_item = normalize_result(
                        item,
                        source_name,
                        settings["use_qb_plugins"],
                    )
                    results["data"].append(normalized_item)

            except Exception as e:
                results["errors"].append(f"Error with {source_name}: {e}")

        # Apply sorting after collecting results
        sort_config = SORT_MAP.get(settings["sort_by"])
        if sort_config:
            results["data"].sort(
                key=sort_config["key"],
                reverse=sort_config["reverse"],
            )

    # -----------------------------------------------------------------------
    # qBittorrent plugin search path
    # -----------------------------------------------------------------------

    else:

        for source_name in settings["sources"]:
            if source_name not in engines:
                continue

            try:
                norm_cat = normalize_category(settings["categories"][0])
                cat = (
                    norm_cat
                    if norm_cat in getattr(
                        engines[source_name],
                        "supported_categories",
                        {"all": ""},
                    )
                    else "all"
                )

                plugin_results = run_qb_plugin(
                    source_name,
                    query,
                    cat,
                )

                for item in plugin_results:
                    normalized_item = normalize_result(
                        item,
                        source_name,
                        settings["use_qb_plugins"],
                    )
                    results["data"].append(normalized_item)

            except Exception as e:
                results["errors"].append(f"Error with {source_name}: {e}")

            # Apply sorting after each plugin execution
            sort_config = SORT_MAP.get(settings["sort_by"])
            if sort_config:
                results["data"].sort(
                    key=sort_config["key"],
                    reverse=sort_config["reverse"],
                )

        pass

    return results



# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def cli_entry():
    """
    Command-line interface entry point.

    Parses CLI arguments, handles status and plugin checks, and dispatches
    search execution in either interactive or headless mode.
    """
    parser = argparse.ArgumentParser(
        description="Ghidorah Torrent Search CLI"
    )

    # Positional arguments
    parser.add_argument("query", nargs="?", help="Search query")

    # Optional arguments
    parser.add_argument(
        "--limit",
        type=int,
        default=2,
        help="Number of results per source",
    )
    parser.add_argument(
        "--total_limit",
        type=int,
        default=10,
        help="Total number of results to display",
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="+",
        default=[
            "Movies",
            "TV Shows",
            "Application",
            "Games",
            "Music",
            "Other",
        ],
        help="Categories to search in",
    )
    parser.add_argument(
        "--sort_by",
        type=str,
        choices=["Name", "Size", "Seeders", "Source"],
        default="Source",
        help="Sort results by",
    )
    parser.add_argument(
        "--sources",
        type=str,
        nargs="+",
        choices=SOURCES,
        default=SOURCES,
        help="Sources to search from",
    )

    # Feature flags
    parser.add_argument(
        "--use_qb_plugins",
        action="store_true",
        help="Enable qBittorrent plugins",
    )
    parser.add_argument(
        "--check_status",
        action="store_true",
        help="Check availability of built-in sources",
    )
    parser.add_argument(
        "--check_plugins",
        action="store_true",
        help="List detected qBittorrent plugins",
    )

    args = parser.parse_args()

    # -----------------------------------------------------------------------
    # Status check mode
    # -----------------------------------------------------------------------

    if args.check_status:
        output = {
            "paths": print_path_debug(),
            "message": "Checking status...",
            "results": [],
        }

        # Suppress noisy output from source checks
        with suppress_stdout():
            for source in [
                KickAssTorrents,
                ThePirateBay,
                LimeTorrents,
                YTS,
                X1337,
                TorrentGalaxy,
            ]:
                try:
                    settings = {
                        "limit": 1,
                        "total_limit": args.total_limit,
                        "categories": args.categories,
                        "sort_by": args.sort_by,
                        "use_qb_plugins": args.use_qb_plugins,
                        "sources": args.sources,
                    }

                    instance = source(settings)
                    result = instance.search("test")

                    if result.get("data"):
                        output["results"].append({
                            "source": source.__name__,
                            "status": "ONLINE",
                            "results": len(result["data"]),
                        })
                    else:
                        output["results"].append({
                            "source": source.__name__,
                            "status": "OFFLINE",
                            "results": 0,
                        })

                except Exception as e:
                    output["results"].append({
                        "source": source.__name__,
                        "status": "ERROR",
                        "error": str(e),
                    })

        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)

    # -----------------------------------------------------------------------
    # Plugin listing mode
    # -----------------------------------------------------------------------

    elif args.check_plugins:
        print(json.dumps(list(QB_SOURCE_LIST), ensure_ascii=False))
        sys.exit(0)

    # -----------------------------------------------------------------------
    # Search execution mode
    # -----------------------------------------------------------------------

    if not args.query:
        parser.error(
            "the following argument is required: query "
            "(unless --check-status or --check-plugins is used)"
        )

    else:
        settings = {
            "limit": args.limit,
            "total_limit": args.total_limit,
            "categories": args.categories,
            "sort_by": args.sort_by,
            "use_qb_plugins": args.use_qb_plugins,
            "sources": args.sources,
        }

        try:
            # Suppress plugin and source stdout noise
            with suppress_stdout():
                if not args.use_qb_plugins:
                    settings["sources"] = (
                        set(BASE_SOURCE_LIST) & set(args.sources)
                    )
                else:  
                    if not QB_SOURCE_LIST:
                        raise Exception("Error: The --use_qb_plugins argument was passed, but no qBittorrent plugins were found.") 
                    else:
                        settings["sources"] = (
                            set(QB_SOURCE_LIST) & set(args.sources)
                        )

                results = run_search(args.query, settings)

            print(json.dumps(results, ensure_ascii=False))
            sys.exit(0)

        except Exception as e:
            print(f"An error occurred: {e}")


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def print_icon():
    """Print the Ghidorah ASCII art logo."""
    print(
        colored(
            """⠈⠉⠛⣶⣶⣶⣦⣤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⣤⣶⣶⣶⡟⠋⠁
⠀⠀⠀⠈⠹⣿⣿⣿⣿⣿⣷⣦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣶⣿⣿⣿⣿⣿⡟⠉⠀⠀⠀
⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⣴⠀⠀⠀⠀⠀⠀⠀⣀⣄⡀⠀⠀⠀⠀⠀⠀⢸⣤⣾⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠋⠀⠀⣠⣾⣦⠀⠀⣻⣿⡁⠀⣠⡾⣦⠀⠀⠈⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡀⠀⠀⠀⠀
⠀⠀⠀⠀⠘⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⢸⣿⡏⣿⡇⢠⣿⣿⣧⠀⣿⡏⣿⣯⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠛⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⢘⡿⠀⣿⠁⠀⣿⣿⡇⠀⢿⡇⠸⣏⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠄⠀⠀⠀⠀
⠀⠀⠀⠀⡰⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠁⢸⣿⠀⠀⣿⣿⡇⠀⢸⣷⠀⠁⠀⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠳⡀⠀⠀⠀
⠀⠀⠀⠀⢠⣿⣿⡿⠿⣿⣿⣿⣿⣿⣿⣿⣆⠀⠀⠀⢸⣿⡀⠀⣿⣿⡇⠀⣼⣿⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⡿⠿⣿⣿⣧⠀⠀⠀⠀
⠀⠀⠀⠀⡾⠻⠋⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣷⣄⡀⠸⣿⣷⣴⣿⣿⣷⣴⣿⡯⠀⣀⣴⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠈⠻⢻⡆⠀⠀⠀
⠀⠀⠀⠸⠃⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡻⡿⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⢳⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⠟⠋⠉⠀⢿⣿⣿⣿⡿⠟⠻⠿⣿⣿⣿⣾⣿⣿⠿⠿⠛⠿⣿⣿⣿⣟⠇⠈⠉⠛⢿⣷⠀⠀⠀⠀⠈⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠞⠁⠀⠀⠀⠀⠈⣿⡿⠋⠀⠀⠀⠀⠈⢿⣽⢿⣿⣿⣶⠀⠀⠀⠈⠻⣿⡇⠀⠀⠀⠀⠀⠙⠆⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠟⠀⢰⣦⡄⠀⢸⣷⣾⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠘⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠈⢿⠇⠀⠸⣿⣿⣿⣿⣿⣻⣿⠞⡆⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣤⣤⣀⠀⠀⢀⡟⠀⢰⠷⣿⣧⣹⣿⡍⠋⠁⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⡟⠉⠀⠉⠙⢿⣦⡛⠀⠀⠈⠀⠀⠈⢸⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⠶⠶⠶⠞⠋⠈⠻⢶⣤⣀⡀⢀⣀⣾⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠛⠛⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀""",
            "red",
        )
    )


# ---------------------------------------------------------------------------
# Diagnostic helpers
# ---------------------------------------------------------------------------

def check_status():
    """
    Print a human-readable status report for all built-in sources.
    """
    print(print_path_debug())
    print("Checking status...")

    settings = {
        "limit": 1,
        "total_limit": 10,
        "categories": [
            "Movies",
            "TV Shows",
            "Application",
            "Games",
            "Music",
            "Other",
        ],
        "sort_by": "Source",
        "use_qb_plugins": False,
        "sources": SOURCES,
    }

    for source in [
        KickAssTorrents,
        ThePirateBay,
        LimeTorrents,
        YTS,
        X1337,
        TorrentGalaxy,
    ]:
        try:
            instance = source(settings)
            result = instance.search("test")

            if len(result.get("data", [])) > 0:
                print(
                    f"{source.__name__}: "
                    f"{Fore.GREEN}ONLINE{Fore.RESET} - "
                    f"{len(result['data'])} result(s) found"
                )
            else:
                print(
                    f"{source.__name__}: "
                    f"{Fore.RED}OFFLINE{Fore.RESET} - "
                    f"No result(s) found"
                )

        except Exception as e:
            print(
                f"{source.__name__}: "
                f"{Fore.RED}ERROR{Fore.RESET} - {e}"
            )


# ---------------------------------------------------------------------------
# Size parsing helpers
# ---------------------------------------------------------------------------

# Regex used to parse human-readable size strings (e.g., "1.5 GB", "700 MiB")
_SIZE_RE = re.compile(
    r"(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>kib|kb|mib|mb|gib|gb|tib|tb|b)?",
    re.IGNORECASE,
)

# Unit multipliers for converting parsed sizes into bytes
_MULTIPLIERS_BYTES = {
    "b": 1,
    "kib": 1024,
    "kb": 1024,
    "mib": 1024 ** 2,
    "mb": 1024 ** 2,
    "gib": 1024 ** 3,
    "gb": 1024 ** 3,
    "tib": 1024 ** 4,
    "tb": 1024 ** 4,
}



# ---------------------------------------------------------------------------
# Size parsing and formatting utilities
# ---------------------------------------------------------------------------

def parse_size(size) -> int:
    """
    Parse a human-readable size string into bytes.

    Accepts numeric values, strings with units (e.g. "1.5 GB", "700 MiB"),
    and ranges (e.g. "7.9~8.5 GB"). Always returns an integer byte count
    and never raises an exception.
    """

    # Already numeric → assume bytes
    if isinstance(size, (int, float)):
        return int(size)

    # Handle missing or invalid values
    if not size or size in ("N/A", "-1"):
        return 0

    s = str(size).lower().strip()

    # Handle ranges like "7.9~8.5", "7.9 - 8.5 gb"
    if "~" in s or "-" in s:
        parts = re.split(r"[~-]", s)
        for part in reversed(parts):  # Prefer upper bound
            val = parse_size(part)
            if val > 0:
                return val
        return 0

    match = _SIZE_RE.search(s)
    if not match:
        return 0

    try:
        number = float(match.group("num"))
    except (TypeError, ValueError):
        return 0

    unit = match.group("unit") or "b"
    multiplier = _MULTIPLIERS_BYTES.get(unit, 1)

    return int(number * multiplier)


def format_size_bytes(num_bytes: int, precision: int = 1) -> str:
    """
    Format a byte count into a human-readable string using binary units.
    """

    try:
        num_bytes = float(num_bytes)
    except (TypeError, ValueError):
        return "0 B"

    if num_bytes <= 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    step = 1024.0

    for unit in units:
        if num_bytes < step:
            if unit == "B":
                return f"{int(num_bytes)} {unit}"
            return f"{num_bytes:.{precision}f} {unit}"
        num_bytes /= step

    return f"{num_bytes:.{precision}f} PB"


# ---------------------------------------------------------------------------
# Result normalization
# ---------------------------------------------------------------------------

def normalize_result(item, source_name, qb):
    """
    Normalize a raw search result into the common result schema.

    Handles both built-in sources and qBittorrent plugin results.
    """

    if not qb:
        normalized = NORMALIZED_FIELDS.copy()

        for key in normalized:
            if key in item and item[key] not in [None, ""]:
                normalized[key] = item[key]

        normalized["source"] = source_name
        normalized["size"] = parse_size(normalized["size"])
        return normalized

    else:
        return {
            "name": item.get("name") if not qb_missing(item.get("name")) else "N/A",
            "size": parse_size(item.get("size")) if not qb_missing(item.get("size")) else "N/A",
            "seeders": safe_int(item.get("seeds")),
            "leechers": safe_int(item.get("leech")),
            "category": "N/A",
            "source": source_name,
            "url": item.get("engine_url") if not qb_missing(item.get("engine_url")) else "N/A",
            "date": safe_date(item.get("pub_date")),
            "hash": "N/A",  # qBittorrent plugins never provide this
            "magnet": item.get("link") if not qb_missing(item.get("link")) else "N/A",
        }


# ---------------------------------------------------------------------------
# Application control helpers
# ---------------------------------------------------------------------------

def exit_app():
    """Exit the application cleanly."""
    print("Exiting application...")
    raise SystemExit


def truncate(text, length=40):
    """Truncate text to a maximum length, appending ellipsis if needed."""
    return text if len(text) <= length else text[:length - 3] + "..."


# ---------------------------------------------------------------------------
# Settings menu
# ---------------------------------------------------------------------------

def settings_menu(settings):
    """
    Interactive settings menu for modifying search configuration.
    """
    while True:
        answer = prompt([
            {
                "type": "list",
                "name": "settings_action",
                "message": "Settings",
                "choices": [
                    "Limit",
                    "Total Limit",
                    "Use qBittorrent plugins",
                    "Categories",
                    "Sort by",
                    "Sources",
                    Separator(),
                    "Back",
                ],
            }
        ])["settings_action"]

        if answer == "Limit":
            result = prompt([
                {
                    "type": "number",
                    "name": "limit",
                    "message": "Set result limit:",
                    "default": None,
                    "min_allowed": 1,
                }
            ])
            settings["limit"] = int(result["limit"]) if result["limit"] is not None else 2

        elif answer == "Total Limit":
            result = prompt([
                {
                    "type": "number",
                    "name": "total_limit",
                    "message": "Set total result limit:",
                    "default": None,
                    "min_allowed": 1,
                }
            ])
            settings["total_limit"] = int(result["total_limit"]) if result["total_limit"] is not None else 10

        elif answer == "Use qBittorrent plugins":
            result = prompt([
                {
                    "type": "confirm",
                    "name": "use_qb_plugins",
                    "message": "Enable qBittorrent plugins?",
                    "default": settings.get("use_qb_plugins", False),
                }
            ])
            if not QB_SOURCE_LIST and result["use_qb_plugins"]:
                print("Error: No qBittorrent plugins found.")
                settings["use_qb_plugins"] = False
            else:
                settings["use_qb_plugins"] = result["use_qb_plugins"]

        elif answer == "Categories":
            result = prompt([
                {
                    "type": "checkbox",
                    "name": "categories",
                    "message": "Select categories:",
                    "choices": [
                        "Movies",
                        "TV Shows",
                        "Application",
                        "Games",
                        "Music",
                        "Other",
                    ],
                    "default": settings["categories"],
                }
            ])
            settings["categories"] = result["categories"]

        elif answer == "Sort by":
            result = prompt([
                {
                    "type": "list",
                    "name": "sort_by",
                    "message": "Sort results by:",
                    "choices": [
                        "Name",
                        "Size",
                        "Seeders",
                        "Source",
                    ],
                    "default": settings["sort_by"],
                }
            ])
            settings["sort_by"] = result["sort_by"]

        elif answer == "Sources":
            print("Available sources:", SOURCES, QB_SOURCE_LIST)
            result = prompt([
                {
                    "type": "checkbox",
                    "name": "sources",
                    "message": "Select sources:",
                    "choices": QB_SOURCE_LIST if settings["use_qb_plugins"] else BASE_SOURCE_LIST,
                    "default": settings["sources"],
                }
            ])
            settings["sources"] = result["sources"]

        elif answer == "Back":
            return


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def main_menu():
    """
    Interactive main menu for the Ghidorah CLI.
    """
    settings = {
        "limit": 2,
        "total_limit": 10,
        "categories": [
            "Movies",
            "TV Shows",
            "Application",
            "Games",
            "Music",
            "Other",
        ],
        "sort_by": "Source",
        "sources": BASE_SOURCE_LIST,
        "use_qb_plugins": False,
    }

    while True:
        print_icon()

        answer = prompt([
            {
                "type": "list",
                "message": "Ghidorah v1.1",
                "name": "main_action",
                "choices": [
                    "Search",
                    "Check status",
                    "Settings",
                    Separator(),
                    "Exit",
                ],
            }
        ])["main_action"]

        if answer == "Search":
            print("Current settings:", settings)
            print(
                "\nIMPORTANT: if using qBittorrent plugins, the per torrent limit "
                "is ignored, and category selection is limited to one category only. "
                "Additionally, many plugins will default to \"all\".\n"
            )

            choice = input("Enter query:")
            results = run_search(choice, settings)

            rows = []
            for item in results["data"]:
                rows.append({
                    "name": truncate(item["name"], 20),
                    "size": format_size_bytes(item["size"]),
                    "seeders": item["seeders"],
                    "leechers": item["leechers"],
                    "category": item["category"],
                    "source": item["source"],
                    "url": truncate(item["url"], 15),
                    "date": item["date"],
                    "hash": truncate(item["hash"], 20),
                    "magnet": truncate(item["magnet"], 20),
                })

            print(
                tabulate(
                    rows[:settings["total_limit"]],
                    headers="keys",
                    tablefmt="grid",
                )
            )

            with open("results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)

            print(colored("Results saved to JSON file 'results.json'", "green"))

        elif answer == "Check status":
            check_status()

        elif answer == "Settings":
            settings_menu(settings)

        elif answer == "Exit":
            exit_app()


# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli_entry()
    else:
        main_menu()

