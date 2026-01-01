import requests
from bs4 import BeautifulSoup

class KickAssTorrents:

    # Mainly just initializes the urls to be used for searching
    def __init__(self, limit):
        self.urls = [
            "https://kickasstorrents.id",
            "https://kickasstorrents.to",
            "https://kickasshydra.net",
            "https://kick4ss.com",
            "https://kickass.torrentsbay.org",
        ]
        self.LIMIT = limit
        self.session = requests.Session()

    def search(self, query) -> dict:

        # for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        result = {"data": []}
        for url in self.urls:

            finalUrl = url + "/usearch/{}/1/".format(query)
            print("FINAL URL:", finalUrl)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }

            # response
            self.session.headers.update(headers)
            res = self.session.get(finalUrl, timeout=15)
            print("STATUS:", res.status_code)
            if res.status_code != 200:
                continue

            self.soup = BeautifulSoup(res.content, "html.parser")

            # actually parse the data, find the table rows
            for table_row in self.soup.select("tr.odd,tr.even"):
                row_data = table_row.find_all("td")

                name = table_row.find("a", class_="cellMainLink").text.strip()
                torUrl = url + table_row.find("a", class_="cellMainLink")["href"]

                if name:
                    size = row_data[1].text.strip()
                    seeders = row_data[4].text.strip()
                    leechers = row_data[3].text.strip()
                    date = row_data[2].text.strip()

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

                if len(result["data"]) == self.LIMIT:
                    break

            print(len(result["data"]))
            if len(result["data"]) > 0:
                break


        return result
