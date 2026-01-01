import requests
import re
from bs4 import BeautifulSoup, soup

class Torlock:


    #Mainly just initializes the urls to be used for searching
    def __init__(self):
        
        self.urls = ["https://www.torlock.com"]


    def search(self, query) -> dict:
        
        #status check to be implemented
        self.check_status(self.urls)
       
        #for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        my_dict = {"data": []}
        list_of_urls = []
        for url in self.urls:
            
            finalUrl = url + "/all/torrents/{}.html?sort=seeds&page={}".format(query, "1")
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
            for tr in self.soup.find_all("tr")[0:]:
                td = tr.find_all("td")
                if len(td) == 0:
                    continue
                name = td[0].get_text(strip=True)
                if name != "":
                    url = td[0].find("a")["href"]
                    if url == "":
                        break
                    url = self.BASE_URL + url
                    list_of_urls.append(url)
                    size = td[2].get_text(strip=True)
                    date = td[1].get_text(strip=True)
                    seeders = td[3].get_text(strip=True)
                    leechers = td[4].get_text(strip=True)
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
            try:
                ul = soup.find("ul", class_="pagination")
                tpages = ul.find_all("a")[-2].text
                current_page = (
                    (ul.find("li", class_="active")).find("span").text.split(" ")[0]
                )
                my_dict["current_page"] = int(current_page)
                my_dict["total_pages"] = int(tpages)
            except:
                my_dict["current_page"] = None
                my_dict["total_pages"] = None
            
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



