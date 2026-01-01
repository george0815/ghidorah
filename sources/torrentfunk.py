import requests
import re
from bs4 import BeautifulSoup

class TorrentFunk:


    #Mainly just initializes the urls to be used for searching
    def __init__(self):
        
        self.urls = ["https://www.torrentfunk.com"]


    def search(self, query) -> dict:
        
        #status check to be implemented
        self.check_status(self.urls)
       
        #for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        my_dict = {"data": []}
        list_of_urls = []
        for url in self.urls:
            
            finalUrl = url + "/all/torrents/{}/{}.html".format(query, "1")
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
            for tr in soup.select(".tmain tr")[idx:]:
                    td = tr.find_all("td")
                    if len(td) == 0:
                        continue
                    name = td[0].find("a").text
                    date = td[1].text
                    size = td[2].text
                    seeders = td[3].text
                    leechers = td[4].text
                    uploader = td[5].text
                    url = self.BASE_URL + td[0].find("a")["href"]
                    list_of_urls.append(url)
                    my_dict["data"].append(
                        {
                            "name": name,
                            "size": size,
                            "date": date,
                            "seeders": seeders,
                            "leechers": leechers,
                            "uploader": uploader if uploader else None,
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



