from pydub import AudioSegment, effects

def snip_audio(input_file, start_sec, end_sec, output_file, hp_cutoff=80, lp_cutoff=10000, export_format="wav"):
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
    normalized_snip = effects.normalize(filtered)
    # --------------------------

    # Use the export_format variable here
    normalized_snip.export(output_file, format=export_format)
    print(f"Successfully saved {output_file} as {export_format.upper()}")

# Example usage (uncomment and change 'my_song.wav' to a real file you have)
# snip_audio("my_song.wav", 10, 20, "snip_output.wav")