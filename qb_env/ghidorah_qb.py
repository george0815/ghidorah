import importlib.util
import sys
import os
import inspect

from qb_env.novaprinter import get_results
import qb_env.novaprinter as _novaprinter
import qb_env.helpers as _helpers


# ---------------------------------------------------------------------------
# Runtime path resolution
# ---------------------------------------------------------------------------

def get_runtime_root():
    """
    Determine the runtime root directory.

    Handles both normal execution and frozen (PyInstaller) environments.
    If executed from within the qb_env directory, returns its parent.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)

    here = os.path.dirname(os.path.abspath(__file__))

    if os.path.basename(here) == "qb_env":
        return os.path.dirname(here)

    return here


RUNTIME_ROOT = get_runtime_root()
QB_ENV_DIR = os.path.join(RUNTIME_ROOT, "qb_env")
ENGINE_DIR = os.path.join(QB_ENV_DIR, "engines")

# Ensure qb_env is importable at runtime
if QB_ENV_DIR not in sys.path:
    sys.path.insert(0, QB_ENV_DIR)


# ---------------------------------------------------------------------------
# Debug utilities
# ---------------------------------------------------------------------------

def print_path_debug() -> str:
    """
    Return diagnostic information about runtime paths and environment state.

    Useful for debugging frozen builds and plugin discovery issues.
    """
    lines = []
    lines.append("==========================")

    lines.append(f"sys.frozen: {getattr(sys, 'frozen', False)}")
    lines.append(f"RUNTIME_ROOT: {RUNTIME_ROOT}")
    lines.append(f"QB_ENV_DIR: {QB_ENV_DIR} exists: {os.path.isdir(QB_ENV_DIR)}")
    lines.append(f"ENGINE_DIR: {ENGINE_DIR} exists: {os.path.isdir(ENGINE_DIR)}")

    if os.path.isdir(ENGINE_DIR):
        lines.append(f"ENGINE FILES: {os.listdir(ENGINE_DIR)}")

    lines.append("==========================")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Legacy qBittorrent plugin compatibility
# ---------------------------------------------------------------------------

# Force legacy plugin imports to resolve correctly
sys.modules["novaprinter"] = _novaprinter
sys.modules["helpers"] = _helpers


# ---------------------------------------------------------------------------
# Plugin discovery
# ---------------------------------------------------------------------------

def detect_qb_plugins():
    """
    Detect and load available qBittorrent search plugins.

    Scans the qb_env/engines directory, dynamically imports each plugin,
    and registers any class that exposes a callable `search` method.

    Returns:
        A dictionary mapping plugin names to instantiated plugin objects.
    """

    if QB_ENV_DIR not in sys.path:
        sys.path.insert(0, QB_ENV_DIR)

    plugins = {}

    if not os.path.isdir(ENGINE_DIR):
        return plugins

    for filename in os.listdir(ENGINE_DIR):
        if not filename.endswith(".py"):
            continue

        path = os.path.join(ENGINE_DIR, filename)
        module_name = os.path.splitext(filename)[0]

        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Locate the first class with a callable search method
        for obj in module.__dict__.values():
            if (
                inspect.isclass(obj)
                and hasattr(obj, "search")
                and callable(obj.search)
            ):
                plugins[module_name] = obj()
                break

    return plugins


# ---------------------------------------------------------------------------
# Plugin execution
# ---------------------------------------------------------------------------

def run_qb_plugin(plugin, query, category="all"):
    """
    Execute a qBittorrent search plugin.

    Loads the specified plugin module dynamically, executes its search
    method, and retrieves normalized results from novaprinter.

    Args:
        plugin: Plugin name (without .py extension).
        query: Search query string.
        category: Search category (defaults to "all").

    Returns:
        A list of search results.
    """
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


# ---------------------------------------------------------------------------
# Standalone CLI entry
# ---------------------------------------------------------------------------

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
