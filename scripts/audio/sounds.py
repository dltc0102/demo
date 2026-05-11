import pygame, random
import numpy as np
from pathlib import Path

class SoundEffects:
    def __init__(self):
        pygame.mixer.init()

        self.sounds = self.load_mp3_folder("assets/sounds")
        self.voices = self.load_mp3_folder("assets/voices")

        self.sound_aliases = {
            "heartbeat": "heartbeat_single",
            "speech_sfx": "blip",
        }

        """ footstep randomizer """
        self.footstep_sounds: dict[str, dict[str, list[str]]] = {
            "wood": {
                "left": [self.load_sound("wood_left2"), self.load_sound("wood_left2")],
                "right": [self.load_sound("wood_right1"), self.load_sound("wood_right2")],
            },
            "tiles": {
                "left": [self.load_sound("tiles_left1"), self.load_sound("tiles_left2")],
                "right": [self.load_sound("tiles_right1"), self.load_sound("tiles_right2")],
            },
            "road": {

            },
        }


        """ sounds """
        self.heartbeat_sound            = self.load_sound('heartbeat')
        self.pouring_milk_sound         = self.load_sound('pouring_milk')
        self.fridge_door_open_sound     = self.load_sound('fridge_door_open')
        self.fridge_door_close_sound    = self.load_sound('fridge_door_close')
        self.page_flip_sound            = self.load_sound('page_flip')
        self.paper_crunch_sound         = self.load_sound('paper_crunch')
        self.unscrew_sounds = [self.load_sound('unscrew1'), self.load_sound('unscrew2'), self.load_sound('unscrew3'), self.load_sound('unscrew4')]
        self.screw_on_sounds = [self.load_sound('screwon1'), self.load_sound('screwon2'), self.load_sound('screwon3'), self.load_sound('screwon4')]
        self.drinking_sounds = [self.load_sound('drinking1'), self.load_sound('drinking2')]
        self.glass_on_counter_sound = self.load_sound('glass_on_counter')
        self.glass_on_table_sound = self.load_sound('glass_on_table')

        """ channels """
        self.heartbeat_channel  = pygame.mixer.Channel(0)
        self.step_channel       = pygame.mixer.Channel(1)
        self.voice_channels = [
            pygame.mixer.Channel(2),
            pygame.mixer.Channel(3),
            pygame.mixer.Channel(4),
            pygame.mixer.Channel(5),
        ]
        self.speech_channel = pygame.mixer.Channel(6)
        self.last_speech_blip_time = 0
        self.speech_blips = []
        base_speech = self.load_sound("speech_sfx")
        if base_speech:
            self.speech_blips = self.create_speech_blips(base_speech)

        self.last_heartbeat: int        = 0
        self.next_foot: str             = "left"
        self.last_footstep_time: int    = 0
        self.heartbeat_active = False
        self.heartbeat_bpm = 70
    
    def load_mp3_folder(self, folder):
        folder = Path(folder)
        loaded = {}

        if not folder.exists():
            print(f"[SOUND FOLDER MISSING] {folder}")
            return loaded

        for path in sorted(folder.glob("*.mp3")):
            key = path.stem

            try:
                loaded[key] = pygame.mixer.Sound(str(path))
            except pygame.error as e:
                print(f"[SOUND LOAD ERROR] {key}: {path} -> {e}")

        return loaded

    def load_sound(self, key: str):
        key = self.sound_aliases.get(key, key)
        return self.sounds.get(key)

    def load_voice(self, key: str):
        return self.voices.get(key)
    
    def get_game_ticks(self):
        return pygame.time.get_ticks()
    
    def start_heartbeat(self, bpm=70, volume=0.35):
        self.heartbeat_active = True
        self.heartbeat_bpm = bpm
        self.heartbeat_sound.set_volume(volume)

    def stop_heartbeat(self):
        self.heartbeat_active = False
        self.heartbeat_channel.stop()

    def set_heartbeat_bpm(self, bpm, volume=None):
        self.heartbeat_bpm = bpm
        if volume is not None:
            self.heartbeat_sound.set_volume(volume)

    def update(self):
        if getattr(self, "heartbeat_active", False):
            self.play_heartbeat(self.heartbeat_bpm)

    def play_heartbeat(self, bpm: float):
        if not self.heartbeat_sound: return
        now = self.get_game_ticks()
        interval = max(280, int(60000 / bpm))
        if now - self.last_heartbeat >= interval:
            self.heartbeat_channel.stop()
            self.heartbeat_channel.set_volume(0.25)
            self.heartbeat_channel.play(self.heartbeat_sound)
            self.last_heartbeat = now

    def play_footstep(self, surface="wood"):
        now = self.get_game_ticks()
        if now - self.last_footstep_time < 340: return
        self.last_footstep_time = now
        sound = random.choice(self.footstep_sounds[surface][self.next_foot])
        sound.set_volume(0.2)
        self.step_channel.play(sound)
        self.next_foot = "right" if self.next_foot == "left" else "left"

    def play_fridge(self, opened=True):
        sound = self.fridge_door_open_sound if opened else self.fridge_door_close_sound
        sound.set_volume(0.25)
        sound.play()
        
    def stop_voice(self):
        for channel in self.voice_channels:
            channel.stop()

    def play(self, sound):
        if not sound: return
        sound.play()

    def play_key(self, key: str):
        sound = self.load_sound(key)
        self.play(sound)

    def play_voice(self, sound_key: str):
        voice = self.load_voice(sound_key)
        if not voice: return
        for channel in self.voice_channels:
            if not channel.get_busy():
                channel.play(voice)
                return

        random.choice(self.voice_channels).play(voice)

    def milk_cap(self, screwed_on=True):
        sounds = self.unscrew_sounds if screwed_on else self.screw_on_sounds
        sounds = [sound for sound in sounds if sound]
        if not sounds: return
        random.choice(sounds).play()

    def pitch_shift_sound(self, sound, pitch: float=1.0):
        if not sound: return None
        arr = pygame.sndarray.array(sound)
        if arr.size == 0: return sound
        old_len = arr.shape[0]
        new_len = max(1, int(old_len / pitch))
        old_indexes = np.linspace(0, old_len - 1, old_len)
        new_indexes = np.linspace(0, old_len - 1, new_len)
        if arr.ndim == 1:
            shifted = np.interp(new_indexes, old_indexes, arr)
        else:
            channels = []
            for channel in range(arr.shape[1]):
                channel_data = np.interp(new_indexes, old_indexes, arr[:, channel])
                channels.append(channel_data)
            shifted = np.stack(channels, axis=1)
        shifted = shifted.astype(arr.dtype)
        return pygame.sndarray.make_sound(shifted)

    def create_speech_blips(self, base_sound):
        pitch_values: list[float] = [ 0.82, 0.9, 0.96, 1.0, 1.05, 1.12, 1.22, ]
        blips = []
        for pitch in pitch_values:
            shifted = self.pitch_shift_sound(base_sound, pitch)
            if shifted:
                shifted.set_volume(0.18)
                blips.append(shifted)
        return blips

    def play_speech_blip(self, char=None, emotion="normal"):
        now = pygame.time.get_ticks()
        if not hasattr(self, "last_speech_blip_time"):
            self.last_speech_blip_time = 0
        if now - self.last_speech_blip_time < 22: return
        self.last_speech_blip_time = now
        sound = self.load_sound("speech_sfx")
        if not sound: sound = self.load_sound("blip")
        if not sound: return

        volume = 0.16
        if emotion == "question": volume = 0.18
        elif emotion == "exclaim": volume = 0.22
        elif emotion == "hesitant": volume = 0.12
        elif emotion == "cutoff": volume = 0.14
        sound.set_volume(volume)

        if hasattr(self, "speech_channel"):
            self.speech_channel.play(sound)
        else:
            sound.play()

    def is_voice_playing(self) -> bool:
        return any(channel.get_busy() for channel in self.voice_channels)