import re
import json
import google.generativeai as genai
from config.settings import MODEL_NAME, GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)

def gemini_api_llm(user_prompt: str, retries: int = 3) -> dict | None:
    """
    Sends a prompt to the Gemini API and returns the parsed JSON response.

    Args:
        user_prompt (str): Prompt to send to Gemini.
        retries (int): Number of retry attempts on failure.

    Returns:
        dict | None: Parsed response or None on failure.
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
    except Exception as e:
        print(f"[ERROR] Error al cargar el modelo '{MODEL_NAME}': {e}")
        return None

    try:
        response = model.generate_content(user_prompt)
        content = response.text

        match = re.search(r"```(?:json)?\n(.*?)```", content, re.DOTALL)
        json_str = match.group(1) if match else content

        return json.loads(json_str.replace('```json\n', '').replace('\n', '').replace('`', ''))
    except Exception as e:
        print(f"[ERROR] Fallo al generar/parsing respuesta: {e}")
        if retries > 0:
            print("[INFO] Reintentando...")
            return gemini_api_llm(user_prompt, retries - 1)
        return None
