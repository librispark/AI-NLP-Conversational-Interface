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
# OpenAI, tenacity, configparser moved to openai_service
import pyscreenshot as ImageGrab # Still needed here for calling the service function
import asyncio
import pyperclip as pc
import keyboard_shortcuts
import threading
import queue
import multiprocessing
from keyboard_shortcuts import run_keyboard_listener_process

# Import the new service
import openai_service

import gui
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

# Config and client init moved to openai_service


# Queues and Events (defined globally for access by functions/threads/processes)
audio_results_queue = queue.Queue()
stop_audio_event = threading.Event()
keyboard_results_queue = multiprocessing.Queue()

# --- Audio Listener Thread Function ---
def audio_listener_thread(stream, recognizer, results_queue, stop_event):
    """Reads audio stream, performs recognition, and puts results in a queue."""
    print("Audio listener thread started.")
    stream.start_stream()
    while not stop_event.is_set():
        try:
            data = stream.read(1024, exception_on_overflow=False)
            if len(data) == 0:
                # End of stream or error
                print("Audio stream read 0 bytes, stopping audio thread.")
                break
            if recognizer.AcceptWaveform(data):
                resultText = recognizer.Result()
                resultJson = json.loads(resultText)
                if len(resultJson.get('text', '')) > 0:
                    results_queue.put({'type': 'final', 'text': resultJson['text']})
            else:
                resultText = recognizer.PartialResult()
                resultJson = json.loads(resultText)
                partialText = resultJson.get('partial', '')
                if len(partialText) > 0:
                    results_queue.put({'type': 'partial', 'text': partialText})
        except Exception as e:
            print(f"Error in audio thread loop: {e}")
            # Optionally put an error message in the queue or just break
            break # Exit loop on error

    # Cleanup before exiting thread
    try:
        if stream.is_active():
            stream.stop_stream()
        stream.close()
    except Exception as e:
        print(f"Error closing audio stream in thread: {e}")
    print("Audio listener thread finished.")
# --- End Audio Listener Thread Function ---


count = 0
startTime = datetime.now()
previousTimePassed = datetime.now() - startTime
loopTime = 0


# async def process_text_questions(input_text): # Keep async commented out
def process_text_questions(input_text, company_context, job_title_context): # Add context args
    question = input_text.lower()
    corrected_text = tool.correct(question)
    questions = list(filter(lambda s: s[-1]=='?', sent_tokenize(corrected_text)))

    if len(questions) > 0:
        ui.set_questions(f"{' '.join(questions)}")
        ui.run_logic(blocking=False)
        # Call service function, passing context
        answers = openai_service.ask_question_openai(questions, company_context, job_title_context, True)
        if answers and ui.show_prompt_window: # Check if service call succeeded
            ui.open_prompt_window2('Teleprompter', answers)
            report = [] # Moved inside the check to avoid processing if no answers
            for resp in answers:
                if resp.choices and resp.choices[0].delta:
                    stream_text = resp.choices[0].delta.content if resp.choices[0].delta.content else ''
                    report.append(stream_text)
                    result = "".join(report).strip()
                    result = result.replace("\n", "")
                    ui.set_answers(f"{result}")
                    ui.run_logic(blocking=False)
        elif not answers:
             print("Failed to get answers from OpenAI service.") # Optional error feedback


