import requests
import re
from bs4 import BeautifulSoup

class ThePirateBay:


    #Mainly just initializes the urls to be used for searching
    def __init__(self):
        
        self.urls = ["https://thepiratebay10.org", "https://tpb.party", "https://pirateproxylive.org"]


    def search(self, query) -> dict:
        
        #status check to be implemented
        self.check_status(self.urls)
       
        #for each url, check for STATUS 200, then check if valid data is returned, if not, move to next url
        my_dict = {"data": []}
        for url in self.urls:
            
            finalUrl = url + "/search/{}/{}/99/0".format(query, '1')
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
            for table_row in self.soup.find_all("tr")[1:]:

                row_data = table_row.find_all("td")
                try:
                    name = row_data[1].find("a").text
                except:
                    name = None
                #parse acutal torrent data
                if name:
                    url = row_data[1].find("a")["href"]
                    magnet = row_data[3].find_all("a")[0]["href"]
                    size = row_data[4].text.strip()
                    seeders = row_data[5].text
                    leechers = row_data[6].text
                    category = row_data[0].find_all("a")[0].text
                    uploader = row_data[7].text
                    dateUploaded = row_data[2].text

                    my_dict["data"].append(
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
                if len(my_dict["data"]) == 100:
                    break

            #gets pagination info (current page number and total pages available)        
            if len(self.soup.find_all("tr")) >= 1:
                last_table_row = self.soup.find_all("tr")[-1]
                potential_page_link = last_table_row.find("td").find("a").href
                check_if_pagination_available = potential_page_link is not None and potential_page_link[:len("/search/")] == "/search/"
                if check_if_pagination_available:
                    current_page = last_table_row.find("td").find("b").text
                    my_dict["current_page"] = int(current_page)
                    my_dict["total_pages"] = int(
                        last_table_row.find("td").find_all("a")[-2].text
                    )

            print(len(my_dict["data"]))
            if len(my_dict["data"]) > 0:
                break
            
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



