import pygame, random

class SoundEffects:
    def __init__(self):
        pygame.mixer.init()

        """ sounds """
        self.heartbeat_sound = pygame.mixer.Sound(
            "assets/sounds/heartbeat_single.mp3"
        )

        self.snowstep_sounds = [
            pygame.mixer.Sound("assets/sounds/snowstep1.mp3"),
            pygame.mixer.Sound("assets/sounds/snowstep2.mp3"),
            pygame.mixer.Sound("assets/sounds/snowstep3.mp3"),
        ]

        """ channels """
        self.heartbeat_channel = pygame.mixer.Channel(0)
        self.step_channel = pygame.mixer.Channel(1)
        self.voice_channel = pygame.mixer.Channel(2)

        """ timers """
        self.last_heartbeat = 0
        self.last_step = 0

    def play_heartbeat(self, bpm: float):
        now = pygame.time.get_ticks()
        interval = max(120, int(60000 / bpm))
        if now - self.last_heartbeat >= interval:
            self.heartbeat_channel.play(self.heartbeat_sound)
            self.last_heartbeat = now

    def play_footstep(self):
        now = pygame.time.get_ticks()
        if now - self.last_step < 280: return
        sound = random.choice(self.snowstep_sounds)
        self.step_channel.play(sound)
        self.last_step = now

    def play_voice(self, filename: str, volume: float = 0.45):
        sound = pygame.mixer.Sound(
            f"assets/voices/{filename}"
        )
        sound.set_volume(volume)
        self.voice_channel.play(sound)

    def stop_voice(self):
        self.voice_channel.stop()

    def is_voice_playing(self) -> bool:
        return self.voice_channel.get_busy()