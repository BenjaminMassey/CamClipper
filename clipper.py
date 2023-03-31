# Libraries
import cv2
import numpy as np
import pyaudio
from datetime import datetime
import wave
from moviepy.editor import *
from pydub import AudioSegment
from pydub.playback import play
from pydub.effects import speedup
import subprocess
import sys
from sys import platform as system_platform
import threading
import keyboard
import time

# Command line arguments

seconds_to_save = 10
res_x = 640
res_y = 480

error_msg = "Expected usage: \"python clipper.py [seconds] [resolution.x] [resolution.y]\""

if (len(sys.argv)) != 4:
    print(error_msg)
    quit()
else:
    try:
        seconds_to_save = int(sys.argv[1])
        res_x = int(sys.argv[2])
        res_y = int(sys.argv[3])
    except:
        print(error_msg)
        quit()

# Global variables
running = True
clip_that = False
audio_rate = 48000
audio_buffer = 2048
auto_audio_delay = False # use additional calculated delay (experimental)
audio_delay = 0 # addition of silence at beginning: for syncing
audio_cut = 0 # removal of audio from beginning: for adjustment

# Initialize the webcam and audio stream, calc delay
webcam = cv2.VideoCapture(0)
webcam.set(cv2.CAP_PROP_FRAME_WIDTH, res_x)
webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, res_y)
video_time = datetime.now()
audio_stream = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=audio_rate, input=True, frames_per_buffer=audio_buffer)
audio_time = datetime.now()

if (auto_audio_delay):
    audio_delay = (audio_time - video_time).total_seconds()
    print("AUDIO DELAY DETECTED OF", audio_delay, "SECONDS")

# Inform of capturing
print("Finished initializing: taking running video")

def clip_loop(webcam, audio_stream):
    global running, clip_that, seconds_to_save, audio_rate, audio_buffer, audio_delay
    
    # Initialize variables to store the last minute of video and audio
    video_frames = []
    audio_samples = []
    
    # Start capturing frames and audio from the webcam feed
    while running:
        # Get the current frame and audio sample from the webcam feed
        ret, frame = webcam.read()
        assert ret
        audio_data = audio_stream.read(audio_buffer)
        
        # Add the frame and audio sample to their respective lists
        video_frames.append(frame)
        audio_samples.append(np.frombuffer(audio_data, np.int16))
        
        # If we have more than 60 seconds of video and audio, remove the oldest frame and audio sample
        if len(video_frames) > seconds_to_save * webcam.get(cv2.CAP_PROP_FPS):
            video_frames.pop(0)
            audio_samples.pop(0)
        
        # Check if the save condition has been hit
        if clip_that or keyboard.is_pressed('c'):
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
            audio_dur = audio_file.getnframes() / audio_rate
            audio_ratio = audio_dur / seconds_to_save
            audio_file.close()
            
            # Adjust for audio delay https://stackoverflow.com/a/46791870
            audio_in_file = "./" + filename + " TEMP.wav"
            audio_out_file = "./" + filename + " TEMP ADJUSTED.wav"
            delay_segment = AudioSegment.silent(duration=(audio_delay * 1000))
            temp_audio = AudioSegment.from_wav(audio_in_file)
            the_audio = speedup(temp_audio, audio_ratio, audio_ratio * 100)
            final_adjusted = delay_segment + the_audio[(audio_cut * 1000):]
            final_adjusted.export(audio_out_file, format="wav")
            
            # Combine the video and audio into a single file
            movie_video = VideoFileClip("./" + filename + " TEMP.mp4")
            movie_audio_raw = AudioFileClip("./" + filename + " TEMP ADJUSTED.wav")
            movie_audio = CompositeAudioClip([movie_audio_raw])
            movie_video.audio = movie_audio
            movie_video.write_videofile("./" + filename + ".mp4")
            
            # Cleanup temp files
            removecmd = "rm *TEMP*"
            if system_platform == "win32":
                removecmd = "del *TEMP*"
            subprocess.call(removecmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            print("Enjoy your video! (" + filename + ")")

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
            global clip_that
            clip_that = True

def abort_loop():
    global running

    while running:
        if keyboard.is_pressed('q'):
            running = False
        else:
            time.sleep(0.25)

# Start speech rec thread
alexa = threading.Thread(target=speech_loop)
alexa.start()

# Start abort thread
abort = threading.Thread(target=abort_loop)
abort.start()

# Start the webcam and audio stream
clip_loop(webcam, audio_stream)

# Release the webcam and audio stream
webcam.release()
audio_stream.stop_stream()
audio_stream.close()

# Bye
print("Goodbye!")
quit()
