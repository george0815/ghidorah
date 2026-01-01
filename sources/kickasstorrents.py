import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import quote

class KickAssTorrents:


    #Mainly just initializes the urls to be used for searching
    def __init__(self):
        
        self.urls = ["https://kickasstorrents.to"]
        self.LIMIT = 50


    def search(self, query) -> dict:
        
    
        #for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        my_dict = {"data": []}
        list_of_urls = []
        for url in self.urls:
            
            finalUrl = f"{url}/usearch/{quote(query)}/1/"

            print("FINAL URL:", finalUrl)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://kickasstorrents.to/",
                "Connection": "keep-alive",
            }    

            #response
            session = requests.Session()
            session.headers.update(headers)
            res = session.get(finalUrl, timeout=15)
            print("STATUS:", res.status_code)  
            if res.status_code != 200:
                continue
            self.soup = BeautifulSoup(res.content, "html.parser")

          
            #actually parse the data, find the table rows ("[1:]" skips header row)
            for tr in self.soup.select("tr.odd,tr.even"):
                td = tr.find_all("td")
                name = tr.find("a", class_="cellMainLink").text.strip()
                url = url + tr.find("a", class_="cellMainLink")["href"]
                list_of_urls.append(url)
                if name:
                    size = td[1].text.strip()
                    seeders = td[4].text.strip()
                    leechers = td[5].text.strip()
                    uploader = td[2].text.strip()
                    date = td[3].text.strip()

                    my_dict["data"].append(
                        {
                            "name": name,
                            "size": size,
                            "date": date,
                            "seeders": seeders,
                            "leechers": leechers,
                            "url": url,
                            "uploader": uploader,
                        }
                    )
                if len(my_dict["data"]) == self.LIMIT:
                    break
            try:
                pages = self.soup.find("div", class_="pages")
                current_page = int(pages.find("a", class_="active").text)
                pages = pages.find_all("a")
                total_page = pages[-1].text
                if total_page == ">>":
                    total_page = pages[-2].text
                my_dict["current_page"] = current_page
                my_dict["total_pages"] = int(total_page)
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



