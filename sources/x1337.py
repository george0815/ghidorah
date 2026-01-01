import requests
import re
from bs4 import BeautifulSoup

class X1337:


    #Mainly just initializes the urls to be used for searching
    def __init__(self):
        
        self.urls = ["https://1337x.pro"]
        self.LIMIT = 50 


    def search(self, query) -> dict:
        
        #status check to be implemented
        self.check_status(self.urls)
       
        #for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        my_dict = {"data": []}
        list_of_urls = []
        for url in self.urls:
            
            finalUrl = url + "/search/?q={}".format(query)
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
            trs = self.soup.select("tbody tr")
            for tr in trs:
                td = tr.find_all("td")
                name = td[0].find_all("a")[-1].text
                if name:
                    torUrl = url + td[0].find_all("a")[-1]["href"]
                    list_of_urls.append(url)
                    seeders = td[1].text
                    leechers = td[2].text
                    date = td[3].text
                    size = td[4].text.replace(seeders, "")
                    #uploader = td[5].find("a").text

                    my_dict["data"].append(
                        {
                            "name": name,
                            "size": size,
                            "date": date,
                            "seeders": seeders,
                            "leechers": leechers,
                            "url": url,
                            #"uploader": uploader,
                        }
                    )
                if len(my_dict["data"]) == self.LIMIT:
                    break
            try:
                pages = self.soup.select(".pagination li a")
                my_dict["current_page"] = int(pages[0].text)
                tpages = pages[-1].text
                if tpages == ">>":
                    my_dict["total_pages"] = int(pages[-2].text)
                else:
                    my_dict["total_pages"] = int(pages[-1].text)
            except:
                ...
            
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



