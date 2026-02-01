import hashlib
import os
import datetime
import numpy as np
import pyloudnorm as lnr
from pydub import AudioSegment, effects
import visualizer
from scipy.signal import butter, lfilter

def apply_til_eq(audio_segment, tilt_amount=0):
    """
    tilt_amount: dB gain/cut at the frequency extremes.
    Positive = Brighter (High boost, Low cut)
    Negative = Warmer (Low boost, High cut)
    """

    if tilt_amount == 0.0:
        return audio_segment

    # Convert to numpy
    samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
    sr = audio_segment.frame_rate

    # simple tilt filter logic (First-order shelving filter)
    # We use a center frequency of 1000hz
    f0 = 1000.0
    omega0 = 2 * np.pi * f0 / sr
    gain = 10**(tilt_amount / 40.0) # Distributed gain

    # Coefficient calculation for a simple tilt
    alpha = (gain - 1) / (gain + 1)
    b = [1.0, alpha]
    a = [1.0, alpha * 0.5]

    # Apply filter
    if audio_segment.channels == 2:
        samples = samples.reshape((-1, 2))
        left = lfilter(b, a, samples[:, 0])
        right = lfilter(b, a, samples[:, 1])
        processed_samples = np.column_stack((left, right)).flatten()
    else:
        processed_samples = lfilter(b, a, samples)

    # Re-normalize to original bit depth
    denom = 2**15 if audio_segment.sample_width == 2 else 2**31
    final_samples = np.clip(processed_samples, -denom, denom-1).astype(np.int16 if audio_segment.sample_width == 2 else np.int32)

    return audio_segment._spawn(final_samples.tobytes())

def apply_ms_tonal_balance(audio_segment, side_gain_db=2.0):
    # If Audio is mono there's no side channel to process
    if audio_segment.channels < 2:
        return audio_segment
    # 1. Split to Mono (L/R)
    channels = audio_segment.split_to_mono()
    left, right = channels[0], channels[1]

    # 2. Encode to Mid/Side
    mid = left.overlay(right, gain_during_overlay=-3.0) # (L/R)/2
    side = left.overlay(right.invert_phase(), gain_during_overlay=-3.0) # (L/R)/2

    # 3. Process the Side channel (e.g., make the sides brighter)
    side = side.high_pass_filter(500).apply_gain(side_gain_db)

    # 4. Decode back to Stereo
    # L = Mid + Side, R = Mid - Side
    new_left = mid.overlay(side)
    new_right = mid.overlay(side.invert_phase())

    return  AudioSegment.from_mono_audiostreams(new_left, new_right)

def apply_dither(audio_segment):
    # Adds very low-level white noise (-110dBish) to preserve low-level detail
    white_noise = effects.strip_silence(audio_segment).apply_gain(-110)
    return audio_segment.overlay(white_noise)

def apply_soft_clip(audio_segment, drive_db=3.0):
    audio_segment = audio_segment.apply_gain(drive_db)

    samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
    denom =  2**15 if audio_segment.sample_width == 2 else 2**31
    samples = samples / denom

    clipped = np.tanh(samples)

    final_samples = (clipped * denom).astype(np.int16 if audio_segment.sample_width == 2 else np.int32)
    return audio_segment._spawn(final_samples.tobytes()).apply_gain(-drive_db)


# --- File Integrity
def generate_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read in 4k blocks so we don't crash the RAM on the laptop
        for byte_block in iter(lambda: f.read(4096), b"" ):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def measure_loudness(audio_segment):
    samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32)

    if audio_segment.channels == 2:
        samples = samples.reshape((-1, 2))
    samples =  samples / (2**15) if audio_segment.sample_width == 2 else samples / (2**31)

    meter = lnr.Meter(audio_segment.frame_rate)
    loudness =  meter.integrated_loudness(samples)
    return loudness

def check_mono_compatibility(audio_segment):
    mono_version = audio_segment.set_channels(1)

    stereo_lufs =  measure_loudness(audio_segment)
    mono_lufs = measure_loudness(mono_version)

    phase_drop = stereo_lufs - mono_lufs
    if phase_drop > 3.0:
        print(f"⚠️Warning: Large phase drop ({phase_drop:.2f} dB). Your master might sound 'hollow' in mono.")
    return phase_drop

# -- Stereo Width Function
def apply_stereo_width(audio, delay_ms=20, dry_wet=0.3):
    if audio.channels == 1:
        audio = audio.set_channels(2)

    channels = audio.split_to_mono()
    left_channel = channels[0]
    right_channel = channels[1]

    silence = AudioSegment.silent(duration=delay_ms)
    delayed_right = (silence + right_channel)[:len(left_channel)]

    min_len = min(len(left_channel), len(delayed_right))

    left_final = left_channel[:min_len]
    right_final = delayed_right[:min_len]

    widened = AudioSegment.from_mono_audiosegments(left_final, right_final)
    return AudioSegment.overlay(audio, widened, gain_during_overlay=10 * dry_wet - 10)

