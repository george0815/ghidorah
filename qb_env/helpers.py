import requests

def retrieve_url(url, timeout=10):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text

def download_file(url, path):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
