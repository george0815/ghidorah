import requests
from bs4 import BeautifulSoup


class LimeTorrents:
    """
    Scraper for LimeTorrents torrent listings.

    Searches across multiple LimeTorrents mirror domains and paginates
    results until the configured limit is reached.
    """

    # ---------------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------------

    def __init__(self, settings):
        """
        Initialize the LimeTorrents source with runtime settings.

        Args:
            settings: Dictionary containing runtime configuration such as
                      result limits and category filters.
        """
        self.urls = [
            "https://www.limetorrents.cc",
            "https://limetorrents.torrentbay.st",
            "https://limetorrents.ninjaproxy1.com",
            "https://limetorrents.piratic.org",
            "https://limetorrents.torrentsbay.org",
        ]
        self.LIMIT = settings["limit"]
        self.settings = settings
        self.starting_page = 1

    # ---------------------------------------------------------------------
    # Search implementation
    # ---------------------------------------------------------------------

    def search(self, query) -> dict:
        """
        Perform a search against LimeTorrents mirror sites.

        Iterates through known mirrors and paginates results until the
        configured result limit is reached.

        Args:
            query: Search query string.

        Returns:
            A dictionary with a single key:
                - "data": List of parsed torrent result items.
        """

        # Accumulated search results
        result = {"data": []}

        # Try each LimeTorrents mirror
        for url in self.urls:
            finalUrl = f"{url}/search/all/{query}//{self.starting_page}"

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

            # Parse table rows
            for table_row in self.soup.find_all("tr")[0:]:
                row_data = table_row.find_all("td")
                if len(row_data) == 0:
                    continue

                # Extract torrent metadata
                name = row_data[0].get_text(strip=True)
                torUrl = url + row_data[0].find_all("a")[-1]["href"]

                added_on_and_category = row_data[1].get_text(strip=True)
                date = (added_on_and_category.split("-")[0]).strip()
                category = (added_on_and_category.split("in")[-1]).strip()

                size = row_data[2].text
                seeders = row_data[3].text

                leechers = "N/A"
                if len(row_data) > 4:
                    leechers = row_data[4].text

                # Filter by enabled categories
                if (
                    category in self.settings["categories"]
                    or (
                        category == "Other"
                        and "Other" in self.settings["categories"]
                    )
                ):
                    result["data"].append(
                        {
                            "name": name,
                            "size": size,
                            "date": date,
                            "category": category if category != date else None,
                            "seeders": seeders,
                            "leechers": leechers,
                            "url": torUrl,
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
