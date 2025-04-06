from vosk import Model, KaldiRecognizer
import pyaudio
import json
import base64
from io import BytesIO
from datetime import datetime
import subprocess
import os
import sys
import language_tool_python
import math
from openai import OpenAI
import pyscreenshot as ImageGrab

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff
import asyncio
import configparser
import pyperclip as pc

import gui
from punctuator2 import punctuate_return, initialize_punctuator
from data import PUNCTUATION_VOCABULARY
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk import data, download

try:
    data.find('tokenizers/punkt')
except LookupError:
    download('punkt')

try:
    data.find('tokenizers/punkt_tab')
except LookupError:
    download('punkt_tab')

config = configparser.ConfigParser()
config.read('config.ini')
client = OpenAI(api_key=config['openapi'].get('ApiKey'))
# print(openai.Model.list())

ui = gui.InterviewGUI()
ui.run_logic(blocking=False)

init_args = initialize_punctuator('Demo-Europarl-EN.pcl')

question_words = ["what", "why", "when", "where",
                  "name", "is", "how", "do", "does",
                  "which", "are", "could", "would",
                  "should", "has", "have", "whom", "whose", "can", "don't"]

paa = pyaudio.PyAudio()
tool = language_tool_python.LanguageTool('en-US')  # use a local server (automatically set up), language English
print(tool.correct('language tool loaded'))

devices = []
device_count = paa.get_device_count()
for i in range(device_count):
    device = paa.get_device_info_by_index(i)
    devices.append(device)
    print(device)

# print(devices)
device_indexes = list(map(lambda d: d['index'], devices))
device_names = tuple(map(lambda d: d['name'], devices))

input_name_choice, form = ui.open_options_dialog(
    'Options',
    'Make a selection for each choice below.',
    tuple(device_names)
)

input_name_value = form['input_name_value']
job_title = form['job_title']
company = form['company']
resume = form['resume'] # potentially add for additional context

ui.set_audio_input_name(input_name_value)
ui.set_job_title_name(job_title)
ui.set_company_name(company)
ui.run_logic(blocking=False)

# selection = input(f"Please select a device ({device_indxs})...\n")
selection = device_indexes[device_names.index(input_name_value)] if input_name_choice=='OK' else None

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

# model = Model(r"vosk-model-small-en-us-0.15")
model = Model(r"vosk-model-en-us-0.42-gigaspeech")
recognizer = KaldiRecognizer(model, sampleRate)
print('vosk model loaded')

stream = paa.open(format=pyaudio.paInt16, channels=1, rate=sampleRate, input=True, input_device_index=selectionInt, frames_per_buffer=8192)
stream.start_stream()

count = 0
startTime = datetime.now()
previousTimePassed = datetime.now() - startTime
loopTime = 0


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
def completion_with_backoff(**kwargs):
    return client.chat.completions.create(**kwargs)


def ask_question_oepnai(questions, is_streamed=False):
    questions_text = " ".join(questions)
    response = completion_with_backoff(
        model="gpt-4o",  # Adjust the model name to "gpt-4" or "gpt-3.5-turbo"
        messages=[
            # {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f"You are interviewing for a role at {company} as a {job_title} and you must provide the "
                           f"best answer to the question: {questions_text}. Summarise the answers so they can be "
                           f"displayed on an easy to read prompter. Keep it as short as you can while conveying the "
                           f"important points and explain thought behind answers briefly after."
            }
        ],
        temperature=0.5,
        # max_tokens=150,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stream=is_streamed
    )
    if is_streamed:
        return response

    try:
        response_text = response["choices"][0]["text"]
    except LookupError:
        response_text = "Couldn't find an answer."

    # print(response_text)
    return response_text


def code_solve_screenshot_openai():
    im = ImageGrab.grab()
    im.save("fullscreen.png")

    with open("fullscreen.png", "rb") as image_file:
        img_str = base64.b64encode(image_file.read()).decode('utf-8')

    prompt = "Do you see a coding challenge on this page and can you solve it? If not return #nochallenge."

    response = client.chat.completions.create(
        model="gpt-4o",
        stream=True,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_str}",
                        },
                    },
                ],
            }
        ],
    )

    os.path.exists("fullscreen.png") and os.remove("fullscreen.png")

    return response


def punctuation_readable(punctuated):
    for punctuation in PUNCTUATION_VOCABULARY:
        punctuated = punctuated.replace(f" {punctuation}", punctuation[0:1])
    return punctuated


# async def process_text_questions(input_text):
def process_text_questions(input_text):
    question = input_text.lower()
    punctuated = punctuate_return(*init_args, f"{question} this is the way")
    punctuated_replaced = punctuation_readable(punctuated)
    # print(punctuated)
    punctuated_replaced_tool_corrected = tool.correct(punctuated_replaced)
    questions = list(filter(lambda s: s[-1]=='?', sent_tokenize(punctuated_replaced_tool_corrected)))
    # question = word_tokenize(question)

    if len(questions) > 0:
        # print(f"\nQuestions1: {questions}")
        ui.set_questions(f"{' '.join(questions)}")
        ui.run_logic(blocking=False)
        answers = ask_question_oepnai(questions, True)
        if ui.show_prompt_window:
            # ui.open_prompt_window('Teleprompter', answers)
            ui.open_prompt_window2('Teleprompter', answers)
        report = []
        for resp in answers:
            if resp.choices and resp.choices[0].delta:
                stream_text = resp.choices[0].delta.content if resp.choices[0].delta.content else ''
                report.append(stream_text)
                result = "".join(report).strip()
                result = result.replace("\n", "")
                # print(f"\r{result}", end='')
                ui.set_answers(f"{result}")
                ui.run_logic(blocking=False)
        # answers = ask_question_oepnai(questions)
        # new_line = '\n'
        # print(f"Answers1: {answers.replace(new_line, '')}")

    # if any(x in question[0] for x in question_words):
    #     print(f"Question2: {textCorrected}?")
    # else:
    #     print("This is not a question!")


while True:
    data = stream.read(1024, exception_on_overflow=False)
    # clip = pc.paste()
    # if clip:
    #     ui.set_tool_detected_text(clip)
    loopTime = (datetime.now() - startTime - previousTimePassed).microseconds / 1000
    # print(f"{loopTime} loop time")
    previousTimePassed = datetime.now() - startTime
    if len(data)==0:
        break
    if recognizer.AcceptWaveform(data):
        resultText = recognizer.Result()
        resultJson = json.loads(resultText)
        if len(resultJson['text']) > 0:
            text = resultJson['text']
            # print(f"{text}, l: {len(text)}")

            # asyncio.run(process_text_questions(text))
            process_text_questions(text)

            if resultJson['text']=='exit':
                quit()
    else:
        resultText = recognizer.PartialResult()
        resultJson = json.loads(resultText)
        partialText = resultJson['partial']
        if len(partialText) > 0:
            # punctuated = punctuate_return(*init_args, partialText)
            # punctuated_replaced = punctuation_readable(punctuated)
            # print(partialText)
            # print(f"\r{partialText}", end='')
            # print(f"\r{punctuated_replaced}", end='')
            ui.print_console(f"{partialText}")

    if ui.run_code_solver:
        ui.run_code_solver = False
        response = code_solve_screenshot_openai()
        ui.open_prompt_window2('Code Solver', response)


    if ui.run_logic(blocking=False):
        break
