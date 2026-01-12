import importlib.util
import sys
import os
from novaprinter import get_results

def run_qbt_plugin(path, query):
    module_name = os.path.splitext(os.path.basename(path))[0]

    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)

    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Find plugin class
    for obj in module.__dict__.values():
        if hasattr(obj, "search"):
            plugin = obj()
            plugin.search(query)
            return get_results()

    return []

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test.py <plugin_path> <search_query>")
        sys.exit(1)

    plugin_path = sys.argv[1]
    search_query = sys.argv[2]

    print(plugin_path, search_query)

    results = run_qbt_plugin(plugin_path, search_query)
    for result in results:
        print(result)
