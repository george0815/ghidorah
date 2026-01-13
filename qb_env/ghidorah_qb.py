import importlib.util
import sys
import os
from qb_env.novaprinter import get_results
import inspect

import sys
import qb_env.novaprinter as _novaprinter
import qb_env.helpers as _helpers

# Force legacy plugin imports to resolve correctly
sys.modules["novaprinter"] = _novaprinter
sys.modules["helpers"] = _helpers


def get_base_dir():
    if getattr(sys, "frozen", False):
        # Running as PyInstaller exe
        return os.path.dirname(sys.executable)
    else:
        # Running as normal Python script
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
QB_ENV_DIR = os.path.join(BASE_DIR, "qb_env")

if QB_ENV_DIR not in sys.path:
    sys.path.insert(0, QB_ENV_DIR)

def detect_qb_plugins():
    base_dir = get_base_dir()
    engine_dir = os.path.join(base_dir, "engines")

    print("QB ENV DIR2:", engine_dir)

    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    plugins = {}

    if not os.path.isdir(engine_dir):
        return plugins

    for filename in os.listdir(engine_dir):
        if not filename.endswith(".py"):
            continue

        path = os.path.join(engine_dir, filename)
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


ENGINE_DIR = os.path.join(BASE_DIR, "engines")

def run_qb_plugin(plugin, query, category="all"):
    plugin_path = os.path.join(ENGINE_DIR, f"{plugin}.py")

    print(plugin_path, plugin, query, category)

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
    
 
 