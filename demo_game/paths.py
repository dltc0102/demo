from pathlib import Path
import sys

def _base() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

def asset(*parts: str) -> str:
    flat = []
    for p in parts: flat.extend(str(p).replace("\\", "/").strip("/").split("/"))
    return str(_base().joinpath(*flat))