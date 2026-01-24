import requests
from bs4 import BeautifulSoup


class X1337:
    """
    Scraper for 1337x torrent listings.

    Attempts to search multiple 1337x mirror domains, parsing results
    from the first mirror that successfully returns data.
    """

    # ---------------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------------

    def __init__(self, settings):
        """
        Initialize the 1337x source with runtime settings.

        Args:
            settings: Dictionary containing runtime configuration such as
                      result limits and category filters.
        """
        self.urls = [
            "https://1337x.pro",
            "https://1337x.st",
            "https://www.1377x.is",
            "https://1337x.proxyninja.net/",
            "https://1337x.unblockninja.com",
        ]
        self.LIMIT = settings["limit"]
        self.settings = settings

    # ---------------------------------------------------------------------
    # Search implementation
    # ---------------------------------------------------------------------

    def search(self, query) -> dict:
        """
        Perform a search against 1337x mirror sites.

        Iterates through known mirrors, stopping once valid results
        are retrieved or all mirrors have been exhausted.

        Args:
            query: Search query string.

        Returns:
            A dictionary with a single key:
                - "data": List of parsed torrent result items.
        """

        # Accumulated search results
        result = {"data": []}

        # Track which mirror URLs returned usable results
        list_of_urls = []

        # Try each mirror URL
        for url in self.urls:
            finalUrl = f"{url}/search/?q={query}"

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

            # Parse torrent rows from the results table
            table_rows = self.soup.select("tbody tr")
            for tr in table_rows:
                row_data = tr.find_all("td")
                name = row_data[0].find_all("a")[-1].text

                if name:
                    list_of_urls.append(url)

                    seeders = row_data[1].text
                    leechers = row_data[2].text
                    date = row_data[3].text
                    size = row_data[4].text.replace(seeders, "")

                    # Only include results if "Other" category is enabled
                    if "Other" in self.settings["categories"]:
                        result["data"].append(
                            {
                                "name": name,
                                "size": size,
                                "date": date,
                                "seeders": seeders,
                                "leechers": leechers,
                                "url": url,
                            }
                        )

                # Stop once per-source limit is reached
                if len(result["data"]) == self.LIMIT:
                    break

            # Stop checking mirrors once results are found
            if len(result["data"]) > 0:
                break

        return result
