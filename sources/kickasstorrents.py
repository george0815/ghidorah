import requests
from bs4 import BeautifulSoup


class KickAssTorrents:
    """
    Scraper for KickAssTorrents listings.

    Searches across multiple KickAssTorrents mirror domains and paginates
    results until the configured limit is reached.
    """

    # ---------------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------------

    def __init__(self, settings):
        """
        Initialize the KickAssTorrents source with runtime settings.

        Args:
            settings: Dictionary containing runtime configuration such as
                      result limits and category filters.
        """
        self.urls = [
            "https://kickasstorrents.id",
            "https://kickasstorrents.to",
            "https://kickasshydra.net",
            "https://kick4ss.com",
            "https://kickass.torrentsbay.org",
        ]
        self.LIMIT = settings["limit"]
        self.settings = settings
        self.starting_page = 1

        # Reuse a session to preserve headers and improve request performance
        self.session = requests.Session()

    # ---------------------------------------------------------------------
    # Search implementation
    # ---------------------------------------------------------------------

    def search(self, query) -> dict:
        """
        Perform a search against KickAssTorrents mirror sites.

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

        # Try each KickAssTorrents mirror
        for url in self.urls:

            finalUrl = f"{url}/usearch/{query}/{self.starting_page}/"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }

            # Perform HTTP request using a persistent session
            self.session.headers.update(headers)
            res = self.session.get(finalUrl, timeout=15)
            print(f"URL: {finalUrl} STATUS: {res.status_code}")

            # Skip mirrors that do not respond successfully
            if res.status_code != 200:
                continue

            self.soup = BeautifulSoup(res.content, "html.parser")

            # Parse table rows containing torrent entries
            for table_row in self.soup.select("tr.odd,tr.even"):
                row_data = table_row.find_all("td")

                name = (
                    table_row
                    .find("a", class_="cellMainLink")
                    .text
                    .strip()
                )
                torUrl = (
                    url
                    + table_row
                    .find("a", class_="cellMainLink")["href"]
                )

                if name:
                    size = row_data[1].text.strip()
                    seeders = row_data[4].text.strip()
                    leechers = row_data[3].text.strip()
                    date = row_data[2].text.strip()

                    # Only include results if "Other" category is enabled
                    if "Other" in self.settings["categories"]:
                        result["data"].append(
                            {
                                "name": name,
                                "size": size,
                                "date": date,
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
