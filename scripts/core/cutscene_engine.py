

class _CutsceneHandle:
    def __init__(self, cutscene, runner):
        self.cutscene = cutscene
        self.runner = runner

    def overlap_with(self, *sound_keys: str, volume: float | None = None):
        for key in sound_keys:
            self.cutscene.game.sfx.play_voice(key, volume)
        return self

    def __iter__(self):
        yield from self.runner()


class _VoiceHandle:
    def __init__(self, cutscene, sound_key):
        self.cutscene = cutscene
        self.sound_key = sound_key

    def overlap_with(self, *sound_keys: str, volume: float | None = None):
        for key in sound_keys:
            self.cutscene.game.sfx.play_voice(key, volume)
        return self

    def __iter__(self):
        yield from self.cutscene.wait_until_voice_finished()

class CutsceneEngine:
    def __init__(self, game):
        self.game = game
        self.sequence = None
        self.wait_until = 0

    def play_voice(self, sound_key: str, volume: float | None = None) -> "_VoiceHandle":
        self.game.sfx.play_voice(sound_key, volume)
        return _VoiceHandle(self, sound_key)

    def clear(self):
        self.stop()
        self.game.thought_manager.clear()
        self.game.dialogue_manager.dialogues.clear()
        
    def start(self, sequence):
        self.sequence = sequence
        self.wait_until = 0

    def stop(self):
        self.sequence = None
        self.wait_until = 0

    def update(self):
        if not self.sequence: return
        now = self.game.get_ticks()
        if now < self.wait_until: return
        try:
            result = next(self.sequence)

            if isinstance(result, int):
                self.wait_until = now + result
        except StopIteration:
            self.sequence = None

    def say(self, text, target, stall=1500, interval: int = 28):
        dialogue = self.game.dialogue_manager.dialogue_object(text=text, target=target, stall=stall, interval=interval)
        while not dialogue.finished: yield

    def wait(self, milliseconds):
        yield milliseconds

    def wait_until_voice_finished(self):
        while self.game.sfx.is_voice_playing(): yield
    
    def heartbeat(self, bpm: float = 70, beats: int = 1):
        interval = int(60000 / bpm)
        for _ in range(beats):
            self.game.sfx.heartbeat_sound.play()
            yield from self.wait(interval)
            
    def voice(self, sound_key: str, volume: float | None = None):
        self.game.sfx.play_voice(sound_key)
        yield from self.wait_until_voice_finished()
    
    def shakethink(self, text, target, stall: int = 2200, gap: int = 250):
        lines = text if isinstance(text, list) else [text]
        for line in lines:
            thought = self.game.thought_manager.shakethink(str(line), target, stall=stall)
            while not thought.finished: yield
            yield from self.wait(gap)
        
    def cloudthink(self, lines, target, stall: int = 1800, gap: int = 180):
        def runner():
            fixed_lines = lines if isinstance(lines, list) else [lines]
            thoughts = []

            for line in fixed_lines:
                thoughts.append(
                    self.game.thought_manager.cloudthink(
                        line,
                        target,
                        stall=stall * len(fixed_lines) / 3
                    )
                )
                yield from self.wait(gap)

            while any(not thought.finished for thought in thoughts):
                yield
        return _CutsceneHandle(self, runner)

    def racethink(self, lines, target, stall: int = 850, gap: int = 650):
        def runner():
            fixed_lines = lines if isinstance(lines, list) else [lines]

            for line in fixed_lines:
                self.game.thought_manager.racethink(line, target, stall=stall)
                yield from self.wait(gap)
        return _CutsceneHandle(self, runner)
    
    def spawn_cloudthink(self, lines, target, stall: int = 1400):
        self.game.thought_manager.cloudthink(lines, target, stall=stall)
        yield

    def spawn_racethink(self, lines, target, stall: int = 700, curve: bool = True):
        self.game.thought_manager.racethink(lines, target, stall=stall, curve=curve)
        yield