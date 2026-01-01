import requests
import re
from bs4 import BeautifulSoup

class TorrentProject:


    #Mainly just initializes the urls to be used for searching
    def __init__(self):
        
        self.urls = ["https://torrentproject.cc"]


    def search(self, query) -> dict:
        
        #status check to be implemented
        self.check_status(self.urls)
       
        #for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        my_dict = {"data": []}
        list_of_urls = []
        for url in self.urls:
            
            finalUrl = url + "/?t={}&p={}".format(query, "0")
            print("FINAL URL:", finalUrl)

            headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
            }       

            #response
            res = requests.get(finalUrl, headers=headers, timeout=15)
            print("STATUS:", res.status_code)  
            if res.status_code != 200:
                continue
            self.soup = BeautifulSoup(res.content, "html.parser")

          
            #actually parse the data, find the table rows ("[1:]" skips header row)
            for div in soup.select("div#similarfiles div")[2:]:
                span = div.find_all("span")
                name = span[0].find("a").text
                url = self.BASE_URL + span[0].find("a")["href"]
                list_of_urls.append(url)
                seeders = span[2].text
                leechers = span[3].text
                date = span[4].text
                size = span[5].text

                my_dict["data"].append(
                    {
                        "name": name,
                        "size": size,
                        "date": date,
                        "seeders": seeders,
                        "leechers": leechers,
                        "url": url,
                    }
                )
                if len(my_dict["data"]) == self.LIMIT:
                    break
            
        return my_dict, list_of_urls


    def check_status(self, urls) -> bool:
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                continue
        return False



