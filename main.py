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

# Import services
import openai_service
import audio_service # Add import
import intent_service # Add import

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
stop_keyboard_event = multiprocessing.Event() # Add event for keyboard process

# --- Audio Listener Thread Function moved to audio_service.py ---


count = 0
startTime = datetime.now()
previousTimePassed = datetime.now() - startTime
loopTime = 0


# Renamed from process_text_questions
def process_intent(input_text, intent_result, company_context, job_title_context):
    """Processes the recognized text based on its detected intent."""
    # Correct the original input text
    corrected_text = tool.correct(input_text).strip()
    formatted_text = corrected_text # Default

    # Format based on intent
    if intent_result.get('has_question'):
        if not corrected_text.endswith('?'):
            formatted_text = corrected_text + '?'
    elif intent_result.get('is_action_request'):
        # Add a period for action requests for better LLM prompting
        if not corrected_text.endswith('.'):
             formatted_text = corrected_text + '.'
    # else: # Neither question nor request - could add specific handling later if needed
        # formatted_text remains corrected_text

    # Update UI (consider renaming ui.set_questions later if confusing)
    ui.set_questions(formatted_text) # Using existing UI element for now
    ui.run_logic(blocking=False)

    # Call service function, passing the single formatted text in a list
    answers = openai_service.ask_question_openai([formatted_text], company_context, job_title_context, True)

    if answers: # Check if service call succeeded
        if ui.show_prompt_window:
            ui.update_prompt_window('Teleprompter', answers) # Use updated method
        else:            
            report = []
            # Correct indentation for the loop below
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
        args=(keyboard_results_queue, stop_keyboard_event), # Pass stop event
        daemon=True # Keep as daemon for now, might change if issues persist
    )
    keyboard_process.start()

    audio_thread = threading.Thread(
        target=audio_service.audio_listener_thread, # Use function from audio_service
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
                        ui.run_code_solver = True
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
                    elif shortcut_id == 'action_toggle_prompter':
                        print("Toggle prompter action triggered.")
                        # Toggle the state
                        ui.show_prompt_window = not ui.show_prompt_window
                        # Update the button image
                        ui._InterviewGUI__window['prompter'].update(image_data=gui.TOGGLE_BTN_ON if ui.show_prompt_window else gui.TOGGLE_BTN_OFF)
                        # Update the button metadata (important for the button's own logic)
                        ui._InterviewGUI__window['prompter'].metadata["graphic_off"] = not ui.show_prompt_window
                        # Show or hide the window
                        if ui.show_prompt_window:
                            ui.show_prompt_window_method()
                        else:
                            ui.hide_prompt_window()
                        ui.run_logic(blocking=False) # Update GUI immediately

                if should_exit:
                    break # Exit main while loop

            # Check Audio Results Queue
            try:
                audio_result = audio_results_queue.get_nowait()
                if audio_result['type'] == 'final':
                    text = audio_result['text']
                    print(f"Final text received: {text}")

                    # Analyze intent before processing
                    intent_result = intent_service.analyse_text_intent(text)
                    print(f"Intent analysis: {intent_result}") # Debug print

                    if intent_result:
                        # Only process if it's likely a question for the interview context
                        # Process if it's a question OR an action request
                        if intent_result.get('has_question') or intent_result.get('is_action_request'):
                            print(f"Intent detected as {'question' if intent_result.get('has_question') else 'action request'}, processing...")
                            # Call the renamed function and pass the intent result
                            process_intent(text, intent_result, company, job_title)
                        # elif intent_result.get('is_action_request'): # Combined above
                        #     print(f"Intent detected as action request (verb: {intent_result.get('action_verb')}). Processing...")
                        #     process_intent(text, intent_result, company, job_title)
                        else:
                            print("Intent not detected as question or known action. Ignoring.")

                    # Check for exit command separately
                    if text.strip().lower() == 'exit':
                        print("Exit command received.")
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
                    ui.update_prompt_window('Code Solver', response) # Use updated method
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

        # Stop keyboard process gracefully
        if 'keyboard_process' in locals() and keyboard_process.is_alive():
            print("Signaling keyboard listener process to stop...")
            stop_keyboard_event.set() # Signal the process to exit its loop
            keyboard_process.join(timeout=2) # Wait for the process to finish
            if keyboard_process.is_alive():
                print("Warning: Keyboard process did not exit cleanly after signaling. Terminating...")
                keyboard_process.terminate() # Force terminate if join times out
                keyboard_process.join(timeout=1) # Wait briefly for termination

        # Cleanup PyAudio instance
        paa.terminate()
        print("Application finished.")
# --- End Main Execution Block ---
