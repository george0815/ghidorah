import requests
from bs4 import BeautifulSoup


class TorrentGalaxy:
    """
    Scraper for TorrentGalaxy torrent listings.

    Attempts to search multiple TorrentGalaxy mirror domains, parsing
    results from the first mirror that successfully returns valid data.
    """

    # ---------------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------------

    def __init__(self, settings):
        """
        Initialize the TorrentGalaxy source with runtime settings.

        Args:
            settings: Dictionary containing runtime configuration such as
                      result limits and category filters.
        """
        self.urls = [
            "https://torrentgalaxy.io",
            "https://torrentgalaxy.inf",
            "https://torrentgalaxy.one",
        ]
        self.LIMIT = settings["limit"]
        self.settings = settings

    # ---------------------------------------------------------------------
    # Search implementation
    # ---------------------------------------------------------------------

    def search(self, query) -> dict:
        """
        Perform a search against TorrentGalaxy mirror sites.

        Iterates through known mirrors, stopping once valid results are
        retrieved or all mirrors have been exhausted.

        Args:
            query: Search query string.

        Returns:
            A dictionary with a single key:
                - "data": List of parsed torrent result items.
        """

        # Accumulated search results
        result = {"data": []}

        # Try each TorrentGalaxy mirror
        for url in self.urls:

            finalUrl = f"{url}/get-posts/keywords:{query}"

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

            # Parse each torrent row
            for idx, divs in enumerate(
                self.soup.find_all("div", class_="tgxtablerow")
            ):
                div = divs.find_all("div")

                # Extract torrent name (layout may vary)
                try:
                    name = div[4].find("a").get_text(strip=True)
                except Exception:
                    name = (
                        div[1]
                        .find("a", class_="txlight")
                        .find("b")
                        .text
                    )

                if name != "":
                    # Extract magnet and torrent links (layout may vary)
                    try:
                        magnet = div[5].find_all("a")[1]["href"]
                        torrent = div[5].find_all("a")[0]["href"]
                    except Exception:
                        magnet = div[3].find_all("a")[1]["href"]
                        torrent = div[3].find_all("a")[0]["href"]

                    # Extract file size (indexed by row position)
                    size = self.soup.select(
                        "span.badge.badge-secondary.txlight"
                    )[idx].text

                    # Extract torrent page URL
                    try:
                        torUrl = div[4].find("a")["href"]
                    except Exception:
                        torUrl = div[1].find(
                            "a", class_="txlight"
                        )["href"]

                    # Extract upload date
                    try:
                        date = div[12].get_text(strip=True)
                    except Exception:
                        date = div[10].get_text(strip=True)

                    # Extract seeders and leechers
                    try:
                        seeders_leechers = div[11].find_all("b")
                        seeders = seeders_leechers[0].text
                        leechers = seeders_leechers[1].text
                    except Exception:
                        seeders_leechers = div[11].find_all("b")
                        seeders = seeders_leechers[0].text
                        leechers = seeders_leechers[1].text

                    # Extract uploader name
                    try:
                        uploader = (
                            div[7].find("a").find("span").text
                        )
                    except Exception:
                        uploader = (
                            div[5].find("a").find("span").text
                        )

                    # Only include results if Movies category is enabled
                    if "Movies" in self.settings["categories"]:
                        result["data"].append(
                            {
                                "name": name,
                                "size": size,
                                "seeders": seeders,
                                "leechers": leechers,
                                "category": "Movies",
                                "uploader": uploader,
                                "magnet": magnet,
                                "torrent": torrent,
                                "url": url + torUrl,
                                "date": date,
                            }
                        )

                # Stop once per-source limit is reached
                if len(result["data"]) == self.LIMIT:
                    break

            # Stop checking mirrors once results are found
            if len(result["data"]) > 0:
                break

        return result
