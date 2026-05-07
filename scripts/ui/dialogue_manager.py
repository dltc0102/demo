import pygame
from scripts.ui.font import Font

class DialogueObject:
    def __init__(self, text, target, stall=1500):
        self.lines: list[str] = text if isinstance(text, list) else [text]
        self.target = target
        self.font = Font("assets/fonts/large_font_white.png", scale=1)
        self.stall: int = stall
        self.fade = 350
        self.y_offset = 35

        self.idx = 0
        self.start_time = pygame.time.get_ticks()
        self.finished = False

    def get_dialogue_duration(self) -> int:
        text = self.lines[self.idx]
        word_count = max(1, len(text.split(" ")))
        ms_per_word: int = 180
        return self.fade + self.stall + (word_count * ms_per_word) + self.fade
    
    def update(self):
        if self.finished: return
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time

        if elapsed >= self.get_dialogue_duration():
            self.idx += 1
            self.start_time = now

            if self.idx >= len(self.lines):
                self.finished = True

    def alpha(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        duration = self.get_dialogue_duration()
        if elapsed < self.fade:
            return int(255 * (elapsed / self.fade))
        if elapsed > duration - self.fade:
            return int(255 * ((duration - elapsed) / self.fade))
        return 255
    
    def render(self, surface, offset=(0, 0)):
        if self.finished: return
        text = self.lines[self.idx]
        width = self.font.text_width(text)
        height = next(iter(self.font.characters.values())).get_height()
        text_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self.font.render(text_surf, text, (0, 0))
        text_surf.set_alpha(max(0, min(255, self.alpha())))
        rect = self.target.rect()
        x = rect.centerx - offset[0] - width // 2
        y = rect.top - offset[1] - self.y_offset
        surface.blit(text_surf, (x, y))

class DialogueManager:
    def __init__(self):
        self.dialogues = []

    def dialogue_object(self, text, target, stall=1500):
        dialogue = DialogueObject(
            text=text,
            target=target,
            stall=stall
        )
        self.dialogues.append(dialogue)
        return dialogue

    def update(self):
        for dialogue in self.dialogues[:]:
            dialogue.update()

            if dialogue.finished:
                self.dialogues.remove(dialogue)

    def render(self, surface, offset=(0, 0)):
        for dialogue in self.dialogues:
            dialogue.render(surface, offset)
