import os
import time
import torch
import whisper
from collections import deque
from transformers import WhisperTokenizer

from pipeline.classifier import gemini_api_llm
from pipeline.utils import move_audio_file, is_valid_text
from pipeline.transcriber import update_context, get_actual_context
from config.prompts_loader import load_prompts
from config.settings import RECORD_FOLDER, DESTINATION_FOLDER, WHISPER_MODEL, AUDIO_DURATION, MAX_SILENT_ITERS

def real_time_analyzer(extension: str = ".mp3") -> None:
    """
    Continuously monitors a directory for new audio files, transcribes them,
    manages token context, and uses a classification LLM to generate responses.

    Args:
        extension (str): The audio file extension to monitor (default: ".mp3").

    Returns:
        None
    """
    prompts = load_prompts()
    model = whisper.load_model(WHISPER_MODEL)
    tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-base")
    context_tokens = deque()
    empty_text_counter = 0
    
    try:
        while True:
            archivos = [f for f in os.listdir(RECORD_FOLDER) if f.endswith(extension) and os.path.isfile(os.path.join(RECORD_FOLDER, f))]
            archivos = sorted(archivos)
            if len(archivos) > 0:
                for archivo in archivos:
                    file_path = os.path.join(RECORD_FOLDER, archivo)
                    try:

                        texto_transcrito = model.transcribe(file_path, language="es")
                        move_audio_file(file_path, DESTINATION_FOLDER)
                        print("*"*100,f"\n[INFO]\t\t Archivo transcrito: {archivo}")
                        if not is_valid_text(texto_transcrito['text']):
                            empty_text_counter += 1
                            if empty_text_counter >= MAX_SILENT_ITERS and len(context_tokens) > 0:
                                tokens_a_eliminar = min(10, len(context_tokens))
                                for _ in range(tokens_a_eliminar):
                                    context_tokens.popleft()
                            print(f"[INFO]\t\t Texto transcrito no válido:'{texto_transcrito['text']}'")
                            print(f"[CONTEXT]\t {get_actual_context(context_tokens,tokenizer)}")
                            continue
                        else:
                            empty_text_counter = 0
                            print(f"[WHISPER]\t {texto_transcrito['text']}")
                        
                        context_tokens = update_context(texto_transcrito['text'],context_tokens,tokenizer)
                        context_tokens_str = get_actual_context(context_tokens,tokenizer)
                        print(f"[CONTEXT]\t {context_tokens_str}")
                        
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
                        print(f"[ERROR]\t\t Error en {archivo}: {e}")
                        continue
            else:
                print("*"*100,"\n[INFO]\t\t No hay archivos. Esperando...")
                time.sleep(AUDIO_DURATION)
    except KeyboardInterrupt:
        print("\n[INFO]\t\t Proceso interrumpido por el usuario.")
    finally:
        del model
        torch.cuda.empty_cache()