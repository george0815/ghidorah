import importlib.util
import sys
import os
from qb_env.novaprinter import get_results
import inspect

import sys

def get_runtime_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)

    here = os.path.dirname(os.path.abspath(__file__))

    if os.path.basename(here) == "qb_env":
        return os.path.dirname(here)

    return here

RUNTIME_ROOT = get_runtime_root()
QB_ENV_DIR = os.path.join(RUNTIME_ROOT, "qb_env")
ENGINE_DIR = os.path.join(QB_ENV_DIR, "engines")

if QB_ENV_DIR not in sys.path:
    sys.path.insert(0, QB_ENV_DIR)

print("=== DEBUG plugin paths ===")
print("sys.frozen:", getattr(sys, "frozen", False))
print("RUNTIME_ROOT:", RUNTIME_ROOT)
print("QB_ENV_DIR:", QB_ENV_DIR, "exists:", os.path.isdir(QB_ENV_DIR))
print("ENGINE_DIR:", ENGINE_DIR, "exists:", os.path.isdir(ENGINE_DIR))
if os.path.isdir(ENGINE_DIR):
    print("ENGINE FILES:", os.listdir(ENGINE_DIR))
print("==========================")


import qb_env.novaprinter as _novaprinter
import qb_env.helpers as _helpers

# Force legacy plugin imports to resolve correctly
sys.modules["novaprinter"] = _novaprinter
sys.modules["helpers"] = _helpers




def detect_qb_plugins():

    if QB_ENV_DIR not in sys.path:
        sys.path.insert(0, QB_ENV_DIR)

    plugins = {}

    if not os.path.isdir(ENGINE_DIR):
        return plugins

    for filename in os.listdir(ENGINE_DIR):
        if not filename.endswith(".py"):
            continue

        path = os.path.join(ENGINE_DIR, filename)
        module_name = f"{os.path.splitext(filename)[0]}"

        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        for obj in module.__dict__.values():
            if (
                inspect.isclass(obj)
                and hasattr(obj, "search")
                and callable(obj.search)
            ):
                plugins[module_name] = obj()
                break

    return plugins



def run_qb_plugin(plugin, query, category="all"):
    plugin_path = os.path.join(ENGINE_DIR, f"{plugin}.py")


    if not os.path.isfile(plugin_path):
        raise FileNotFoundError(f"Plugin not found: {plugin_path}")

    spec = importlib.util.spec_from_file_location(plugin, plugin_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for obj in module.__dict__.values():
        if inspect.isclass(obj) and hasattr(obj, "search"):
            engine = obj()
            engine.search(query, category)
            return get_results()

    return []


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python ghidorah_qb.py <plugin> <category> <query>")
        sys.exit(1)

    plugin = sys.argv[1]
    category = sys.argv[2]
    query = sys.argv[3]

    results = run_qb_plugin(plugin, query, category)

    for r in results:
        print(r)
    
 
 