import requests
import re
from bs4 import BeautifulSoup


class ThePirateBay:
    """
    Scraper for The Pirate Bay torrent listings.

    Searches across multiple TPB mirror domains and paginates results
    until the configured limit is reached or no more data is available.
    """

    # ---------------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------------

    def __init__(self, settings):
        """
        Initialize the Pirate Bay source with runtime settings.

        Args:
            settings: Dictionary containing runtime configuration such as
                      result limits and category filters.
        """
        self.urls = [
            "https://thepiratebay10.org",
            "https://tpb.party",
            "https://pirateproxylive.org",
            "https://thepiratebay11.com",
            "https://thepiratebay.zone",
        ]
        self.LIMIT = settings["limit"]
        self.settings = settings
        self.starting_page = 1

    # ---------------------------------------------------------------------
    # Search implementation
    # ---------------------------------------------------------------------

    def search(self, query) -> dict:
        """
        Perform a search against The Pirate Bay mirror sites.

        Iterates through mirror URLs and paginates results until the
        configured result limit is reached.

        Args:
            query: Search query string.

        Returns:
            A dictionary with a single key:
                - "data": List of parsed torrent result items.
        """

        # Accumulated search results
        result = {"data": []}

        # Try each TPB mirror
        for url in self.urls:

            finalUrl = f"{url}/search/{query}/{self.starting_page}/99/0"

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

            # Parse table rows (skip header row)
            for table_row in self.soup.find_all("tr")[1:]:
                row_data = table_row.find_all("td")

                # Extract torrent name
                try:
                    name = row_data[1].find("a").text
                except Exception:
                    name = None

                # Parse torrent details if a name is present
                if name:
                    url = row_data[1].find("a")["href"]
                    magnet = row_data[3].find_all("a")[0]["href"]
                    size = row_data[4].text.strip()
                    seeders = row_data[5].text
                    leechers = row_data[6].text
                    category = row_data[0].find_all("a")[0].text
                    uploader = row_data[7].text
                    dateUploaded = row_data[2].text

                    # Check if torrent category matches user settings
                    cat_check = False
                    for cat in self.settings["categories"]:
                        if cat.lower() in category.lower():
                            cat_check = True

                    if cat_check:
                        result["data"].append(
                            {
                                "name": name,
                                "size": size,
                                "seeders": seeders,
                                "leechers": leechers,
                                "category": category,
                                "uploader": uploader,
                                "url": url,
                                "date": dateUploaded,
                                "hash": re.search(
                                    r"([{a-f\d,A-F\d}]{32,40})\b",
                                    magnet,
                                ).group(0),
                                "magnet": magnet,
                            }
                        )

                # Stop once per-source limit is reached
                if len(result["data"]) == self.LIMIT:
                    break

            # Stop checking mirrors once results are found
            if len(result["data"]) > 0:
                break

        # If limit not reached, paginate to next page recursively
        if len(result["data"]) != self.LIMIT:
            self.starting_page += 1
            more_results = self.search(query)
            result["data"].extend(more_results["data"])

        #if 10 pages are searched, cut loses and just return results
        elif self.starting_page == 10:
            return result

        return result
