import hashlib
import os
import datetime
from pydub import AudioSegment, effects

# --- File Integrity
def generate_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read in 4k blocks so we don't crash the RAM on the laptop
        for byte_block in iter(lambda: f.read(4096), b"" ):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# -- Stereo Width Function
def apply_stereo_width(audio, delay_ms=20, dry_wet=0.3):
    if audio.channels == 1:
        audio = audio.set_channels(2)

    channels = audio.split_to_mono()
    left_channel = channels[0]
    right_channel = channels[1]

    silence = AudioSegment.silent(duration=delay_ms)
    delayed_right = (silence + right_channel)[:len(left_channel)]

    widened = AudioSegment.from_mono_audiostreams(left_channel, delayed_right)
    return AudioSegment.overlay(audio, widened, gain_during_overlay=10 * dry_wet - 10)

def apply_safe_stereo_width(audio, crossover_freq=200, delay_ms=25, dry_wet=0.25):
    low_end = audio.low_pass_filter(crossover_freq).set_channels(1).set_channels(2)
    high_end = audio.high_pass_filter(crossover_freq)
    widened_highs = apply_stereo_width(high_end, delay_ms=delay_ms, dry_wet=dry_wet)

    return low_end.overlay(widened_highs)


def snip_audio(input_file, start_sec, end_sec, output_file, hp_cutoff=40, lp_cutoff=15000, fade_ms=50, export_format="wav"):
    start_ms = start_sec * 1000
    end_ms = end_sec * 1000

    print(f"Loading {input_file}...")
    audio = AudioSegment.from_file(input_file)
    processed = audio[start_ms:end_ms]

    # --- EQ Filters ---
    print(f"Applying Filters ...")
    processed = processed.high_pass_filter(hp_cutoff).low_pass_filter(lp_cutoff)

    # --- Stereo Widening ---
    print(f"Applying Stereo Widening---")
    processed = apply_safe_stereo_width(processed, crossover_freq=200, delay_ms=25, dry_wet=0.25)

    # --- Normalization & Limiter---
    print(f"Normalizing & Limiting...")
    final_master = effects.normalize(processed, headroom=0.1)

    # --- Fades ---
    print(f"Applying {fade_ms}ms Fades...")
    final_master = final_master.fade_in(fade_ms).fade_out(fade_ms)

    # Export
    final_master.export(output_file, format=export_format)

    # Metadata and Signatures
    now = datetime.datetime.now().strftime("%H:%M:%S")
    sig = generate_file_hash(output_file)

    print(f"[{now}] Done: {output_file}")
    print(f"[{now}] SHA-256 Signature: {sig}")

# --- Batch Processor ---
def batch_process(input_folder, output_folder, start, end):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith((".wav", ".mp3", ".flac")):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, f"mastered_{filename}")
            ext = filename.split('.')[-1]
            snip_audio(input_path, start, end, output_path, export_format=ext)
