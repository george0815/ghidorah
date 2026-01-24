import requests
from bs4 import BeautifulSoup


class YTS:
    """
    Scraper for YTS movie torrent listings.

    Iterates through multiple YTS mirror domains, attempting to retrieve
    and parse movie results until valid data is found or all mirrors fail.
    """

    # ---------------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------------

    def __init__(self, settings):
        """
        Initialize the YTS source with runtime settings.

        Args:
            settings: Dictionary containing runtime configuration, including
                      result limits and category filters.
        """
        self.urls = [
            "https://yts.do",
            "https://yts.lt",
            "https://yts.ag",
            "https://yts.am",
            "https://yts.rs",
        ]
        self.LIMIT = settings["limit"]
        self.settings = settings

    # ---------------------------------------------------------------------
    # Search implementation
    # ---------------------------------------------------------------------

    def search(self, query) -> dict:
        """
        Perform a search against YTS mirror sites.

        Tries each configured YTS domain in order, stopping once valid
        results are found. Only HTTP 200 responses are parsed.

        Args:
            query: Search query string.

        Returns:
            A dictionary with a single key:
                - "data": List of result items.
        """

        # Accumulated search results
        result = {"data": []}

        # Try each YTS mirror until valid data is found
        for url in self.urls:

            finalUrl = f"{url}/browse-movies/{query}/all/all/0/0/latest"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }

            # Perform HTTP request
            res = requests.get(finalUrl, headers=headers, timeout=15)
            print(f"URL: {finalUrl} STATUS: {res.status_code}")

            # Skip mirrors that do not respond successfully
            if res.status_code != 200:
                continue

            self.soup = BeautifulSoup(res.content, "html.parser")

            # Parse movie result blocks
            for div in self.soup.find_all("div", class_="browse-movie-wrap"):
                torUrl = div.find("a")["href"]

                # Only include movie results if Movies category is enabled
                if "Movies" in self.settings["categories"]:
                    result["data"].append({
                        "url": torUrl,
                        "category": "Movies",
                    })

                # Stop once per-source limit is reached
                if len(result["data"]) == self.LIMIT:
                    break

            # Stop checking mirrors once results are found
            if len(result["data"]) > 0:
                break

        return result
