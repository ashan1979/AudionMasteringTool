from pydub import AudioSegment,
def snip_audio(input_file, start_sec, end_sec, output_file):
    # pydub works in milliseconds
    start_ms = start_sec * 1000
    end_ms = end_sec * 1000

    print(f"Loading {input_file}...")
    audio = AudioSegment.from_file(input_file)

    print(f"Snipping from {start_sec}s to {end_sec}s...")
    snip = audio[start_ms:end_ms]

    snip.export(output_file, format="wav")
    print(f"Saving to {output_file}")

# Example usage (uncomment and change 'my_song.wav' to a real file you have)
# snip_audio("my_song.wav", 10, 20, "snip_output.wav")