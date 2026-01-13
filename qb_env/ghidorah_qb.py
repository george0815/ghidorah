import importlib.util
import sys
import os
from qb_env.novaprinter import get_results
import inspect




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




def run_qb_plugin(plugin_path, query):
    plugin_path = os.path.abspath(plugin_path)
    module_name = f"qb_run_{os.path.splitext(os.path.basename(plugin_path))[0]}"

    spec = importlib.util.spec_from_file_location(module_name, plugin_path)
    module = importlib.util.module_from_spec(spec)

    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    for obj in module.__dict__.values():
        if hasattr(obj, "search") and callable(obj.search):
            obj().search(query)
            return get_results()

    return []


if __name__ == "__main__":

    """
    if len(sys.argv) != 3:
        print("Usage: python test.py <plugin_path> <search_query>")
        sys.exit(1)

    plugin_path = sys.argv[1]
    search_query = sys.argv[2]

    print(plugin_path, search_query)

    results = run_qb_plugin(plugin_path, search_query)
    for result in results:
        print(result)"""
    
    plugins = detect_qb_plugins()

    for name, plugin in plugins.items():
        print(f"plugin: {name}")
        plugin