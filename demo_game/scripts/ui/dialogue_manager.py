import pygame, math, random
from demo_game.scripts.ui.font import Font

class DialogueObject:
    def __init__(self, game, text, target, stall=1500, interval: int = 28, speech_sfx: bool = True):
        self.game = game
        self.lines: list[str] = text if isinstance(text, list) else [text]
        self.target = target
        self.font = Font("assets/fonts/large_font_white.png", scale=1)
        self.stall: int = stall
        self.fade = 350
        self.y_offset = 35

        self.idx = 0
        self.start_time = pygame.time.get_ticks()
        self.finished = False

        self.visible_chars = 0
        self.char_timer = 0
        self.char_delay = interval
        self.speech_blip_interval = interval
        self.last_speech_blip_time = 0
        self.current_alpha = 0
        self.line_finished_time = None
        self.pause_until = 0
        self.speech_sfx = speech_sfx

    def current_text(self): return self.lines[self.idx]

    def visible_text(self): return self.current_text()[:self.visible_chars]

    def reset_line(self): 
        self.visible_chars = 0
        self.char_timer = 0
        self.line_finished_time = None
        self.pause_until = 0
        self.start_time = pygame.time.get_ticks()

    def get_dialogue_duration(self) -> int:
        text = self.lines[self.idx]
        word_count = max(1, len(text.split(" ")))
        ms_per_word: int = 180
        return self.fade + self.stall + (word_count * ms_per_word) + self.fade
    
    def alpha(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        duration = self.get_dialogue_duration()
        if elapsed < self.fade:
            return int(255 * (elapsed / self.fade))
        if self.line_finished_time and now > self.line_finished_time + self.stall:
            fade_elapsed = now - (self.line_finished_time + self.stall)
            return int(255 * max(0, 1 - fade_elapsed / self.fade))
        return 255
    
    def next_char_delay(self, char: str) -> int:
        text = self.current_text()
        i = self.visible_chars - 1
        if text[i:i+3] == "...": return 500
        delays = {
            ".": 220,
            ",": 120,
            "?": 260,
            "!": 160,
            " ": 18,
            "-": 320,
        }
        return delays[char] if char in delays.keys() else self.char_delay

    def word_at_index(self, text: str, index: int) -> str:
        start = index
        end = index
        while start > 0 and not text[start - 1].isspace(): start -= 1
        while end < len(text) and not text[end].isspace(): end += 1
        return text[start:end]

    def pitch_for_char(self, text: str, index: int) -> float:
        word = self.word_at_index(text, index).strip()
        if word.endswith("?!") or word.endswith("!?"):
            return random.uniform(1.35, 1.55)

        if word.endswith("?"):
            return random.uniform(1.25, 1.45)

        if word.endswith("!"):
            return random.uniform(1.2, 1.4)

        if word.endswith("..."):
            return random.uniform(1.18, 1.35)

        return random.uniform(0.9, 1.15)
    
    def update_typing(self):
        now = pygame.time.get_ticks()
        if now < self.pause_until: return
        text = self.current_text()
        if self.visible_chars >= len(text):
            if self.line_finished_time is None:
                self.line_finished_time = now
            return

        self.char_timer += max(16, self.game.clock.get_time())
        while self.visible_chars < len(text) and self.char_timer >= self.char_delay:
            char_index = self.visible_chars
            char = text[char_index]
            self.visible_chars += 1
            self.char_timer -= self.char_delay
            if self.speech_sfx and not char.isspace():
                self.game.sfx.play_speech_blip()

            if char in (".", ",", "?", "!", "-"):
                self.pause_until = now + self.next_char_delay(char)
                break
    
    def get_speech_emotion(self, text, index):
        remaining_text = text[index:]
        if "?" in remaining_text[:8]: return "question"
        if "!" in remaining_text[:8]: return "exclaim"
        if "..." in remaining_text[:8]: return "hesitant"
        if "-" in remaining_text[:5]: return "cutoff"
        return "normal"

    def update(self):
        if self.finished: return
        self.update_typing()
        now = pygame.time.get_ticks()
        if self.line_finished_time and now >= self.line_finished_time + self.stall + self.fade:
            self.idx += 1
            if self.idx >= len(self.lines):
                self.finished = True
                return
            self.reset_line()

    def draw_text_with_effects(self, text_surf, text):
        x = 0
        tick = pygame.time.get_ticks()
        ellipsis_start = text.rfind("...")
        for i, char in enumerate(text):
            if char == " ":
                x += self.font.space_width + self.font.spacing
                continue
            if char not in self.font.characters:
                continue
            char_img = self.font.characters[char].copy()
            y = 0
            if ellipsis_start != -1 and ellipsis_start <= i < ellipsis_start + 3:
                y += int(math.sin(tick * 0.012 + (i - ellipsis_start) * 0.9) * 2)
            if char == "-" and i == len(text) - 1:
                flash = random.random() > 0.35
                if not flash:
                    x += char_img.get_width() + self.font.spacing
                    continue
            text_surf.blit(char_img, (x, y))
            x += char_img.get_width() + self.font.spacing
    
    def render(self, surface, offset=(0, 0)):
        if self.finished: return
        text = self.visible_text()
        if not text: return
        width = max(1, self.font.text_width(text))
        height = next(iter(self.font.characters.values())).get_height() + 8
        text_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self.draw_text_with_effects(text_surf, text)
        text_surf.set_alpha(max(0, min(255, self.alpha())))
        rect = self.target.rect()
        x = rect.centerx - offset[0] - width // 2
        y = rect.top - offset[1] - self.y_offset
        surface.blit(text_surf, (x, y))

class DialogueManager:
    def __init__(self, game):
        self.game = game
        self.dialogues = []

    def dialogue_object(self, text, target, stall=1500, interval: int = 28, speech_sfx: bool = True):
        dialogue = DialogueObject(self.game, text, target, stall, interval, speech_sfx)
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