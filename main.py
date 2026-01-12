from pydub import AudioSegment, effects
def snip_audio(input_file, start_sec, end_sec, output_file, hp_cutoff=80, lp_cutoff=10000):
    # pydub works in milliseconds
    start_ms = start_sec * 1000
    end_ms = end_sec * 1000

    print(f"Loading {input_file}...")
    audio = AudioSegment.from_file(input_file)

    print(f"Snipping ...")
    snip = audio[start_ms:end_ms]

    # --- EQ Filters ---
    print(f"Applying High-Pass ({hp_cutoff}Hz) and Low-Pass ({lp_cutoff}Hz)...")
    # Removes the "mud" from below the cutoff
    filtered = snip.high_pass_filter(hp_cutoff)
    # Removes the "hiss/harshness" above the cutoff
    filtered = filtered.low_pass_filter(lp_cutoff)

    # --- Normalization ---
    #This brings the peak volume to 0 dB (or very close to it)
    print(f"Normalizing audio levels...")
    normalized_snip = effects.normalize(filtered)
    # --------------------------

    normalized_snip.export(output_file, format="wav")
    print(f"Saved normalized snip to {output_file}")


# Example usage (uncomment and change 'my_song.wav' to a real file you have)
# snip_audio("my_song.wav", 10, 20, "snip_output.wav")