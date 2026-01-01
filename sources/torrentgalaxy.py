import requests
import re
from bs4 import BeautifulSoup

class TorrentGalaxy:


    #Mainly just initializes the urls to be used for searching
    def __init__(self):
        
        self.urls = ["https://torrentgalaxy.one"]
        self.LIMIT = 50


    def search(self, query) -> dict:
        
        #status check to be implemented
        self.check_status(self.urls)
       
        #for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        my_dict = {"data": []}
        for url in self.urls:
            
            finalUrl = url + "/get-posts/keywords:{}".format(query)
            print("FINAL URL:", finalUrl)

            headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
            }       

            #response
            res = requests.get(finalUrl, headers=headers, timeout=15)
            print("STATUS:", res.status_code)
            print(res.text)  
            if res.status_code != 200:
                continue
            self.soup = BeautifulSoup(res.content, "html.parser")

          
            #actually parse the data, find the table rows ("[1:]" skips header row)
            for idx, divs in enumerate(self.soup.find_all("div", class_="tgxtablerow")):
                div = divs.find_all("div")
                try:
                    name = div[4].find("a").get_text(strip=True)
                    imdb_url = (div[4].find_all("a"))[-1]["href"]
                except:
                    name = (div[1].find("a", class_="txlight")).find("b").text
                    imdb_url = (div[1].find_all("a"))[-1]["href"]

                if name != "":
                    try:
                        magnet = div[5].find_all("a")[1]["href"]
                        torrent = div[5].find_all("a")[0]["href"]
                    except:
                        magnet = div[3].find_all("a")[1]["href"]
                        torrent = div[3].find_all("a")[0]["href"]
                    size = self.soup.select("span.badge.badge-secondary.txlight")[
                        idx
                    ].text
                    try:
                        torUrl = div[4].find("a")["href"]
                    except:
                        torUrl = div[1].find("a", class_="txlight")["href"]
                    try:
                        date = div[12].get_text(strip=True)
                    except:
                        date = div[10].get_text(strip=True)
                    try:
                        seeders_leechers = div[11].find_all("b")
                        seeders = seeders_leechers[0].text
                        leechers = seeders_leechers[1].text
                    except:
                        seeders_leechers = div[11].find_all("b")
                        seeders = seeders_leechers[0].text
                        leechers = seeders_leechers[1].text
                    try:
                        uploader = (div[7].find("a")).find("span").text
                    except:
                        uploader = (div[5].find("a")).find("span").text
                    try:
                        category = (
                            div[0].find("small").text.replace("&nbsp", "")
                        ).split(":")[0]
                    except:
                        category = None
                    my_dict["data"].append(
                        {
                            "name": name,
                            "size": size,
                            "seeders": seeders,
                            "leechers": leechers,
                            "category": category,
                            "uploader": uploader,
                            "imdb_id": imdb_url.split("=")[-1],
                            
                            "magnet": magnet,
                            "torrent": torrent,
                            "url": url + torUrl,
                            "date": date,
                        }
                    )
                if len(my_dict["data"]) == self.LIMIT:
                    break
            try:
                ul = self.soup.find_all("ul", class_="pagination")[-1]
                tpages = ul.find_all("li")[-2]
                my_dict["current_page"] = int(
                    self.soup.select_one("li.page-item.active.txlight a").text.split(
                        " "
                    )[0]
                )
                my_dict["total_pages"] = int(tpages.find("a").text)
            except:
                my_dict["current_page"] = None
                my_dict["total_pages"] = None
                # ...
            
        return my_dict


    def check_status(self, urls) -> bool:
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                continue
        return False



