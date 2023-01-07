import speech_recognition as sr

key_phrase = "Alexa clip that"

key_phrase = key_phrase.replace(" ", "")
key_phrase = key_phrase.lower()

while True:

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
        print("\n\n\n\n!!!!!CLIP!!HIT!!!!!\n\n\n\n")
