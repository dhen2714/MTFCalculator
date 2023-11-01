import json
from pathlib import Path


def read_json(fpath: str | Path) -> dict:
    with open(fpath, "r") as f:
        return json.load(f)