# ==============================================
# ==============================================
# Main Execution Block
# ==============================================
if __name__ == '__main__':
    # --- Application Setup ---
    paa = pyaudio.PyAudio()
    tool = language_tool_python.LanguageTool('en-US')
    print(tool.correct('language tool loaded'))

    devices = []
    device_count = paa.get_device_count()
    for i in range(device_count):
        device = paa.get_device_info_by_index(i)
        devices.append(device)
        print(device)

    device_indexes = list(map(lambda d: d['index'], devices))
    device_names = tuple(map(lambda d: d['name'], devices))

    ui = gui.InterviewGUI()
    ui.run_logic(blocking=False) # Show GUI window

    input_name_choice, form = ui.open_options_dialog(
        'Options',
        'Make a selection for each choice below.',
        tuple(device_names)
    )

    if input_name_choice != 'OK' or not form:
        print("Options dialog cancelled or closed. Exiting.")
        paa.terminate()
        quit()

    input_name_value = form['input_name_value']
    job_title = form['job_title'] # These are now used as context for OpenAI calls
    company = form['company']     # These are now used as context for OpenAI calls
    resume = form['resume']

    ui.set_audio_input_name(input_name_value)
    ui.set_job_title_name(job_title)
    ui.set_company_name(company)
    ui.run_logic(blocking=False)

    selection = device_indexes[device_names.index(input_name_value)]

    try:
        selectionInt = int(selection)
    except (LookupError, TypeError):
        print(f"Error converting selection '{selection}' to int. Exiting.")
        paa.terminate()
        quit()

    if selectionInt not in device_indexes:
        print(f"Selected index {selectionInt} not valid. Exiting.")
        paa.terminate()
        quit()

    selectedDevice = devices[selectionInt]
    sampleRate = int(selectedDevice['defaultSampleRate'])
    print(f"Selection index: {selection}, name: {selectedDevice['name']}")

    model = Model(r"vosk-model-en-us-0.42-gigaspeech")
    recognizer = KaldiRecognizer(model, sampleRate)
    print('vosk model loaded')

    stream = paa.open(format=pyaudio.paInt16, channels=1, rate=sampleRate, input=True, input_device_index=selectionInt, frames_per_buffer=8192)
    # --- End Application Setup ---

    # --- Start Background Processes/Threads ---
    keyboard_process = multiprocessing.Process(
        target=run_keyboard_listener_process,
        args=(keyboard_results_queue,),
        daemon=True
    )
    keyboard_process.start()

    audio_thread = threading.Thread(
        target=audio_listener_thread,
        args=(stream, recognizer, audio_results_queue, stop_audio_event),
        daemon=True
    )
    audio_thread.start()
    # --- End Background Processes/Threads ---

    # --- Main Application Loop ---
    try:
        while True:
            # Check Keyboard Shortcuts Queue
            shortcuts_fired = keyboard_shortcuts.get_triggered_shortcuts(keyboard_results_queue)
            if shortcuts_fired:
                should_exit = False
                for shortcut_id in shortcuts_fired:
                    print(f"Processing shortcut: {shortcut_id}")

                    if shortcut_id == '__EXIT__':
                        print("Exit signal received from keyboard listener.")
                        should_exit = True
                        break # Exit inner shortcut processing loop

                    if shortcut_id == 'action_save':
                        print("Save action triggered (implementation pending).")
                    elif shortcut_id == 'action_copy_clipboard':
                        try:
                            text_to_copy = ui.get_answers()
                            if text_to_copy:
                                pc.copy(text_to_copy)
                                print(f"Copied to clipboard: {text_to_copy[:50]}...")
                            else:
                                print("Nothing to copy from answers field.")
                        except Exception as e:
                            print(f"Error copying to clipboard: {e}")

                if should_exit:
                    break # Exit main while loop

            # Check Audio Results Queue
            try:
                audio_result = audio_results_queue.get_nowait()
                if audio_result['type'] == 'final':
                    text = audio_result['text']
                    print(f"Final text received: {text}") # Keep debug print for now
                    # Pass company and job_title context from main scope
                    process_text_questions(text, company, job_title)
                    if text == 'exit':
                        break # Exit main while loop
                elif audio_result['type'] == 'partial':
                    partialText = audio_result['text']
                    ui.print_console(f"{partialText}")

            except queue.Empty:
                pass # No audio result ready, continue loop

            # Check for GUI actions
            if ui.run_code_solver:
                ui.run_code_solver = False
                # Call service function
                response = openai_service.code_solve_screenshot_openai()
                if response: # Check if service call succeeded
                    ui.open_prompt_window2('Code Solver', response)
                else:
                    print("Code solver screenshot analysis failed.") # Optional error feedback

            # Run GUI event loop check
            if ui.run_logic(blocking=False):
                break # Exit main while loop if GUI closes

    # --- Cleanup ---
    finally:
        print("Main loop exited, initiating cleanup...")
        # Stop audio thread gracefully
        stop_audio_event.set()
        if 'audio_thread' in locals() and audio_thread.is_alive():
            audio_thread.join(timeout=2)
            if audio_thread.is_alive():
                print("Warning: Audio thread did not exit cleanly.")

        # Terminate keyboard process
        if 'keyboard_process' in locals() and keyboard_process.is_alive():
            print("Terminating keyboard listener process...")
            keyboard_process.terminate()
            keyboard_process.join(timeout=1)
            if keyboard_process.is_alive():
                print("Warning: Keyboard process did not terminate cleanly.")

        # Cleanup PyAudio instance
        paa.terminate()
        print("Application finished.")
# --- End Main Execution Block ---
