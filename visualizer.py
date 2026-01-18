import matplotlib.pyplot as plt
import librosa
import librosa.display
import numpy as np

def visualize_mastering(original_path, mastered_path):
    y_orig, sr = librosa.load(original_path, duration=30)
    y_mast, _ = librosa.load(mastered_path, duration=30)

    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # ---Waveform---
    librosa.display.waveshow(y_orig, sr=sr, ax=axes[0, 0], color='#458588')
    axes[0, 0].set_title("Original Waveform")

    librosa.display.waveshow(y_mast, sr=sr, ax=axes[0, 1], color='#d79921')

    # ---Spectrograms --
    D_orig = librosa.amplitude_to_db(np.abs(librosa.stft(y_orig)), ref=np.max)
    img1 = librosa.display.specshow(D_orig, sr=sr, x_axis='time', y_axis='hz', ax=axes[1, 0])
    axes[1, 0].set_title("Original Spectrum")

    D_mast = librosa.amplitude_to_db(np.abs(librosa.stft(y_mast)), ref=np.max)
    img2 = librosa.display.specshow(D_mast, sr=sr, x_axis='time', y_axis='hz', ax=axes[1, 1])
    axes[1, 1].set_title("Mastered Spectrum")

    plt.tight_layout()
    plt.show()