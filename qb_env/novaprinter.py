# novaprinter.py
_RESULTS = []

def prettyPrinter(data):
    _RESULTS.append(data)

def get_results():
    global _RESULTS
    out = _RESULTS
    _RESULTS = []
    return out
