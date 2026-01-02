import requests
import re
from bs4 import BeautifulSoup

class X1337:

    # Mainly just initializes the urls to be used for searching
    def __init__(self, limit):
        self.urls = [
            "https://1337x.pro",
            "https://1337x.st",
            "https://www.1377x.is",
            "https://1337x.proxyninja.net/",
            "https://1337x.unblockninja.com"]
        self.LIMIT = limit

    def search(self, query) -> dict:

        # for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        result = {"data": []}
        list_of_urls = []

        for url in self.urls:
            finalUrl = url + "/search/?q={}".format(query)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }

            # response
            res = requests.get(finalUrl, headers=headers, timeout=15)
            print("URL: {} STATUS: {}".format(finalUrl, res.status_code))
            if res.status_code != 200:
                continue

            self.soup = BeautifulSoup(res.content, "html.parser")

            # actually parse the data, find the table rows
            table_rows = self.soup.select("tbody tr")
            for tr in table_rows:
                row_data = tr.find_all("td")
                name = row_data[0].find_all("a")[-1].text

                if name:
                    torUrl = url + row_data[0].find_all("a")[-1]["href"]
                    list_of_urls.append(url)
                    seeders = row_data[1].text
                    leechers = row_data[2].text
                    date = row_data[3].text
                    size = row_data[4].text.replace(seeders, "")

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

                if len(result["data"]) == self.LIMIT:
                    break

            if len(result["data"]) > 0:
                break

        return result

