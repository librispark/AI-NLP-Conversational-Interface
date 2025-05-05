import spacy

# Load the English spaCy model
try:
    nlp_en = spacy.load("en_core_web_sm")
    print("spaCy 'en_core_web_sm' model loaded.")
except OSError:
    print("spaCy 'en_core_web_sm' model not found.")
    print("Please run: python -m spacy download en_core_web_sm")
    # Depending on requirements, might want to raise an error or exit here
    nlp_en = None # Set to None to handle gracefully later if needed

# List of common filler words in English
# (Reduced list for simplicity, can be expanded)
filler_words_en = {"okay", "um", "uh", "well", "like", "you know", "so"}

# List of interrogative pronouns and auxiliary verbs for English
interrogative_words_en = {"what", "why", "how", "who", "when", "where", "which"}
auxiliary_verbs_en = {
    "can", "could", "will", "would", "shall", "should", "may", "might",
    "do", "does", "did", "is", "are", "was", "were", "am", "be", "being", "been",
    "have", "has", "had" # Added common auxiliaries
}

def remove_filler_words_en(text):
    """Removes common English filler words from text."""
    tokens = text.split()
    # Remove filler words (case-insensitive)
    filtered_tokens = [token for token in tokens if token.lower() not in filler_words_en]
    return " ".join(filtered_tokens)

def detect_intent_en(doc):
    """
    Detects if the English text is likely a question or an action request.

    Args:
        doc (spacy.Doc): The processed spaCy document.

    Returns:
        dict: A dictionary containing intent flags:
              {'text': str, 'has_question': bool, 'is_action_request': bool, 'action_verb': str|None}
    """
    has_question = False
    is_action_request = False
    action_verb = None

    # Basic Question Detection:
    # 1. Check for interrogative words
    # 2. Check if sentence starts with an auxiliary verb
    # 3. Check if sentence ends with a question mark (less reliable with ASR)

    first_token = doc[0]
    last_token = doc[-1]

    # Check for interrogative words
    for token in doc:
        if token.lemma_.lower() in interrogative_words_en:
            has_question = True
            break

    # Check if starts with auxiliary (common in yes/no questions)
    if not has_question and first_token.lemma_.lower() in auxiliary_verbs_en:
        has_question = True

    # Check for ending question mark (might be added by punctuation model later)
    # if last_token.text == '?':
    #     has_question = True

    # Basic Action Request Detection (Imperative):
    # Check if the first token is a base form verb (VB)
    # This is a simple heuristic and might misclassify things.
    if not has_question and first_token.pos_ == "VERB" and first_token.tag_ == "VB":
        is_action_request = True
        action_verb = first_token.lemma_

    return {
        "text": doc.text,
        "has_question": has_question,
        "is_action_request": is_action_request,
        "action_verb": action_verb
    }

def analyse_text_intent(text):
    """
    Analyzes the intent of a piece of English text.

    Args:
        text (str): The input text.

    Returns:
        dict: The intent analysis result, or None if spaCy model not loaded.
    """
    if not nlp_en:
        print("Error: spaCy English model not loaded. Cannot analyze intent.")
        return None

    filtered_text = remove_filler_words_en(text)
    if not filtered_text: # Handle empty string after removing fillers
        return {"text": "", "has_question": False, "is_action_request": False, "action_verb": None}

    doc = nlp_en(filtered_text)
    intent = detect_intent_en(doc)
    return intent

# Example Usage (for testing if run directly)
if __name__ == '__main__':
    test_sentences = [
        "what is the weather today",
        "tell me a joke",
        "um like can you find the capital of France",
        "so write a poem about cats",
        "the sky is blue",
        "exit the program",
        "do you know the time",
        "is this a test",
        "how does this work"
    ]
    for sentence in test_sentences:
        result = analyse_text_intent(sentence)
        print(f"'{sentence}' -> {result}")
