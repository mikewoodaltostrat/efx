from pydub import AudioSegment
import os

# --- Configuration ---
# 1. Enter the name of the audio file you downloaded.
source_filename = "test.wav" 
# 2. This will be the name of your new, converted file.
target_filename = "test_16khz.wav" 

# --- Conversion Process ---
try:
    # Load your original audio file
    print(f"Loading '{source_filename}'...")
    audio = AudioSegment.from_file(source_filename)

    # Resample the audio to 16,000 Hz
    print("Resampling to 16,000 Hz...")
    resampled_audio = audio.set_frame_rate(16000)

    # Ensure the audio is mono (single channel), as recommended for STT
    resampled_audio = resampled_audio.set_channels(1)

    # Export the new, resampled file in WAV format
    print(f"Saving new file as '{target_filename}'...")
    resampled_audio.export(target_filename, format="wav")

    print("\n✅ Success! Your converted file is ready.")

except FileNotFoundError:
    print(f"\n❌ Error: The file '{source_filename}' was not found.")
    print("Please make sure it's in the same directory as this script.")

except Exception as e:
    print(f"\n❌ An unexpected error occurred: {e}")