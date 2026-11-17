"""JARVIS configuration loader."""
import os
import yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_PATH = os.path.join(_ROOT, "config.yaml")


def load_config(path: str = _CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_root"] = _ROOT
    cfg["_data_dir"] = os.path.join(_ROOT, "data")
    os.makedirs(cfg["_data_dir"], exist_ok=True)
    return cfg


CONFIG = load_config()
