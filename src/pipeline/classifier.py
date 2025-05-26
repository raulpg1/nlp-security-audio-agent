import os
import json
import google.generativeai as genai
from config.settings import MODEL_NAME, GOOGLE_API_KEY


def gemini_api_llm(user_prompt: str) -> dict | None:
    """
    Sends a prompt to the Gemini API and parses the returned JSON-like response.

    Args:
        user_prompt (str): Full prompt string to send to the generative model.

    Returns:
        dict | None: Parsed JSON dictionary from the model response, or None if an error occurred.
    """
    genai.configure(api_key=GOOGLE_API_KEY)
    try:
        model = genai.GenerativeModel(MODEL_NAME)
    except Exception as e:
        print(f"Error al cargar el modelo '{MODEL_NAME}': {e}\n Asegúrate de que el modelo esté disponible en tu región y que tu API Key sea válida.")
        exit()
    try:
        response = model.generate_content(user_prompt)
        return json.loads(response.text.replace('```json\n', '').replace('\n', '').replace('`', ''))
    except Exception as e:
        print(f"\n¡Ocurrió un error al generar la respuesta!: {e}\n Posibles razones: límites de uso excedidos, API Key inválida, o problemas de conexión.")
