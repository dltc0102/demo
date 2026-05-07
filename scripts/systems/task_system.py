
class TaskSystem:
    def __init__(self):
        self.tasks = {}

    def add(self, task):
        self.tasks[task] = False

    def complete(self, task):
        if task in self.tasks:
            self.tasks[task] = True

    def is_complete(self, task):
        return self.tasks.get(task, False)

    def all_complete(self):
        return all(self.tasks.values())