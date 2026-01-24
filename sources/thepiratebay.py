import requests
import re
from bs4 import BeautifulSoup

class ThePirateBay:

    # Mainly just initializes the urls to be used for searching
    def __init__(self, settings):
        self.urls = [
            "https://thepiratebay10.org",
            "https://tpb.party",
            "https://pirateproxylive.org",
            "https://thepiratebay11.com",
            "https://thepiratebay.zone"
        ]
        self.LIMIT = settings["limit"]
        self.settings = settings
        self.starting_page = 1

    def search(self, query) -> dict:

        # for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        result = {"data": []}
        for url in self.urls:

            finalUrl = url + "/search/{}/{}/99/0".format(query, self.starting_page)

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
            for table_row in self.soup.find_all("tr")[1:]:
                row_data = table_row.find_all("td")
                try:
                    name = row_data[1].find("a").text
                    
                except Exception:
                    name = None


                # parse actual torrent data
                if name:
                    
                    url = row_data[1].find("a")["href"]
                    magnet = row_data[3].find_all("a")[0]["href"]
                    size = row_data[4].text.strip()
                    seeders = row_data[5].text
                    leechers = row_data[6].text
                    category = row_data[0].find_all("a")[0].text
                    uploader = row_data[7].text
                    dateUploaded = row_data[2].text

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
                                    r"([{a-f\d,A-F\d}]{32,40})\b", magnet
                                ).group(0),
                                "magnet": magnet,
                            }
                        )

                if len(result["data"]) == self.LIMIT:
                    break

           

       
            if len(result["data"]) > 0:
                break


        if len(result["data"]) != self.LIMIT:
            self.starting_page += 1
            more_results = self.search(query)
            result["data"].extend(more_results["data"])

        return result
