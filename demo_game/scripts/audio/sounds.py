import pygame, random
import numpy as np
from pathlib import Path
from paths import asset

class SoundEffects:
    def __init__(self):
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)

        self.sounds = self.load_mp3_folder(asset("assets/sounds"))
        self.voices = self.load_mp3_folder(asset("assets/voices"))

        self.whisper_sound = self._load_wav(asset("assets/voices/schizophrenia_voices.wav"))
        self.static_sound = self._load_wav(asset("assets/sounds/static_noise_bg.wav"))

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
            "pill_bottle": "opening_pill_bottle",
            "inf_laughter": "infectious_laughter",
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
        self.heartbeat_sound            = self.amplify_sound(self.load_sound('heartbeat'), gain=4.5)
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
        self.fridge_channel     = pygame.mixer.Channel(9)

        pygame.mixer.set_reserved(11)

        self.last_heartbeat: int        = 0
        self.next_foot: str             = "left"
        self.last_footstep_time: int    = 0
        self.heartbeat_active = False
        self.heartbeat_bpm = 70
        self.last_speech_blip_time = 0

        self.speech_blip = self.make_blip_sound()
        self.bpm_boost_target = None

        """ master volume multipliers (set externally by game.py) """
        self.master_volume: float    = 1.0
        self.sfx_master: float       = 1.0
        self.voices_master: float    = 1.0
        self.heartbeat_master: float = 1.0

    def set_masters(self, master: float, sfx: float, voices: float, heartbeat: float) -> None:
        self.master_volume    = float(master)
        self.sfx_master       = float(sfx)
        self.voices_master    = float(voices)
        self.heartbeat_master = float(heartbeat)

    def _sfx_vol(self, base: float) -> float:
        return max(0.0, min(1.0, base * self.sfx_master * self.master_volume))

    def _voice_vol(self, base: float) -> float:
        return max(0.0, min(1.0, base * self.voices_master * self.master_volume))

    def _heartbeat_vol(self, base: float) -> float:
        return max(0.0, min(1.0, base * self.heartbeat_master * self.master_volume))
    
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
    
    def start_heartbeat(self, bpm=80, volume: float = 1.0):
        if not self.heartbeat_sound:
            print("[MISSING SOUND] assets/sounds/heartbeat_single.mp3")
            return

        self.heartbeat_active = True
        self.heartbeat_bpm = max(1, float(bpm))
        self._heartbeat_base_volume: float = float(volume)

        eff = self._heartbeat_vol(self._heartbeat_base_volume)
        self.heartbeat_sound.set_volume(eff)
        self.heartbeat_channel.set_volume(eff)

        interval = max(280, int(60000 / self.heartbeat_bpm))
        self.last_heartbeat = pygame.time.get_ticks() - interval
        self.play_heartbeat(self.heartbeat_bpm)

    def stop_heartbeat(self):
        self.heartbeat_active = False
        self.heartbeat_channel.stop()

    def set_heartbeat_bpm(self, bpm: float, volume: float | None = None) -> None:
        if not self.heartbeat_sound:
            print("[MISSING SOUND] assets/sounds/heartbeat_single.mp3")
            return

        self.heartbeat_active = True
        self.heartbeat_bpm = max(1, float(bpm))
        if volume is not None:
            self._heartbeat_base_volume = float(volume)

        base = getattr(self, "_heartbeat_base_volume", 1.0)
        eff = self._heartbeat_vol(base)
        self.heartbeat_sound.set_volume(eff)
        self.heartbeat_channel.set_volume(eff)

    def update(self):
        if getattr(self, "heartbeat_active", False): self.play_heartbeat(self.heartbeat_bpm)
        self.update_ambient()
        self.update_bpm_linked_audio()

    def update_bpm_linked_audio(self) -> None:
        if self.bpm_boost_target is None: return
        bpm = float(getattr(self.bpm_boost_target, "bpm", 80.0))
        ratio = max(0.0, min(1.0, (bpm - 80.0) / 100.0))
        fade = self._ambient_fade_factor() if hasattr(self, "_ambient_fade_start") else 1.0
        static_vol = (0.10 + ratio * 0.45) * fade
        if self.static_sound:
            self.static_sound.set_volume(self._sfx_vol(static_vol))
        if hasattr(self, "_ambient_channel") and self._ambient_playing:
            self._ambient_channel.set_volume(self._sfx_vol((0.25 + ratio * 0.40) * fade))

    def play_heartbeat(self, bpm: float | None = None):
        if not self.heartbeat_sound: return
        bpm = max(1, float(bpm if bpm is not None else self.heartbeat_bpm))
        now = self.get_game_ticks()
        interval = max(240, int(60000 / bpm))

        if now - self.last_heartbeat >= interval:
            base = getattr(self, "_heartbeat_base_volume", 1.0)
            eff = self._heartbeat_vol(base)
            self.heartbeat_sound.set_volume(eff)
            self.heartbeat_channel.stop()
            self.heartbeat_channel.set_volume(eff)
            self.heartbeat_channel.play(self.heartbeat_sound)
            self.last_heartbeat = now

    def play_footstep(self, surface="wood"):
        now = self.get_game_ticks()
        if now - self.last_footstep_time < 340: return
        self.last_footstep_time = now
        sound = random.choice(self.footstep_sounds[surface][self.next_foot])
        sound.set_volume(self._sfx_vol(0.2))
        self.step_channel.play(sound)
        self.next_foot = "right" if self.next_foot == "left" else "left"

    def play_fridge(self, opened=True):
        key = "fridge_door_open" if opened else "fridge_door_close"
        sound = self.fridge_door_open_sound if opened else self.fridge_door_close_sound
        if not sound:
            print(f"[MISSING SOUND] {key}.mp3 in assets/sounds")
            return None
        sound.set_volume(self._sfx_vol(0.65))
        self.fridge_channel.stop()
        self.fridge_channel.play(sound)
        return self.fridge_channel
        
    def stop_voice(self):
        for channel in self.voice_channels:
            channel.stop()

    def play(self, sound):
        if not sound: return
        sound.play()

    def play_key(self, key: str, volume: float | None = None, bpm_boost: float = 0.0) -> pygame.mixer.Channel | None:
        sound = self.load_sound(key)
        if not sound: return None
        channel = sound.play()
        if channel and volume is not None:
            channel.set_volume(self._sfx_vol(volume))
        elif channel:
            # No explicit volume — re-assert master scaling on the Sound's current base.
            # (apply_master_volumes from game.py keeps Sound.get_volume() already-scaled,
            #  so playing it as-is is correct; nothing to do.)
            pass
        if bpm_boost > 0 and self.bpm_boost_target is not None:
            self.bpm_boost_target.bump_bpm(bpm_boost)
        return channel
    
    def play_voice(self, sound_key: str, volume: float | None = None, bpm_boost: float = 0.0) -> pygame.mixer.Channel | None:
        voice: pygame.mixer.Sound | None = self.load_voice(sound_key)
        if not voice: raise ValueError(f"[MISSING VOICE] {sound_key}")
        if volume is not None: voice.set_volume(self._voice_vol(volume))
        if bpm_boost > 0 and self.bpm_boost_target is not None:
            self.bpm_boost_target.bump_bpm(bpm_boost)
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

    def amplify_sound(self, sound: pygame.mixer.Sound | None, gain: float = 2.0) -> pygame.mixer.Sound | None:
        if sound is None: return None
        try:
            arr = pygame.sndarray.array(sound)
        except Exception:
            return sound
        if arr.size == 0: return sound
        amplified = np.clip(arr.astype(np.float32) * gain, -32768, 32767).astype(arr.dtype)
        return pygame.sndarray.make_sound(amplified)

    def make_blip_sound(self, frequency: int = 220, duration_ms: int = 80, volume: float = 0.4) -> pygame.mixer.Sound:
        mixer_init = pygame.mixer.get_init()
        sample_rate = mixer_init[0] if mixer_init else 44100
        mixer_channels = mixer_init[2] if mixer_init else 2
        num_samples = int(sample_rate * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, num_samples, endpoint=False)
        wave = np.sin(2 * np.pi * frequency * t)
        fade_samples = max(1, int(num_samples * 0.3))
        envelope = np.ones(num_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        audio = (wave * envelope * 32767 * volume).astype(np.int16)
        if mixer_channels == 2:
            audio = np.column_stack((audio, audio))
        elif mixer_channels != 1:
            audio = np.repeat(audio[:, None], mixer_channels, axis=1)
        return pygame.sndarray.make_sound(audio)

    def play_speech_blip(self, volume: float = 0.45) -> None:
        if self.speech_channel.get_busy():
            return
        self.speech_blip.set_volume(self._sfx_vol(volume))
        self.speech_channel.play(self.speech_blip)
        
    def is_voice_playing(self) -> bool:
        return any(channel.get_busy() for channel in self.voice_channels)

    def stop_static(self) -> None:
        self.static_channel.stop()

    def set_static_volume(self, volume: float) -> None:
        sound = self.sounds.get("static_noise_bg")
        if sound: sound.set_volume(self._sfx_vol(volume))

    def start_whispers(self, volume: float = 0.3) -> None:
        if not self.whisper_sound:
            print("[MISSING SOUND] whispers.wav / schizophrenia_voices.wav")
            return
        self.whisper_sound.set_volume(self._voice_vol(volume))
        self.whisper_channel.stop()
        self.whisper_channel.play(self.whisper_sound, loops=-1)

    def start_static(self, volume: float = 0.15) -> None:
        if not self.static_sound:
            print("[MISSING SOUND] static_noise_bg.wav")
            return
        self.static_sound.set_volume(self._sfx_vol(volume))
        self.static_channel.play(self.static_sound, loops=-1)

    def stop_whispers(self) -> None:
        self.whisper_channel.stop()

    def set_whisper_volume(self, volume: float) -> None:
        sound = self.sounds.get("whispers") or self.voices.get("schizophrenia_voices")
        if sound: sound.set_volume(self._voice_vol(volume))

    def start_ambient(self, static_volume: float = 0.15, fade_in_ms: int = 3000) -> None:
        if self.static_sound:
            self.static_sound.set_volume(0.0)
            self.static_channel.stop()
            self.static_channel.play(self.static_sound, loops=-1)

        self._static_base_volume: float = static_volume
        self._ambient_fade_start: int = pygame.time.get_ticks()
        self._ambient_fade_duration: int = max(1, int(fade_in_ms))

        self._ambient_pool: list[str] = ["whispers", "bar_sounds", "muffled_talking"]
        self._ambient_last: str | None = None
        self._ambient_channel: pygame.mixer.Channel = pygame.mixer.Channel(10)
        self._ambient_next_time: int = pygame.time.get_ticks() + fade_in_ms + random.randint(8_000, 18_000)
        self._ambient_playing: bool = False

    def _ambient_fade_factor(self) -> float:
        start = getattr(self, "_ambient_fade_start", None)
        if start is None: return 1.0
        elapsed = pygame.time.get_ticks() - start
        return max(0.0, min(1.0, elapsed / self._ambient_fade_duration))

    def stop_ambient(self) -> None:
        self.static_channel.stop()
        if hasattr(self, "_ambient_channel"):
            self._ambient_channel.stop()
        if hasattr(self, "_ambient_playing"):
            self._ambient_playing = False

    def update_ambient(self) -> None:
        if not hasattr(self, "_ambient_pool"): return
        now = pygame.time.get_ticks()
        if self.bpm_boost_target is None and self.static_sound is not None:
            fade = self._ambient_fade_factor()
            base = getattr(self, "_static_base_volume", 0.15)
            self.static_sound.set_volume(self._sfx_vol(base * fade))

        if self._ambient_playing and not self._ambient_channel.get_busy():
            self._ambient_playing = False
            self._ambient_next_time = now + random.randint(12_000, 28_000)

        if self._ambient_playing or now < self._ambient_next_time: return
        candidates = [k for k in self._ambient_pool if k != self._ambient_last]
        random.shuffle(candidates)
        chosen_key: str | None = None
        chosen_sound: pygame.mixer.Sound | None = None
        for key in candidates:
            snd = self.sounds.get(key) or self.voices.get(key)
            if snd:
                chosen_key = key
                chosen_sound = snd
                break

        if not chosen_sound:
            self._ambient_next_time = now + random.randint(15_000, 30_000)
            return

        chosen_sound.set_volume(self._sfx_vol(random.uniform(0.25, 0.55)))
        self._ambient_channel.stop()
        self._ambient_channel.play(chosen_sound, loops=0)
        self._ambient_last = chosen_key
        self._ambient_playing = True

    def stop_all_gameplay_audio(self) -> None:
        self.heartbeat_channel.stop()
        self.step_channel.stop()
        self.speech_channel.stop()
        self.static_channel.stop()
        self.whisper_channel.stop()
        if hasattr(self, "fridge_channel"): self.fridge_channel.stop()
        if hasattr(self, "_ambient_channel"): self._ambient_channel.stop()
        for ch in self.voice_channels: ch.stop()
        self.heartbeat_active = False
        if hasattr(self, "_ambient_playing"): self._ambient_playing = False

    def resume_gameplay_audio(self, static_volume: float = 0.15) -> None:
        self.heartbeat_active = True
        if self.static_sound:
            self.static_sound.set_volume(self._sfx_vol(static_volume))
            self.static_channel.play(self.static_sound, loops=-1)
        if hasattr(self, "_ambient_next_time"):
            self._ambient_next_time = pygame.time.get_ticks() + random.randint(5_000, 12_000)
            self._ambient_playing = False