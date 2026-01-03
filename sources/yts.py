import requests
import re
from bs4 import BeautifulSoup

class YTS:

    # Mainly just initializes the urls to be used for searching
    def __init__(self, settings):
        self.urls = [
            "https://yts.do",
            "https://yts.lt",
            "https://yts.ag",
            "https://yts.am",
            "https://yts.rs"]
        self.LIMIT = settings["limit"]
        self.settings = settings

    def search(self, query) -> dict:


        # for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        result = {"data": []}
        for url in self.urls:

            finalUrl = url + "/browse-movies/{}/all/all/0/0/latest".format(query)

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

            # actually parse the data
            for div in self.soup.find_all("div", class_="browse-movie-wrap"):
                torUrl = div.find("a")["href"]

                if "Movies" in self.settings["categories"]:
                    result["data"].append({"url": torUrl,
                                           "category": "Movies"})
                    
                if len(result["data"]) == self.LIMIT:
                    break

            if len(result["data"]) > 0:
                break

        return result
