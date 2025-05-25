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

load_dotenv("keys.env")


RECORD_FOLDER = os.getenv("RECORD_FOLDER")
DESTINATION_FOLDER = os.getenv("DESTINATION_FOLDER")

MAX_TOKENS = int(os.getenv("MAX_TOKENS"))
ON_HOLD = int(os.getenv("ON_HOLD"))

WHISPER_MODEL = os.getenv("WHISPER_MODEL")
MODEL_NAME= os.getenv("MODEL_NAME")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 

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
    texto = re.sub(r'(.)\1{3,}', r'\1\1\1', texto)
    texto = re.sub(r'\s+', ' ', texto)
    texto = ''.join(c for c in texto if c.isprintable())
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


def es_texto_valido(texto):
    texto = texto.strip()
    if not texto:
        return False
    if not re.search(r'\w', texto):
        return False
    if re.fullmatch(r'(.)\1{5,}', texto):
        return False
    if len(texto.split()) < 2:
        return False
    return True

def mover_archivo(origen, destino_directorio):
    os.makedirs(destino_directorio, exist_ok=True)
    nombre_archivo = os.path.basename(origen)
    destino = os.path.join(destino_directorio, nombre_archivo)
    shutil.move(origen, destino)

def transcribe_and_classify(extension=".mp3"):
    prompts = cargar_prompts()
    model = whisper.load_model(WHISPER_MODEL)
    tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-base")
    context_tokens = deque()

    try:
        while True:
            archivos = [f for f in os.listdir(RECORD_FOLDER) if f.endswith(extension) and os.path.isfile(os.path.join(RECORD_FOLDER, f))]
            archivos = sorted(archivos)
            if len(archivos) > 0:
                for archivo in archivos:
                    ruta = os.path.join(RECORD_FOLDER, archivo)
                    try:
                        texto_transcrito = model.transcribe(ruta, language="es")
                        mover_archivo(ruta, DESTINATION_FOLDER)
                        print("*"*100,f"\n[INFO]\t Archivo transcrito: {archivo}")
                        print(f"[WHISPER]\t {texto_transcrito['text']}")
                        
                        if not es_texto_valido(texto_transcrito['text']):
                            print(f"[INFO] Texto no válido en {archivo}. Saltando...")
                            continue
                        
                        context_tokens = actualizar_contexto(texto_transcrito['text'],context_tokens,tokenizer)
                        context_tokens_str = obtener_contexto_actual(context_tokens,tokenizer)
                        print(f"[TOKENIZER]\t {context_tokens_str}")
                        
                        respuesta_clasificador = gemini_api_llm(f"{prompts['clasificador']} {context_tokens_str}")
                        
                        if respuesta_clasificador:
                            print(f"[GEMINI_CLASS]\t {respuesta_clasificador}")
                            if respuesta_clasificador['categoria'] != "ninguna":
                                respuesta = gemini_api_llm(f"{prompts[respuesta_clasificador['categoria']]} {context_tokens_str}")
                                print(f"[GEMINI_AGENT]\t {respuesta}")
                        else:
                            print("[GEMINI_CLASSIFIER]\t No se obtuvo respuesta del clasificador.")
                            continue
  
                    except Exception as e:
                        print(f"[ERROR]\t Error en {archivo}: {e}")
                        continue
            else:
                print("*"*100)
                print("[INFO] No hay archivos. Esperando...")
                time.sleep(ON_HOLD)
    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario.")
    finally:
        del model
        torch.cuda.empty_cache()


def gemini_api_llm(user_prompt):
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


if __name__ == "__main__":
    transcribe_and_classify()