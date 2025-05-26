import os
from config.settings import PROMPTS_FOLDER

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