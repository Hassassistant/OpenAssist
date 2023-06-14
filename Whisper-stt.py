import pyaudio
import openai
import wave
import requests

######### UPDATE THESE ############

HOME_ASSISTANT_URL = "https://your_home_assistant_utl.xyz"

HA_LONG_LIVED_ACCESS_TOKEN = "ey....."

openai.api_key = "sk-...."

###################################


CHUNK = 1024
WIDTH = 2
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 10
WAVE_OUTPUT_FILENAME = "output.wav"

p = pyaudio.PyAudio()

stream = p.open(format=p.get_format_from_width(WIDTH),
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("* recording")

frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("* done recording")

stream.stop_stream()
stream.close()

p.terminate()

wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(p.get_format_from_width(WIDTH)))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

# Transcribe audio file
audio_file = open(WAVE_OUTPUT_FILENAME, "rb")
transcript = openai.Audio.transcribe(model="whisper-1", file=audio_file, response_format="text")
print(transcript)

# Define the URL for the Home Assistant API call
url = f"{HOME_ASSISTANT_URL}/api/states/input_text.openassist_prompt"

# Define the headers for the API call
headers = {
    "Authorization": f"Bearer {HA_LONG_LIVED_ACCESS_TOKEN}",
    "content-type": "application/json",
}

# Define the data for the API call
data = {
    "state": transcript
}

# Make the API call
response = requests.post(url, headers=headers, json=data)

# Print the response
print(response.text)

print(response.json())
