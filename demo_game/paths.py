from pathlib import Path

_PKG = Path(__file__).parent

def asset(*parts: str) -> str:
    flat = []
    for p in parts: flat.extend(str(p).replace("\\", "/").strip("/").split("/"))
    return str(_PKG.joinpath(*flat))