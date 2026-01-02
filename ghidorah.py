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
from termcolor import colored






# -------------------
# Helper functions
# -------------------z

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
        for source in [KickAssTorrents, ThePirateBay, LimeTorrents, YTS, X1337, TorrentGalaxy]:
            instance = source(settings["limit"] )
            result = instance.search("test")
            if len(result["data"]) > 0:
                print(f"{source.__name__}: {Fore.GREEN}ONLINE{Fore.RESET} - {len(result['data'])} results found")
            else:
                print(f"{source.__name__}: {Fore.RED}OFFLINE{Fore.RESET} - No results found")
    except Exception as e:
        print(f"An error occurred while checking status: {e}")



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
                    "default": settings["limit"],
                    "min_allowed": 1,
                }
            ])
            settings["limit"] = result["limit"]

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
                        "Date",
                        "Name",
                        "Size",
                        "Seeders",
                        "Leechers",
                    ],
                    "default": settings["sort_by"],
                }
            ])
            settings["sort_by"] = result["sort_by"]

        elif answer == "Sources":
            result = prompt([
                {
                    "type": "checkbox",
                    "name": "sources",
                    "message": "Select sources:",
                    "choices": [
                        "kickasstorrents", 
                        "thepiratebay", 
                        "limetorrents", 
                        "yts", 
                        "x1337", 
                        "torrentgalaxy"
                    ],
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
        "limit": 10,
        "categories": [],
        "sort_by": "Date",
        "sources": ["kickasstorrents", "thepiratebay", "limetorrents", "yts", "x1337", "torrentgalaxy"],
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

            tpb = LimeTorrents(settings["limit"])
            results = tpb.search(choice)
            rows = []
            for item in results["data"]:
                rows.append({
                    "name": truncate(item["name"], 20),
                    "size": item["size"],
                    "seeders": item["seeders"],
                    "leechers": item["leechers"],
                    "category": item["category"],
                    "url": truncate(item["url"], 15),
                    "date": item["date"],
                    #"hash": truncate(item["hash"], 20),
                    #"magnet": truncate(item["magnet"], 20),
                })

            print(tabulate(rows, headers="keys", tablefmt="grid"))

        elif answer == "Check status":
            check_status(settings)

        elif answer == "Settings":
            settings_menu(settings)

        elif answer == "Exit":
            exit_app()


if __name__ == "__main__":
    main_menu()

