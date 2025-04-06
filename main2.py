import numpy as np
import whisper
import pyaudio
import torch
from datetime import datetime

# initialize PyAudio object
p = pyaudio.PyAudio()

devices = []
device_count = p.get_device_count()
for i in range(device_count):
    device = p.get_device_info_by_index(i)
    devices.append(device)
    print(device)

device_indexes = list(map(lambda d: d['index'], devices))
device_names = tuple(map(lambda d: d['name'], devices))
print(device_indexes)
print(device_names)

selection = input(f"Please select a device ({device_indexes})...\n")

try:
    selectionInt = int(selection)
except LookupError:
    selectionInt = -1
    print("Input needs to be a whole number (0, 1, 2, ..etc)")
    quit()

if selectionInt not in device_indexes:
    print(f"{selection} not available, options are {device_indexes}")
    quit()

selectedDevice = devices[selectionInt]
sampleRate = int(selectedDevice['defaultSampleRate'])
print(f"Selection index: {selection}, name: {selectedDevice['name']}")

# open microphone stream
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, input_device_index=selectionInt, frames_per_buffer=8192)
# stream = p.open(format=pyaudio.paInt16, channels=1, rate=sampleRate, input=True, input_device_index=selectionInt, frames_per_buffer=8192)
stream.start_stream()

# initialize whisper model
model = whisper.load_model("base")

startTime = datetime.now()
previousTimePassed = datetime.now() - startTime
loopTime = 0
# continue recording until the user presses Ctrl+C
while True:
    # read audio data from the microphone stream
    data = stream.read(4096)

    loopTime = (datetime.now() - startTime - previousTimePassed).microseconds / 1000
    print(f"{loopTime} loop time")

    if len(data)==0:
        break
    print('running')

    # convert data to 1-dimensional array
    print('audio')
    audio = np.frombuffer(data, dtype=np.int16).copy()

    # convert audio tensor to floating-point tensor
    print('audio_tensor')
    audio_tensor = torch.from_numpy(audio).to(dtype=torch.float32)

    # pad/trim audio to fit 30 seconds
    print('audio_tensor 2')
    audio_tensor = whisper.pad_or_trim(audio_tensor)

    # make log-Mel spectrogram and move to the same device as the model
    print('mel')
    mel = whisper.log_mel_spectrogram(audio_tensor).to(model.device)

    # detect the spoken language
    _, probs = model.detect_language(mel)
    print('probs')
    print(f"Detected language: {max(probs, key=probs.get)}")

    # decode the audio
    print('options')
    options = whisper.DecodingOptions()
    print('result', mel, options)
    result = whisper.decode(model, mel, options)
    print('result after', result)

    # print the recognized text
    print(result.text)