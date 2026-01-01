import requests
import re
from bs4 import BeautifulSoup

class YTS:


    #Mainly just initializes the urls to be used for searching
    def __init__(self):
        
        self.urls = ["https://yts.do"]
        self.LIMIT = 50


    def search(self, query) -> dict:
        
        #status check to be implemented
        self.check_status(self.urls)
       
        #for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        my_dict = {"data": []}
        for url in self.urls:
            
            finalUrl = url + "/browse-movies/{}/all/all/0/0/latest".format(query)
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
            for div in self.soup.find_all("div", class_="browse-movie-wrap"):
                url = div.find("a")["href"]
                my_dict["data"].append({"url": url})
                if len(my_dict["data"]) == self.LIMIT:
                    break
            try:
                ul = self.soup.find("ul", class_="tsc_pagination")
                current_page = ul.find("a", class_="current").text
                my_dict["current_page"] = int(current_page)
                if current_page:
                    total_results = self.soup.select_one(
                        "body > div.main-content > div.browse-content > div > h2 > b"
                    ).text
                    if "," in total_results:
                        total_results = total_results.replace(",", "")
                    total_page = int(total_results) / 20
                    my_dict["total_pages"] = (
                        int(total_page) + 1
                        if type(total_page) == float
                        else int(total_page)
                    )

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



