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
from colorama import Fore, init
import contextlib
import os
from datetime import datetime
from termcolor import colored
import json
import re
import argparse
import sys


RUNTIME_ROOT = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)

QB_ENV_DIR = os.path.join(RUNTIME_ROOT, "qb_env")
if QB_ENV_DIR not in sys.path:
    sys.path.insert(0, QB_ENV_DIR)

    
from qb_env.ghidorah_qb import detect_qb_plugins, run_qb_plugin



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
    return value in (None, "", -1)

def safe_int(value, default=0):
    try:
        if qb_missing(value):
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_date(unix_ts):
    try:
        if qb_missing(unix_ts):
            return "N/A"
        return datetime.fromtimestamp(int(unix_ts)).strftime("%m/%d/%Y")
    except (ValueError, TypeError, OSError):
        return "N/A"

SOURCE_REGISTRY = {
    "kickasstorrents": KickAssTorrents,
    "thepiratebay": ThePirateBay,
    "limetorrents": LimeTorrents,
    "yts": YTS,
    "x1337": X1337,
    "torrentgalaxy": TorrentGalaxy,
  
}


BASE_SOURCE_LIST = ["kickasstorrents", 
                        "thepiratebay", 
                        "limetorrents", 
                        "yts", 
                        "x1337", 
                        "torrentgalaxy"]


engines = detect_qb_plugins()



QB_SOURCE_LIST = engines.keys()

SOURCES = list(QB_SOURCE_LIST) + list(BASE_SOURCE_LIST)


SORT_MAP = {

    "Name": {
        "key": lambda x: x["name"].lower(),
        "reverse": False
    },
    "Size": {
        "key": lambda x: x["size"],
        "reverse": True
    },
    "Seeders": {
        "key": lambda x: int(x["seeders"]) if str(x["seeders"]).isdigit() else 0,
        "reverse": True
    },
    "Source": {
        "key": lambda x: x["source"].lower(),
        "reverse": False
    }

}

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



@contextlib.contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

def run_search(query, settings):
    results = {
        "data": [],
        "errors": []
    }

    if settings["use_qb_plugins"] == False:
        
        for source_name in settings["sources"]:
            source_class = SOURCE_REGISTRY.get(source_name)
    
            if not source_class:
                continue
    
            try:
                instance = source_class(settings)
                response = instance.search(query)
    
                for item in response.get("data", []):
                    normalized_item = normalize_result(item, source_name, settings["use_qb_plugins"])
                    results["data"].append(normalized_item)
    
            except Exception as e:
                results["errors"].append(f"Error with {source_name}: {e}")
    
    
        sort_config = SORT_MAP.get(settings["sort_by"])
        if sort_config:
            results["data"].sort(
                key=sort_config["key"],
                reverse=sort_config["reverse"]
            )

    else:

        for source_name in settings["sources"]:
            if source_name not in engines:
                continue

            try:
                source_path = engines[source_name].__module__
                source_file = engines[source_name].__class__.__module__
                norm_cat = normalize_category(settings["categories"][0])
                cat = norm_cat if norm_cat in getattr(engines[source_name], "supported_categories", {"all": ""}) else "all"
                plugin_results = run_qb_plugin(source_name, query, cat)

                for item in plugin_results:
                    normalized_item = normalize_result(item, source_name, settings["use_qb_plugins"])
                    results["data"].append(normalized_item)

            except Exception as e:
                results["errors"].append(f"Error with {source_name}: {e}")

            sort_config = SORT_MAP.get(settings["sort_by"])
            if sort_config:
                results["data"].sort(
                    key=sort_config["key"],
                    reverse=sort_config["reverse"]
                )

        pass

    return results


