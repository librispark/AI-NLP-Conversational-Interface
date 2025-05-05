from pynput import keyboard
import multiprocessing # Add full import
from multiprocessing import Queue as mpQueue
import sys # For flushing output in process
from pynput import keyboard

# Note: Queue is passed in from the main process

def default_action(params):
    print('default_action triggered for:', params)

# Dictionary to track currently pressed keys
active_keys = set()

# Define your shortcuts and their corresponding actions (optional, can be handled in main)
# For now, we just put the shortcut string into the queue
shortcuts = {
    'a+s': 'action_save',  # Example action identifier
    'Key.cmd+s': 'action_save',
    'Key.ctrl+c': 'action_copy_clipboard', # Example
    'Key.shift': 'action_toggle_prompter' # New shortcut for toggling prompter
    # Add more shortcuts as needed
}

def check_shortcut(output_queue): # Accept queue as argument
    """Checks if any defined shortcut combination is currently active."""
    for shortcut, action_id in shortcuts.items():
        required_keys = set(shortcut.split('+'))
        if required_keys.issubset(active_keys):
            print(f'****** shortcut {shortcut} detected ******', flush=True) # Flush output for process
            output_queue.put(action_id)

# --- This is the correct on_press function ---
def on_press(key, output_queue):
    """Callback function for key press events."""
    # --- Add Esc handling here ---
    if key == keyboard.Key.esc:
        print("ESC pressed, sending exit signal...", flush=True)
        output_queue.put('__EXIT__') # Send exit signal on press
        # Listener stop is handled in on_release

    # --- Regular key press logic ---
    try:
        key_str = key.char
    except AttributeError:
        key_str = str(key)

    if key_str not in active_keys:
        active_keys.add(key_str)
        check_shortcut(output_queue)

def on_release(key):
    """Callback function for key release events."""
    try:
        key_str = key.char
    except AttributeError:
        key_str = str(key)

    if key_str in active_keys:
        active_keys.remove(key_str)

    # Special handling for Escape key release to stop the listener
    if key == keyboard.Key.esc:
        print("Stopping listener process on ESC release.", flush=True)
        return False # Returning False stops the pynput listener
    try:
        key_str = key.char
    except AttributeError:
        key_str = str(key)

import time # Import time

    # Note: The actual exit signal ('__EXIT__') is sent on Esc *press* in on_press

def run_keyboard_listener_process(output_queue, stop_event: multiprocessing.Event): # Add stop_event parameter
    """Target function for the keyboard listener process."""
    print("Keyboard listener process started.", flush=True)

    # Wrapper needed to pass the queue to the on_press callback
    def on_press_wrapper(key):
        on_press(key, output_queue)

    # Create the listener instance without 'with'
    listener = keyboard.Listener(on_press=on_press_wrapper, on_release=on_release)
    listener.start()
    print("Keyboard listener running...", flush=True)

    try:
        # Loop checking the stop event instead of just joining
        while not stop_event.is_set() and listener.is_alive():
            time.sleep(0.1) # Prevent busy-waiting
    except Exception as e:
        print(f"Error in keyboard listener process loop: {e}", flush=True)
    finally:
        print("Keyboard listener process stopping...", flush=True)
        if listener.is_alive():
            listener.stop()
        print("Keyboard listener process finished.", flush=True)

# start_shortcut_listener removed (process started in main.py)

def get_triggered_shortcuts(input_queue):
    """Retrieves all triggered shortcuts from the input_queue."""
    shortcuts_fired = []
    while not input_queue.empty():
        try:
            shortcuts_fired.append(input_queue.get_nowait())
        except mpQueue.Empty:
            break # Should not happen, but safety check
    return shortcuts_fired

# Direct execution block for testing this module independently
if __name__ == '__main__':
    import time
    from multiprocessing import Process

    print("Starting keyboard listener process for testing...")
    test_queue = mpQueue()
    # Start the listener as a daemon process
    listener_process = Process(target=run_keyboard_listener_process, args=(test_queue,), daemon=True)
    listener_process.start()

    print("Main test process running. Press shortcuts or Esc to test. Ctrl+C to exit main.")
    try:
        while listener_process.is_alive(): # Keep running while listener is up
            triggered = get_triggered_shortcuts(test_queue)
            if triggered:
                print(f"Main test process received: {triggered}", flush=True)
                if '__EXIT__' in triggered:
                    print("Exit signal received in test.")
                    break # Exit test loop if Esc was pressed
            time.sleep(0.1) # Small sleep to avoid busy-waiting
    except KeyboardInterrupt:
        print("\nCtrl+C detected in main test process.")
    finally:
        print("Cleaning up test process...")
        if listener_process.is_alive():
            # Attempt graceful shutdown first if possible, but terminate is often needed for daemons
            listener_process.terminate()
            listener_process.join(timeout=1)
        print("Test finished.")
