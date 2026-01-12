# helpers.py
import requests

def retrieve_url(url):
    return requests.get(url, timeout=10).text

def download_file(url, path):
    r = requests.get(url, stream=True)
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
