from pathlib import Path
import pygame

class LiveReloader:
    def __init__(self):
        self.files = {}

    def watch(self, path):
        path = Path(path)
        self.files[path] = path.stat().st_mtime

    def changed(self, path):
        path = Path(path)

        if not path.exists():
            return False

        old_time = self.files.get(path)
        new_time = path.stat().st_mtime

        if old_time is None:
            self.files[path] = new_time
            return False

        if new_time != old_time:
            self.files[path] = new_time
            return True

        return False