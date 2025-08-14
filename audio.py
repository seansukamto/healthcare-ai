import wave
import speech_recognition as sr
import pyaudio
import os

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

from openai import OpenAI 
client = OpenAI(api_key="dpais", base_url="http://localhost:8553/v1/openai")

audio_file = open("speech.mp3", "rb") 
transcript = client.audio.transcriptions.create(   model="whisper",   file=audio_file )

print(transcript.text)


try:
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording...")

    frames = []
    seconds = 3
    for i in range(0, int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Recording complete")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded audio
    wf = wave.open("output.wav", "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # OPTION A
    # # Speech recognition by Google
    # r = sr.Recognizer()
    
    # # FIXED: Properly open the audio file
    # with sr.AudioFile("output.wav") as source:
    #     audio = r.record(source)
    #     MyText = r.recognize_google(audio)
    #     MyText = MyText.lower()
    #     print(f"You said: {MyText}")

    # OPTION B
    # Speech recognition by Whisper
    audio_file = open("output.wav", "rb") 
    transcript = client.audio.transcriptions.create(   model="whisper",   file=audio_file )
    print(transcript.text)

# OPTION A
# except sr.UnknownValueError:
#     print("Speech recognition could not understand the audio")
# except sr.RequestError as e:
#     print(f"Could not request results from speech recognition service; {e}")
except Exception as e:
    print(f"An error occurred: {e}")