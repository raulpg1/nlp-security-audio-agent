import os
import re
import time
import json
import torch
import shutil
import whisper
import google.generativeai as genai

from collections import deque
from dotenv import load_dotenv 
from transformers import WhisperTokenizer

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 
MAX_TOKENS = os.getenv("MAX_TOKENS", 50)
INTERVALO = os.getenv("INTERVALO", 3)

def cargar_prompts(directorio="./prompts"):
    prompts = {}
    archivos = {
        "robo_banco": "robo_banco.txt",
        "robo_casa": "robo_casa.txt",
        "asistencia_mayor": "asistencia_mayor.txt",
        "clasificador": "clasificador.txt"
    }

    for clave, nombre_archivo in archivos.items():
        ruta = os.path.join(directorio, nombre_archivo)
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


def limpiar_texto(texto):
    texto = re.sub(r'(.)\1{3,}', r'\1\1\1', texto)  # Limita repeticiones
    texto = re.sub(r'\s+', ' ', texto)             # Normaliza espacios
    texto = ''.join(c for c in texto if c.isprintable())  # Elimina caracteres no imprimibles
    return texto.strip()

def actualizar_contexto(nuevo_texto, context_tokens, tokenizer):
    nuevo_texto = limpiar_texto(nuevo_texto)
    nuevos_tokens = tokenizer.tokenize(nuevo_texto + " ")

    if len(nuevos_tokens) > MAX_TOKENS:
        context_tokens = deque((tok, None) for tok in nuevos_tokens)
    else:
        exceso = max(0, len(context_tokens) + len(nuevos_tokens) - MAX_TOKENS)
        for _ in range(exceso):
            context_tokens.popleft()
        context_tokens.extend((tok, None) for tok in nuevos_tokens)

    return context_tokens

def obtener_contexto_actual(context_tokens, tokenizer):
    solo_tokens = [tok for tok, _ in context_tokens]
    return tokenizer.convert_tokens_to_string(solo_tokens)

def transcribe_and_move_old_audios(extension, intervalo, prompts):
    carpeta = "./grabaciones"
    carpeta_destino = "./grabaciones_procesadas"
    os.makedirs(carpeta_destino, exist_ok=True)

    print(f"[INFO] Iniciando supervisión de: {carpeta}")
    model = whisper.load_model("medium")

    tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-base")
    context_tokens = deque()

    try:
        while True:
            archivos = [f for f in os.listdir(carpeta) if f.endswith(extension) and os.path.isfile(os.path.join(carpeta, f))]
            archivos = sorted(archivos)
            if len(archivos) > 0:
                print(f"[INFO] {len(archivos)} archivos encontrados. Procesando {len(archivos)-1}...")
                for archivo in archivos[:-1]:
                    ruta = os.path.join(carpeta, archivo)
                    try:
                        texto_transcrito = model.transcribe(ruta, language="es")
                        print(f"[WHISPER]\t{archivo} → {texto_transcrito['text']}")
                        
                        
                        context_tokens = actualizar_contexto(texto_transcrito['text'],context_tokens,tokenizer)
                        context_tokens_str = obtener_contexto_actual(context_tokens,tokenizer)
                        print(f"[TOKENIZER]\t{archivo} → {context_tokens_str}")
                        
                        respuesta_clasificador = gemini_api_llm(f"{prompts['clasificador']} {context_tokens_str}")
                        if respuesta_clasificador['categoria'] != "ninguna":
                            respuesta = gemini_api_llm(f"{prompts[respuesta_clasificador['categoria']]} {context_tokens_str}")
                            print(f"[GEMINI]\t{respuesta}")
                        
                    except Exception as e:
                        print(f"[ERROR] Error en {archivo}: {e}")
                        continue

                    destino = os.path.join(carpeta_destino, archivo)
                    shutil.move(ruta, destino)
                    print(f"[INFO] {archivo} movido a {destino}")
            else:
                print("[INFO] No hay archivos. Esperando...")

            time.sleep(intervalo)

    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario.")
    finally:
        del model
        torch.cuda.empty_cache()

def gemini_api_llm(user_prompt):
    genai.configure(api_key=GOOGLE_API_KEY)
    model_name = "gemini-2.0-flash"  # model_name = "gemini-1.5-flash" 
    try:
        model = genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"Error al cargar el modelo '{model_name}': {e}")
        print("Asegúrate de que el modelo esté disponible en tu región y que tu API Key sea válida.")
        exit()
    try:
        response = model.generate_content(user_prompt)
        return json.loads(response.text.replace('```json\n', '').replace('\n', '').replace('`', ''))
    except Exception as e:
        print(f"\n¡Ocurrió un error al generar la respuesta!: {e}")
        print("Posibles razones: límites de uso excedidos, API Key inválida, o problemas de conexión.")

if __name__ == "__main__":
    prompts = cargar_prompts()
    transcribe_and_move_old_audios(extension=".mp3", intervalo=INTERVALO, prompts=prompts)