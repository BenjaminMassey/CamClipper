# Live Highlights

## Overview

A tool for capturing real life moments.

Written in Python, using tools like OpenCV, pyaudio, numpy, wave, moviepy, pydub, and more.

The idea is sixty seconds of video is captured, with each new second after that being added onto the end, and the first second taken off the beginning.
That gives the last sixty seconds of capture continously, which can be grabbed at any time.
This capturing is activated by speech recongition, a key phrase handled via Google's cloud services.

## Usage

Dependencies will need to be handled carefully with pip.

Google Cloud usage will need to be setup as well, see their documentation (for now).

Usage should be as easy as a command line run of

```
python clippy.py [phrase] [seconds] [resolution.x] [resolution.y]
```

## Credits

Written by Benjamin Massey, contact via benjamin.w.massey@gmail.com