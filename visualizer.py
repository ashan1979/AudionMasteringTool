import matplotlib.pyplot as plt
import librosa
import librosa.display
import numpy as np

def visualize_mastering(original_path, mastered_path):
    #Load audio (default 22050Hz for analysis)
    y_orig, sr = librosa.load(original_path, duration=30)
    y_mast, _ = librosa.load(mastered_path, duration=30)

    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
    fig.suptitle("Mastering Comparison: Original vs. Processed", fontsize=16)

    # --- ROW 1: WAVEFORMS (Amplitude) ---
    # Shows overall gain and dynamic range compression
    librosa.display.waveshow(y_orig, sr=sr, ax=axes[0, 0], color='#458588', alpha=0.8)
    axes[0, 0].set_title("Original Waveform")

    librosa.display.waveshow(y_mast, sr=sr, ax=axes[0, 1], color='#d79921', alpha=0.8)

    # --- ROW : SPECTOGRAMS (Frequencies) ---
    D_orig = librosa.amplitude_to_db(np.abs(librosa.stft(y_orig)), ref=np.max)
    img1 = librosa.display.specshow(D_orig, sr=sr, x_axis='time', y_axis='log', ax=axes[1, 0])
    axes[1, 0].set_title("Original Spectrum (Log Hz)")

    D_mast = librosa.amplitude_to_db(np.abs(librosa.stft(y_mast)), ref=np.max)
    img2 = librosa.display.specshow(D_mast, sr=sr, x_axis='time', y_axis='log', ax=axes[1, 1])
    axes[1, 1].set_title("Mastered Spectrum (Note EQ cuts)")

    # Add a global colorbar to show decibel intensity
    fig.colorbar(img2, ax=axes[1, :], format="%+2.0f dB")

    plt.tight_layout(rect=[0. 0.03, 1, 0.95])
    plt.show()