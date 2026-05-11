import pygame, random
import numpy as np
from pathlib import Path

class SoundEffects:
    def __init__(self):
        pygame.mixer.init()
        pygame.mixer.set_num_channels(10)

        self.sounds = self.load_mp3_folder("assets/sounds")
        self.voices = self.load_mp3_folder("assets/voices")

        self.whisper_sound = self._load_wav("assets/voices/schizophrenia_voices.wav")
        self.static_sound = self._load_wav("assets/sounds/static_noise_bg.wav")

        self.sound_aliases = {
            "heartbeat": "heartbeat_single",
            "wood_left1": "walking_on_wood_left1",
            "wood_left2": "walking_on_wood_left2",
            "wood_right1": "walking_on_wood_right1",
            "wood_right2": "walking_on_wood_right2",
            "tiles_left1": "walking_on_tiles_left1",
            "tiles_left2": "walking_on_tiles_left2",
            "tiles_right1": "walking_on_tiles_right1",
            "tiles_right2": "walking_on_tiles_right2",
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
        self.speech_channel     = pygame.mixer.Channel(6)
        self.static_channel     = pygame.mixer.Channel(7)
        self.whisper_channel    = pygame.mixer.Channel(8)

        # reserve these so pygame never reassigns them to other sounds
        self.static_channel.set_reserved(True) if hasattr(pygame.mixer.Channel, 'set_reserved') else None
        pygame.mixer.set_reserved(9)  # reserve channels 0-8 from auto-assignment

        self.last_heartbeat: int        = 0
        self.next_foot: str             = "left"
        self.last_footstep_time: int    = 0
        self.heartbeat_active = False
        self.heartbeat_bpm = 70
        self.last_speech_blip_time = 0

        self.speech_blip = self.make_blip_sound()
    
    def _load_wav(self, path: str) -> pygame.mixer.Sound | None:
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"[SOUND LOAD ERROR] {path}: {e}")
            return None
        
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
        if self.heartbeat_sound: self.heartbeat_sound.set_volume(volume)

    def stop_heartbeat(self):
        self.heartbeat_active = False
        self.heartbeat_channel.stop()

    def set_heartbeat_bpm(self, bpm, volume=None):
        self.heartbeat_bpm = bpm
        if volume is not None and self.heartbeat_sound: self.heartbeat_sound.set_volume(volume)

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

    def play_key(self, key: str, volume: float | None = None) -> pygame.mixer.Channel | None:
        sound = self.load_sound(key)
        if not sound: return None
        channel = sound.play()
        if channel and volume is not None:
            channel.set_volume(volume)
        return channel

    def play_voice(self, sound_key: str, volume: float | None = None) -> pygame.mixer.Channel | None:
        voice: pygame.mixer.Sound | None = self.load_voice(sound_key)
        if not voice:
            raise ValueError(f"[MISSING VOICE] {sound_key}")

        if volume is not None:
            voice.set_volume(volume)

        for channel in self.voice_channels:
            if not channel.get_busy():
                channel.play(voice)
                return channel

        channel = random.choice(self.voice_channels)
        channel.play(voice)
        return channel

    def play_voice_and_wait(self, sound_key: str, volume: float | None = None):
        channel: pygame.mixer.Channel | None = self.play_voice(sound_key, volume)
        if not channel: return
        while channel.get_busy(): yield
            
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

    def make_blip_sound(self, frequency: int = 220, duration_ms: int = 80, volume: float = 0.4) -> pygame.mixer.Sound:
        sample_rate = 44100
        num_samples = int(sample_rate * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, num_samples, endpoint=False)
        wave = np.sin(2 * np.pi * frequency * t)
        fade_samples = int(num_samples * 0.3)
        envelope = np.ones(num_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        wave = (wave * envelope * 32767 * volume).astype(np.int16)
        stereo = np.stack([wave, wave], axis=1)
        return pygame.sndarray.make_sound(stereo)

    def play_speech_blip(self, volume: float = 0.45) -> None:
        if self.speech_channel.get_busy():
            return
        self.speech_blip.set_volume(volume)
        self.speech_channel.play(self.speech_blip)
        
    def is_voice_playing(self) -> bool:
        return any(channel.get_busy() for channel in self.voice_channels)

    def stop_static(self) -> None:
        self.static_channel.stop()

    def set_static_volume(self, volume: float) -> None:
        sound = self.sounds.get("static_noise_bg")
        if sound: sound.set_volume(volume)

    def start_whispers(self, volume: float = 0.3) -> None:
        if not self.whisper_sound:
            print("[MISSING SOUND] whispers.wav / schizophrenia_voices.wav")
            return
        self.whisper_sound.set_volume(volume)
        self.whisper_channel.stop()
        self.whisper_channel.play(self.whisper_sound, loops=-1)

    def start_static(self, volume: float = 0.15) -> None:
        if not self.static_sound:
            print("[MISSING SOUND] static_noise_bg.wav")
            return
        self.static_sound.set_volume(volume)
        self.static_channel.play(self.static_sound, loops=-1)

    def stop_whispers(self) -> None:
        self.whisper_channel.stop()

    def set_whisper_volume(self, volume: float) -> None:
        sound = self.sounds.get("whispers") or self.voices.get("schizophrenia_voices")
        if sound: sound.set_volume(volume)