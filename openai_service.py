import configparser
import base64
import os
from io import BytesIO
from openai import OpenAI
import pyscreenshot as ImageGrab
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

# --- Configuration and Client Initialization ---

config = configparser.ConfigParser()
# Assume config.ini is in the same directory or adjust path as needed
config_path = 'config.ini'
if not os.path.exists(config_path):
    raise FileNotFoundError(f"Configuration file '{config_path}' not found.")

config.read(config_path)

try:
    api_key = config['openapi']['ApiKey']
except KeyError:
    raise KeyError("ApiKey not found in config.ini under [openapi] section.")

if not api_key:
    raise ValueError("ApiKey found in config.ini is empty.")

client = OpenAI(api_key=api_key)
print("OpenAI client initialized.")

# --- API Call Functions ---

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
def completion_with_backoff(**kwargs):
    """Wrapper for OpenAI completion with exponential backoff retry."""
    return client.chat.completions.create(**kwargs)

def ask_question_openai(questions, company, job_title, is_streamed=False):
    """
    Asks a question to the OpenAI API, formatted for an interview context.

    Args:
        questions (list): A list of question strings.
        company (str): The company name for context.
        job_title (str): The job title for context.
        is_streamed (bool): Whether to stream the response.

    Returns:
        The OpenAI API response object.
    """
    questions_text = " ".join(questions)
    # Ensure company and job_title are provided
    if not company or not job_title:
         print("Warning: Company or job title not provided for OpenAI context.")
         # Handle this case as needed, maybe use default prompt or raise error

    response = completion_with_backoff(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"You are interviewing for a role at {company} as a {job_title} and you must provide the "
                           f"best answer to the question: {questions_text}. Summarise the answers so they can be "
                           f"displayed on an easy to read prompter. Keep it as short as you can while conveying the "
                           f"important points and explain thought behind answers briefly after."
            }
        ],
        temperature=0.5,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stream=is_streamed
    )
    # Note: Streaming responses are returned directly. Non-streaming extraction removed
    # as the caller (main.py) handles the streaming response.
    return response

def code_solve_screenshot_openai():
    """
    Takes a screenshot, sends it to OpenAI (gpt-4o) to check for and solve coding challenges.

    Returns:
        The OpenAI API streaming response object.
    """
    screenshot_filename = "fullscreen_temp.png" # Use a temp name
    try:
        im = ImageGrab.grab()
        im.save(screenshot_filename)

        with open(screenshot_filename, "rb") as image_file:
            img_str = base64.b64encode(image_file.read()).decode('utf-8')

    except Exception as e:
        print(f"Error capturing or encoding screenshot: {e}")
        return None # Indicate error
    finally:
        # Ensure temp file is deleted
        if os.path.exists(screenshot_filename):
            try:
                os.remove(screenshot_filename)
            except Exception as e:
                print(f"Error removing temporary screenshot file: {e}")


    prompt = "Do you see a coding challenge on this page and can you solve it? If not return #nochallenge."

    try:
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
        return response
    except Exception as e:
        print(f"Error calling OpenAI for code solving: {e}")
        return None # Indicate error
