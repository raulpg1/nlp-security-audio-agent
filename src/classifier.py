import os
import json
import google.generativeai as genai
from dotenv import load_dotenv 

load_dotenv("keys.env")

PROMPTS_FOLDER = os.getenv("PROMPTS_FOLDER")
MODEL_NAME= os.getenv("MODEL_NAME")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 

def load_prompts() -> dict:
    """
    Loads prompt templates from text files in the specified directory.

    Returns:
        dict: A dictionary mapping prompt keys to their corresponding text content.
    """
    prompts = {}
    archivos = {
        "robo_banco": "robo_banco.txt",
        "robo_casa": "robo_casa.txt",
        "asistencia_mayor": "asistencia_mayor.txt",
        "clasificador": "clasificador.txt"
    }

    for clave, nombre_archivo in archivos.items():
        ruta = os.path.join(PROMPTS_FOLDER, nombre_archivo)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                prompts[clave] = f.read()
        except FileNotFoundError:
            print(f"[ERROR] No se encontró el archivo: {ruta}")
            prompts[clave] = ""
        except Exception as e:
            print(f"[ERROR] No se pudo leer {ruta}: {e}")
            prompts[clave] = ""
    return prompts


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
