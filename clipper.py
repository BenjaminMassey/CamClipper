import cv2
import numpy as np
import pyaudio
import keyboard
from datetime import datetime
import wave

# Want to print this at end, so global
filename = ""

# Initialize the webcam and audio stream
webcam = cv2.VideoCapture(0)
audio_stream = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

def save_button_pressed():
    return keyboard.is_pressed('x')

def save_last_minute(webcam, audio_stream):
    # Initialize variables to store the last minute of video and audio
    video_frames = []
    audio_samples = []
    
    # Start capturing frames and audio from the webcam feed
    while True:
        # Get the current frame and audio sample from the webcam feed
        ret, frame = webcam.read()
        assert ret
        audio_data = audio_stream.read(1024)
        
        # Add the frame and audio sample to their respective lists
        video_frames.append(frame)
        audio_samples.append(np.frombuffer(audio_data, np.int16))
        
        # If we have more than 60 seconds of video and audio, remove the oldest frame and audio sample
        if len(video_frames) > 60 * webcam.get(cv2.CAP_PROP_FPS):
            video_frames.pop(0)
            audio_samples.pop(0)
        
        # Check if the save button has been pressed
        if save_button_pressed():
            # Quick date time for filename
            now = datetime.now()
            dt_string = now.strftime("%d-%m-%Y %H-%M-%S")
            global filename
            filename = "Clip " + dt_string
            
            # Initialize the video writer
            fourcc = cv2.VideoWriter_fourcc('F','M','P','4')
            video_file = cv2.VideoWriter(filename + ".mp4", fourcc, webcam.get(cv2.CAP_PROP_FPS),
                                          (int(webcam.get(cv2.CAP_PROP_FRAME_WIDTH)), int(webcam.get(cv2.CAP_PROP_FRAME_HEIGHT))))

            
            # Save the last minute of video to the output file
            for frame in video_frames:
                video_file.write(frame)

            # Initialize the audio file
            audio_file = wave.open(filename + ".wav", "w")
            audio_file.setnframes(len(audio_samples))
            audio_file.setnchannels(1)
            audio_file.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            audio_file.setframerate(44100)

            # Save the last minute of audio to the output file
            np_audio = np.array(audio_samples, dtype=np.int16)
            audio_file.writeframes(np_audio)

            # Done :)
            video_file.release()
            audio_file.close()
            break

# Inform of capturing
print("Finished initializing: taking running video")

# Start the webcam and audio stream
save_last_minute(webcam, audio_stream)

# Release the webcam and audio stream
webcam.release()
audio_stream.stop_stream()
audio_stream.close()

# Bye
print("Enjoy your video! (" + filename + ")")
