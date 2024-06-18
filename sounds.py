import simpleaudio as sa
import numpy as np

def play_sound():
    # Set the frequency and duration
    frequency = 440  # Frequency in Hz (A4 note)
    duration = 0.1  # Duration in seconds

    # Create a waveform
    sample_rate = 44100  # Sample rate in Hz
    amplitude = 16000  # Amplitude (volume)

    # Generate a sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    waveform = np.sin(frequency * 2 * np.pi * t)
    waveform = (waveform * amplitude).astype(np.int16)

    # Play the sound
    audio = sa.play_buffer(waveform, 1, 2, sample_rate)

    # Wait for the waveform to finish playing
    audio.wait_done()
