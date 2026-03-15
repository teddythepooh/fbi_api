import yaml
from pathlib import Path

def load_yaml(file: Path) -> dict:
    try:
        with open(file, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"{file} not found.")
