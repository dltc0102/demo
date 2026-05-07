
class Mail:
    def __init__(self, sender, text, tasks=None):
        self.sender = sender
        self.text = text
        self.tasks = tasks or []
        self.read = False


class MailSystem:
    def __init__(self):
        self.mail = []
        self.open = False

    def add_mail(self, sender, text, tasks=None):
        self.mail.append(Mail(sender, text, tasks))

    def has_unread(self):
        return any(not m.read for m in self.mail)

    def toggle(self):
        self.open = not self.open
        if self.open:
            for m in self.mail:
                m.read = True