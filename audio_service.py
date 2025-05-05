import pyaudio
import json
import queue
import threading
from vosk import KaldiRecognizer # Keep vosk import specific

# --- Audio Listener Thread Function ---
# Moved from main.py
def audio_listener_thread(stream: pyaudio.Stream, recognizer: KaldiRecognizer, results_queue: queue.Queue, stop_event: threading.Event):
    """
    Reads audio stream from PyAudio, performs speech recognition using Vosk,
    and puts the results (partial or final) into a queue.

    Args:
        stream: The PyAudio input stream.
        recognizer: The initialized Vosk KaldiRecognizer.
        results_queue: The queue to put recognition results into.
                       Results are dicts: {'type': 'partial'|'final', 'text': str}
        stop_event: A threading.Event to signal when the thread should stop.
    """
    print("Audio listener thread started.")
    try:
        stream.start_stream()
        print("Audio stream started.")
        while not stop_event.is_set():
            try:
                # Read data from the stream
                data = stream.read(1024, exception_on_overflow=False)
                if len(data) == 0:
                    # Should not happen with a live stream unless it closes unexpectedly
                    print("Audio stream read 0 bytes, stopping audio thread.")
                    break

                # Process data with Vosk
                if recognizer.AcceptWaveform(data):
                    result_text = recognizer.Result()
                    result_json = json.loads(result_text)
                    final_text = result_json.get('text', '')
                    if len(final_text) > 0:
                        results_queue.put({'type': 'final', 'text': final_text})
                        # print(f"Final: {final_text}") # Optional debug print
                else:
                    result_text = recognizer.PartialResult()
                    result_json = json.loads(result_text)
                    partial_text = result_json.get('partial', '')
                    if len(partial_text) > 0:
                        results_queue.put({'type': 'partial', 'text': partial_text})
                        # print(f"Partial: {partial_text}") # Optional debug print

            except IOError as e:
                # Handle potential stream errors, e.g., buffer overflow if not handled by exception_on_overflow=False
                print(f"IOError in audio thread loop: {e}")
                # Depending on the error, might want to break or continue
            except Exception as e:
                print(f"Unexpected error in audio thread loop: {e}")
                break # Exit loop on unexpected errors

    finally:
        # Cleanup before exiting thread
        print("Audio listener thread cleaning up...")
        try:
            if stream.is_active():
                stream.stop_stream()
                print("Audio stream stopped.")
            stream.close()
            print("Audio stream closed.")
        except Exception as e:
            print(f"Error closing audio stream in thread: {e}")
        print("Audio listener thread finished.")
# --- End Audio Listener Thread Function ---
