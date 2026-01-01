import requests
from bs4 import BeautifulSoup

class LimeTorrents:

    # Mainly just initializes the urls to be used for searching
    def __init__(self):
        self.urls = [
            "https://www.limetorrents.cc",
            "https://limetorrents.torrentbay.st",
            "https://limetorrents.ninjaproxy1.com",
            "https://limetorrents.piratic.org",
            "https://limetorrents.torrentsbay.org"]
        self.LIMIT = 50

    def search(self, query) -> dict:

        # for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        result = {"data": []}

        for url in self.urls:
            finalUrl = url + "/search/all/{}//1".format(query)
            print("FINAL URL:", finalUrl)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }

            # response
            res = requests.get(finalUrl, headers=headers, timeout=15)
            print("STATUS:", res.status_code)
            if res.status_code != 200:
                continue

            self.soup = BeautifulSoup(res.content, "html.parser")

            # actually parse the data, find the table rows
            for table_row in self.soup.find_all("tr")[0:]:
                row_data = table_row.find_all("td")
                if len(row_data) == 0:
                    continue

                name = row_data[0].get_text(strip=True)
                torUrl = url + row_data[0].find_all("a")[-1]["href"]

                added_on_and_category = row_data[1].get_text(strip=True)
                date = (added_on_and_category.split("-")[0]).strip()
                category = (added_on_and_category.split("in")[-1]).strip()

                size = row_data[2].text
                seeders = row_data[3].text
                # leechers = row_data[4].text

                result["data"].append(
                    {
                        "name": name,
                        "size": size,
                        "date": date,
                        "category": category if category != date else None,
                        "seeders": seeders,
                        # "leechers": leechers,
                        "url": torUrl,
                    }
                )

                if len(result["data"]) == self.LIMIT:
                    break

            print(len(result["data"]))
            if len(result["data"]) > 0:
                break        

        return result
