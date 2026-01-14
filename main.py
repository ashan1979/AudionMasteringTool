import hashlib
import os
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
def apply_stereo_width(audio, delay_ms=20):
    if audio.channels == 1:
        audio = audio.set_channels(2)

    channels = audio.split_to_mono()
    left_channel = channels[0]
    right_channel = channels[1]

    silence = AudioSegment.silent(duration=delay_ms)
    delayed_right = (silence + right_channel)[:len(left_channel)]

    return AudioSegment.from_mono_audiostreams(left_channel, delayed_right)

def snip_audio(input_file, start_sec, end_sec, output_file, hp_cutoff=80, lp_cutoff=10000, fade_ms=50, export_format="wav"):
    # pydub works in milliseconds
    start_ms = start_sec * 1000
    end_ms = end_sec * 1000

    print(f"Loading {input_file}...")
    audio = AudioSegment.from_file(input_file)

    print(f"Snipping ...")
    snip = audio[start_ms:end_ms]

    # --- EQ Filters ---
    print(f"Applying Filters ...")
    filtered = snip.high_pass_filter(hp_cutoff).low_pass_filter(lp_cutoff)

    # --- Normalization ---
    print(f"Normalizing...")
    normalized = effects.normalize(filtered)

    # --- Safety Limiter (-0.1 dB)
    if normalized.max_dBFS > -0.1:
        normalized = normalized - (normalized.max_dBFS + 0.1)

    # --- Stereo Widening ---
    print(f"Applying Stereo Widening---")
    widened = apply_stereo_width(normalized, delay_ms=25)
    # --- Fades ---
    print(f"Applying {fade_ms}ms Fades...")
    final_audio = widened.fade_in(fade_ms).fade_out(fade_ms)

    # Export
    final_audio.export(output_file, format=export_format)

    # Integrity Signature
    sig = generate_file_hash(output_file)

    print(f"Done: {output_file}")
    print(f"SHA-256 Signature: {sig}")

# --- NEW: Batch Processor ---
def batch_process(input_folder, output_folder, start, end):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith((".wav", ".mp3", ".flac")):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, f"mastered_{filename}")

            # --- Extract the extension
            ext = filename.split('.')[-1]

            snip_audio(input_path, start, end, output_path, export_format=ext)

# Example usage (uncomment and change 'my_song.wav' to a real file you have)
# snip_audio("my_song.wav", 10, 20, "snip_output.wav")