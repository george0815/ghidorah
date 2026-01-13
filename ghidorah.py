from InquirerPy import prompt
from InquirerPy.separator import Separator
from sources.thepiratebay import ThePirateBay
from sources.kickasstorrents import KickAssTorrents
from sources.limetorrents import LimeTorrents
from sources.yts import YTS
from sources.x1337 import X1337
from sources.torrentgalaxy import TorrentGalaxy
from tabulate import tabulate
from colorama import Fore, init
import contextlib
import os
from termcolor import colored
import json
import argparse
import sys
from qb_env.ghidorah_qb import detect_qb_plugins, run_qb_plugin



sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")





# -------------------
# Helper functions
# -------------------

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
print("QB SOURCE LIST:", QB_SOURCE_LIST)    

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
                    normalized_item = normalize_result(item, source_name)
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


def parse_size(size):
    if not size or size == "N/A":
        return 0
    
    size = size.upper().strip()
    number, unit = size.split()[:2]
    number = float(number)

    multipliers = {
        "KiB": 1,
        "MiB": 1024,
        "GiB": 1024 ** 2,
        "TiB": 1024 ** 3,
        "kb": 1,
        "mb": 1024,
        "gb": 1024 ** 2,
        "tb": 1024 ** 3,
        "KB": 1,
        "MB": 1024,
        "GB": 1024 ** 2,
        "TB": 1024 ** 3,
    }

    return number * multipliers.get(unit, 0)
    




def normalize_result(item, source_name):
    normalized = NORMALIZED_FIELDS.copy()
    for key in normalized:
        if key in item and item[key] not in [None, ""]:
            normalized[key] = item[key]
    normalized["source"] = source_name
    return normalized


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
                "message": "Ghidorah v1.0",
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
            choice = input("Enter query:")

            results = run_search(choice, settings)

            rows = []
            for item in results["data"]:
                rows.append({
                    "name": truncate(item["name"], 20),
                    "size": item["size"],
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
