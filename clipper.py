# Libraries
import cv2
import numpy as np
import pyaudio
from datetime import datetime
import wave
import ffmpeg
import subprocess
from sys import platform as system_platform
import threading
import keyboard
import time

# Global variables
running = True
clip_that = False
seconds_to_save = 60
audio_rate = 44100
audio_buffer = 1024

# Initialize the webcam and audio stream
webcam = cv2.VideoCapture(0)
audio_stream = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, \
                                      rate=audio_rate, input=True, frames_per_buffer=audio_buffer)

def clip_loop():
    global running, webcam, audio_stream, clip_that, seconds_to_save, audio_rate, audio_buffer
    
    # Initialize variables to store the last minute of video and audio
    video_frames = []
    audio_samples = []
    
    # Start capturing frames and audio from the webcam feed
    while running:
        # Get the current frame and audio sample from the webcam feed
        ret, frame = webcam.read()
        if not ret:
            print("Failure with webcam, trying again...")
            audio_stream.stop_stream()
            audio_stream.close()
            webcam.release()
            webcam = cv2.VideoCapture(0)
            audio_stream = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, \
                                          rate=audio_rate, input=True, frames_per_buffer=audio_buffer)
            continue
        audio_data = audio_stream.read(audio_buffer)

        # Show webcam
        cv2.imshow("Webcam Feed", frame)
        cv2.waitKey(1)
        
        # Add the frame and audio sample to their respective lists
        video_frames.append(frame)
        audio_samples.append(np.frombuffer(audio_data, np.int16))
        
        # If we have more than 60 seconds of video and audio, remove the oldest frame and audio sample
        if len(video_frames) > seconds_to_save * webcam.get(cv2.CAP_PROP_FPS):
            video_frames.pop(0)
            audio_samples.pop(0)
        
        # Check if the save condition has been hit
        if clip_that:
            # Untoggle for next clip
            clip_that = False
            
            # Quick date time for filename
            now = datetime.now()
            dt_string = now.strftime("%d-%m-%Y %H-%M-%S")
            filename = "Clip " + dt_string
            
            # Initialize the video writer
            fourcc = cv2.VideoWriter_fourcc('F','M','P','4')
            video_file = cv2.VideoWriter(filename + " TEMP.mp4", fourcc, webcam.get(cv2.CAP_PROP_FPS),
                                          (int(webcam.get(cv2.CAP_PROP_FRAME_WIDTH)), int(webcam.get(cv2.CAP_PROP_FRAME_HEIGHT))))

            # Save the last minute of video to the output file
            for frame in video_frames:
                video_file.write(frame)
            video_file.release()

            # Initialize the audio file
            audio_file = wave.open(filename + " TEMP.wav", "w")
            audio_file.setnframes(len(audio_samples))
            audio_file.setnchannels(1)
            audio_file.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            audio_file.setframerate(audio_rate)

            # Save the last minute of audio to the output file
            np_audio = np.array(audio_samples, dtype=np.int16)
            audio_file.writeframes(np_audio)
            audio_file.close()
            
            # Combine the video and audio into a single file
            video_temp = ffmpeg.input("./" + filename + " TEMP.mp4")
            audio_temp = ffmpeg.input("./" + filename + " TEMP.wav")
            ffmpeg.concat(video_temp, audio_temp, v=1, a=1).output("./" + filename + ".mp4").run(overwrite_output=True)

            # Cleanup temp files
            removecmd = "rm *TEMP*"
            if system_platform == "win32":
                removecmd = "del *TEMP*"
            subprocess.call(removecmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            print("Enjoy your video! (" + filename + ")")

        
        # Release the webcam and audio stream
        webcam.release()
        audio_stream.stop_stream()
        audio_stream.close()

def speech_loop():
    global running, clip_that
    
    import speech_recognition as sr

    key_phrase = "Alexa clip that"

    key_phrase = key_phrase.replace(" ", "")
    key_phrase = key_phrase.lower()

    while running:

        r = sr.Recognizer()
        mic = sr.Microphone(device_index=1)

        with mic as source:
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source)

        result = None

        try:
            result = r.recognize_google(audio)
        except:
            pass

        if result is None:
            continue
        
        if key_phrase in result.replace(" ", "").lower():
            clip_that = True

# Inform of capturing
print("Finished initializing: taking running video")

# Start speech rec thread
alexa = threading.Thread(target=speech_loop)
alexa.start()

# Start the capture thread
capture = threading.Thread(target=clip_loop)
capture.start()

while running:
    if keyboard.is_pressed('x'):
        running = False
    else:
        time.sleep(0.25)

print("Goodbye!")
quit()
