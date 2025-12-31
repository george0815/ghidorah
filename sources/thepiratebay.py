from sources.source import source
import requests
import re
from bs4 import BeautifulSoup

class ThePirateBay(source):

    def __init__(self):
        self.urls = ["https://thepiratebay10.org"], 
        ["https://tpb.party/"], 
        ["https://pirateproxylive.org/"]  

    def search(self, query) -> dict:
        self.check_status()
       

        url = "https://thepiratebay10.org" + "/search/{}/{}/99/0".format(query, '1')

        print(url)

        headers = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
}

        res = requests.get(url, headers=headers, timeout=15)

        print("STATUS:", res.status_code)
        


        soup = BeautifulSoup(res.content, "html.parser")

        my_dict = {"data": []}
        for tr in soup.find_all("tr")[1:]:
            td = tr.find_all("td")
            try:
                name = td[1].find("a").text
            except:
                name = None
            if name:
                url = td[1].find("a")["href"]
                magnet = td[3].find_all("a")[0]["href"]
                size = td[4].text.strip()
                seeders = td[5].text
                leechers = td[6].text
                category = td[0].find_all("a")[0].text
                uploader = td[7].text
                dateUploaded = td[2].text
                    
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
        last_tr = soup.find_all("tr")[-1]
        potential_page_link = last_tr.find("td").find("a").href
        check_if_pagination_available = potential_page_link is not None and potential_page_link[:len("/search/")] == "/search/"
        if check_if_pagination_available:
            current_page = last_tr.find("td").find("b").text
            my_dict["current_page"] = int(current_page)
            my_dict["total_pages"] = int(
                last_tr.find("td").find_all("a")[-2].text
            )
        return my_dict

    pass



    def check_status(self):
        super().check_status(self.urls)





