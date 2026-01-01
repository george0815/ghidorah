from InquirerPy import prompt
from InquirerPy.separator import Separator
from sources.thepiratebay import ThePirateBay
from sources.kickasstorrents import KickAssTorrents
from sources.limetorrents import LimeTorrents
from sources.yts import YTS
from sources.x1337 import X1337
from sources.torrentgalaxy import TorrentGalaxy
from tabulate import tabulate

# -------------------
# Helper functions
# -------------------

def truncate(text, length=40):
    return text if len(text) <= length else text[:length - 3] + "..."

# -------------------
# Stub functions
# -------------------

def check_status():
    print("Checking status...")
    input("Press Enter to return to main menu")


def exit_app():
    print("Exiting application...")
    raise SystemExit


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
                        "News",
                        "Technology",
                        "Sports",
                        "Finance",
                        "Entertainment",
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
                        "Relevance",
                        "Date",
                        "Popularity",
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
                        "Google",
                        "Bing",
                        "DuckDuckGo",
                        "Reddit",
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
        "sources": [],
    }

    while True:
        answer = prompt([
            {
                "type": "list",
                "name": "main_action",
                "message": "Main Menu",
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

            tpb = KickAssTorrents(settings["limit"])
            results = tpb.search(choice)
            rows = []
            for item in results["data"]:
                rows.append({
                    "name": truncate(item["name"], 20),
                    "size": item["size"],
                    "seeders": item["seeders"],
                    "leechers": item["leechers"],
                    #"category": item["category"],
                    "url": truncate(item["url"], 15),
                    "date": item["date"],
                    #"hash": truncate(item["hash"], 20),
                    #"magnet": truncate(item["magnet"], 20),
                })

            print(tabulate(rows, headers="keys", tablefmt="grid"))

        elif answer == "Check status":
            check_status()

        elif answer == "Settings":
            settings_menu(settings)

        elif answer == "Exit":
            exit_app()


if __name__ == "__main__":
    main_menu()