def apply_safe_stereo_width(audio, crossover_freq=200, delay_ms=25, dry_wet=0.25):
    low_end = audio.low_pass_filter(crossover_freq).set_channels(1).set_channels(2)
    high_end = audio.high_pass_filter(crossover_freq)
    widened_highs = apply_stereo_width(high_end, delay_ms=delay_ms, dry_wet=dry_wet)

    return low_end.overlay(widened_highs)

def apply_limiter(audio_segment, ceiling=-1.0):
    current_peak =  audio_segment.max_dBFS
    if current_peak > ceiling:
        reduction = ceiling - current_peak
        return audio_segment.apply_gain(reduction)
    return audio_segment

def match_target_lufs(audio, target_lufs=-14.0, ceiling=-1.0):
    current_lufs = measure_loudness(audio)
    gain_needed =  target_lufs - current_lufs

    audio = audio.apply_gain(gain_needed)
    return apply_limiter(audio, ceiling=ceiling)

def find_zero_crossing(audio_segment, target_ms):
    samples = np.array(audio_segment.get_array_of_samples())
    target_idx = int((target_ms / 1000.0) * audio_segment.frame_rate)

    search_range = int(0.020 * audio_segment.frame_rate)
    start_search = max(0, target_idx - search_range)
    end_search = min(len(samples) - 1, target_idx + search_range)

    sub_section = samples[start_search:end_search]
    zero_cross_idx = np.where(np.diff(np.sign(sub_section)))[0]

    if len(zero_cross_idx) > 0:
        best_match = zero_cross_idx[np.abs(zero_cross_idx - (target_idx - start_search)).argmin()]
        return  (start_search + best_match) / audio_segment.frame_rate * 1000
    return target_ms

def snip_audio(input_file, start_sec, end_sec, output_file, use_clipper=False, hp_cutoff=40, lp_cutoff=15000, fade_ms=50, export_format="wav"):
    start_ms = start_sec * 1000
    end_ms = end_sec * 1000

    print(f"Loading {input_file}...")
    audio = AudioSegment.from_file(input_file)

    # --- SMART SNIP LOGIC START ---
    print(f"Aligning to zero-crossings...")
    smart_start = find_zero_crossing(audio, start_ms)
    smart_end = find_zero_crossing(audio, end_ms)
    processed = audio[smart_start:smart_end]

    # --- EQ Filters ---
    print(f"Applying Filters ...")
    processed = processed.high_pass_filter(hp_cutoff).low_pass_filter(lp_cutoff)

    # --- Tilt EQ ---
    processed = apply_til_eq(processed, tilt_amount=1.0)

    # --- Mid/Side Processing
    print(f"Applying Mid-Side Processing ...")
    processed = apply_ms_tonal_balance(processed, side_gain_db=0.7)

    # --- Stereo Widening ---
    print(f"Applying Stereo Widening---")
    processed = apply_safe_stereo_width(processed, crossover_freq=200, delay_ms=25, dry_wet=0.25)

    # --- Normalization & Limiter---
    print(f"Targeting -14 LUFs & Limiting...")
    processed = match_target_lufs(processed, target_lufs=-14.0, ceiling=-1.0)

    if use_clipper:
        print("Applying Soft Clipping (Warmth)...")
        processed = apply_soft_clip(processed)
        final_master = apply_limiter(processed, ceiling=-1.0)
    else:
        print("Applying Clean Normalization...")
        final_master = effects.normalize(processed, headroom=0.1)

    # --- Lufs ---
    lufs = measure_loudness(final_master)
    print(f"Loudness: {lufs:.2f} LUFS")

    if lufs < -16:
        print("Note: This track might be a bit quiet for streaming (-14 LUFs is the target).")
    elif lufs > -9:
        print("Note: This track is very loud/compressed (Club/EDM levels).")

    # --- Fades ---
    print(f"Applying {fade_ms}ms Fades...")
    final_master = final_master.fade_in(fade_ms).fade_out(fade_ms)

    # --- FINAL ANALYSIS BLOCK --
    lufs = measure_loudness(final_master)
    print(f"Loudness: {lufs:.2f} LUFs")
    check_mono_compatibility(final_master)

    # Metadata and Signatures
    now_full = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    now_short = datetime.datetime.now().strftime("%H:%M:%S")

    # --- Apply Dither ---
    final_master = apply_dither(final_master)


    # Export
    final_master.export(output_file, format=export_format, tags={
        "artist": "Mastered by Python Tool",
        "date": now_full
    })

    # Generate Final Signature
    sig = generate_file_hash(output_file)

    # Visualizer Call
    visualizer.visualize_mastering(input_file, output_file)

    print(f"[{now_short}] Done: {output_file}")
    print(f"[{now_short}] SHA-256 Signature: {sig}")

# --- Batch Processor ---
def batch_process(input_folder, output_folder, start, end, use_clipper=False):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith((".wav", ".mp3", ".flac")):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, f"mastered_{filename}")
            ext = filename.split('.')[-1]
            snip_audio(input_path, start, end, output_path, use_clipper=use_clipper, export_format=ext)
