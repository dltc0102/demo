from TTS.api import TTS
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range
import os


OUTPUT_DIR = "assets/generated_voices"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def make_whisper(input_path, output_path):
    audio = AudioSegment.from_wav(input_path)

    # thin the voice slightly
    audio = audio.high_pass_filter(250)
    audio = audio.low_pass_filter(4200)

    # softer dynamics
    audio = compress_dynamic_range(audio)

    # quieter, more intimate
    audio = audio - 8

    # fake whisper stereo effect
    left = audio.pan(-0.2)

    right = (
        audio.pan(0.2)
        .fade_in(20)
    )

    whispered = left.overlay(right)

    # soften edges
    whispered = whispered.fade_in(80).fade_out(180)

    whispered.export(output_path, format="wav")


tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")


raw_path = f"{OUTPUT_DIR}/raw_whisper.wav"
final_path = f"{OUTPUT_DIR}/whisper.wav"

tts.tts_to_file(
    text="...you heard that too, didn't you?",
    file_path="whisper.wav",
    speaker_wav="reference_voice.wav",
    language="en"
)

make_whisper(raw_path, final_path)

print(f"generated: {final_path}")