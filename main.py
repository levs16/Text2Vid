import numpy as np
from scipy.io.wavfile import write
import sys
from moviepy.editor import VideoClip, AudioFileClip, concatenate_videoclips
import cv2

def text_to_audio(input_file, repeat_count=1):
    try:
        # Read the content of the file
        with open(input_file, "r") as file:
            text = file.read()

        # Convert text to a sequence of integers
        data = np.array([ord(char) for char in text], dtype=np.int16)
        
        # Map ASCII values to a higher frequency range
        min_freq = 1000
        max_freq = 3000
        data = np.interp(data, (min(data), max(data)), (min_freq, max_freq))
        
        # Generate a sine wave for each character
        sample_rate = 44100  # Sample rate in Hz
        t = np.linspace(0, 0.1, int(sample_rate * 0.1), endpoint=False)  # 0.1 second per character
        audio = np.sin(2 * np.pi * data[:, np.newaxis] * t).astype(np.float32)

        # Flatten the array to make it a 1D audio signal
        audio = audio.flatten()

        # Output filename
        audio_output_file = f"{input_file.split('.')[0]}-enc.wav"
        
        # Write to a WAV file
        write(audio_output_file, sample_rate, audio)
        print(f"Encoded audio saved as {audio_output_file}")

        # Create a video with this audio
        create_video(input_file.split('.')[0], text, audio_output_file, repeat_count)

    except Exception as e:
        print(f"An error occurred: {e}")

def create_video(base_filename, text, audio_file, repeat_count):
    # Load the audio file
    audio_clip = AudioFileClip(audio_file)

    # Define a function to animate squares
    def make_frame(t):
        frame_height = 720
        frame_width = 1280
        image = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
        square_size = 20
        num_per_row = frame_width // square_size
        duration_per_char = 0.1
        char_index = int(t / duration_per_char) % len(text)
        
        for i, char in enumerate(text[:char_index + 1]):
            row = i // num_per_row
            col = i % num_per_row
            y = row * square_size
            x = col * square_size
            
            np.random.seed(ord(char))
            color = np.random.randint(0, 255, 3)
            
            image[y:y+square_size, x:x+square_size] = color

        return image

    # Define a function for the repeat screen
    def repeat_frame(t):
        frame_height = 720
        frame_width = 1280
        image = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
        cv2.putText(image, "REPEAT", (frame_width // 2 - 100, frame_height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        return image

    # Generate a beep sound for the repeat screen and save it
    def generate_beep():
        sample_rate = 44100
        duration = 2  # seconds
        frequency = 1000  # Hz
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        beep_sound = (0.5 * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
        beep_output_file = f"{base_filename}-beep.wav"
        write(beep_output_file, sample_rate, beep_sound)
        return beep_output_file

    beep_file = generate_beep()
    repeat_audio = AudioFileClip(beep_file)

    # Create video and audio clips
    video_clip = VideoClip(make_frame, duration=len(text) * 0.1)
    video_clip = video_clip.set_audio(audio_clip)

    repeat_clip = VideoClip(repeat_frame, duration=2)
    repeat_clip = repeat_clip.set_audio(repeat_audio)

    # Append repeat screen and repeat the video if repeat_count is not zero
    if repeat_count > 0:
        final_clip = concatenate_videoclips([video_clip, repeat_clip, video_clip])
    else:
        final_clip = video_clip

    # Add an    "END" screen
    def end_frame(t):
        frame_height = 720
        frame_width = 1280
        image = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
        cv2.putText(image, "END", (frame_width // 2 - 50, frame_height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)
        return image

    end_clip = VideoClip(end_frame, duration=2)
    final_clip = concatenate_videoclips([final_clip, end_clip])

    # Define a function for the decoding table
    def decoding_table_frame(t):
        frame_height = 720
        frame_width = 1280
        image = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
        square_size = 30  # Size of each square
        padding = 20  # Space between squares
        x_offset = 50  # Starting x-coordinate offset
        y_offset = 50  # Starting y-coordinate offset

        unique_chars = sorted(set(text))  # Use a set to remove duplicates and sort the result

        # Calculate the number of squares per row and the number of rows needed
        num_per_row = (frame_width - x_offset) // (square_size + padding)
        num_rows = (frame_height - y_offset) // (square_size + padding)

        for i, char in enumerate(unique_chars):
            row = i // num_per_row
            col = i % num_per_row
            if row >= num_rows:  # Check if we have more characters than can fit in the allocated rows
                break  # Stop adding more characters if we run out of space
            x = x_offset + col * (square_size + padding)
            y = y_offset + row * (square_size + padding)
            
            np.random.seed(ord(char))
            color = np.random.randint(0, 255, 3)
            image[y:y+square_size, x:x+square_size] = color
            
            # Adjust text placement to be more readable
            cv2.putText(image, f"{char}", (x + 5, y + square_size - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return image

    decoding_table_clip = VideoClip(decoding_table_frame, duration=0.5)
    final_clip = concatenate_videoclips([final_clip, decoding_table_clip])

    # Write the result to a file
    video_output_file = f"{base_filename}-video.mp4"
    final_clip.write_videofile(video_output_file, codec="libx264", fps=10, audio_codec="aac")
    print(f"Video with audio saved as {video_output_file}")

if __name__ == "__main__":
    repeat_count = 1  # Default repeat count
    if len(sys.argv) < 2:
        print("Usage: python t2a.py <filename> [repeat_count]")
    else:
        input_file = sys.argv[1]
        if len(sys.argv) > 2:
            repeat_count = int(sys.argv[2])
        text_to_audio(input_file, repeat_count)