def cli_entry():
 
    parser = argparse.ArgumentParser(description="Ghidorah Torrent Search CLI")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--limit", type=int, default=2, help="Number of results per source")
    parser.add_argument("--total_limit", type=int, default=10, help="Total number of results to display")
    parser.add_argument("--categories", type=str, nargs='+', default=["Movies",
                                                                    "TV Shows",
                                                                    "Application",
                                                                    "Games",
                                                                    "Music",
                                                                    "Other"], help="Categories to search in")
    parser.add_argument("--sort_by", type=str, choices=["Name", "Size", "Seeders", "Source"], default="Source", help="Sort results by")
    parser.add_argument("--sources", type=str, nargs='+', choices=SOURCES, default=SOURCES, help="Sources to search from")

    parser.add_argument("--use_qb_plugins", action="store_true", help="Enable qBittorrent plugins")

    args = parser.parse_args()

    settings = {
        "limit": args.limit,
        "total_limit": args.total_limit,
        "categories": args.categories,
        "sort_by": args.sort_by,
        "use_qb_plugins": args.use_qb_plugins,
        "sources": args.sources,
    }


    try:
        with suppress_stdout():
            if not args.use_qb_plugins:
                settings["sources"] = set(BASE_SOURCE_LIST) & set(args.sources)
            else: #revise this later 
                settings["sources"] = set(QB_SOURCE_LIST) & set(args.sources)

            results = run_search(args.query, settings)

    


        print(json.dumps(results, ensure_ascii=False))
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
      

  
def print_icon():
    print(colored("""⠈⠉⠛⣶⣶⣶⣦⣤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⣤⣶⣶⣶⡟⠋⠁
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
⠀⠀⠀⠀⠀⠀""", 'red'))


def check_status(settings):

    print_path_debug()
    print("Checking status...")

    try:
        
        
        if settings["use_qb_plugins"] == False:
            for source in [KickAssTorrents, ThePirateBay, LimeTorrents, YTS, X1337, TorrentGalaxy]:
                instance = source(settings)
                result = instance.search("test")
                if len(result["data"]) > 0:
                    print(f"{source.__name__}: {Fore.GREEN}ONLINE{Fore.RESET} - {len(result['data'])} results found")
                else:
                    print(f"{source.__name__}: {Fore.RED}OFFLINE{Fore.RESET} - No results found")
                    
        else:
            #TODO: fill this in
            pass
            
    except Exception as e:
        print(f"An error occurred while checking status: {e}")


import re

_SIZE_RE = re.compile(
    r"(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>kib|kb|mib|mb|gib|gb|tib|tb|b)?",
    re.IGNORECASE,
)

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


def parse_size(size) -> int:
    """
    Parse human-readable size into bytes.
    Always returns an int. Never raises.
    """

    # Already numeric → assume bytes
    if isinstance(size, (int, float)):
        return int(size)

    if not size or size in ("N/A", "-1"):
        return 0

    s = str(size).lower().strip()

    # Handle ranges like "7.9~8.5", "7.9 - 8.5 gb"
    if "~" in s or "-" in s:
        parts = re.split(r"[~-]", s)
        for part in reversed(parts):  # prefer upper bound
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
    Format a byte count into a human-readable string (binary units).
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




def normalize_result(item, source_name, qb):

    if qb == False:
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
            "hash": "N/A",  # qB plugins never provide this
            "magnet": item.get("link") if not qb_missing(item.get("link")) else "N/A"
        }


def exit_app():
    print("Exiting application...")
    raise SystemExit

def truncate(text, length=40):
    return text if len(text) <= length else text[:length - 3] + "..."


# -------------------
# Settings menu
# -------------------

def settings_menu(settings):
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
                    "Back"
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
            if result["limit"] is not None:
                settings["limit"] = int(result["limit"])

            else:
                settings["limit"] = 2

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
            if result["total_limit"] is not None:
                settings["total_limit"] = int(result["total_limit"])

            else:
                settings["total_limit"] = 10

        elif answer == "Use qBittorrent plugins":
            result = prompt([
                {
                    "type": "confirm",
                    "name": "use_qb_plugins",
                    "message": "Enable qBittorrent plugins?",
                    "default": settings.get("use_qb_plugins", False),
                }
            ])
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
                        "Other"
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
                    "choices": QB_SOURCE_LIST if settings["use_qb_plugins"] else BASE_SOURCE_LIST ,
                    "default": settings["sources"],
                }
            ])
            settings["sources"] = result["sources"]

        elif answer == "Back":
            return


# -------------------
# Main menu
# -------------------

def main_menu():
    
    settings = {
        "limit": 2,
        "total_limit": 10,
        "categories": ["Movies",
                        "TV Shows",
                        "Application",
                        "Games",
                        "Music",
                        "Other"],
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
            print("\nIMPORTANT: if using qBittorrent plugins, the per torrent limit is ignored, and category selection is limited to one category only. Addionally, many plugins will default to \"all\". \n")
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


            
                
            print(tabulate(rows[:settings["total_limit"]], headers="keys", tablefmt="grid"))

            with open("results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)

            print(colored("Results saved to JSON file 'results.json'", 'green'))

        elif answer == "Check status":
            check_status(settings)

        elif answer == "Settings":
            settings_menu(settings)

        elif answer == "Exit":
            exit_app()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli_entry() 
    else:
        main_menu()
