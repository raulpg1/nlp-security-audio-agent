import os
from dotenv import load_dotenv

load_dotenv("../.env")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PROMPTS_FOLDER = os.path.join(BASE_DIR,os.getenv("PROMPTS_FOLDER", "prompts"))
RECORD_FOLDER = os.path.join(BASE_DIR,os.getenv("RECORD_FOLDER", "grabaciones"))
DESTINATION_FOLDER = os.path.join(BASE_DIR,os.getenv("DESTINATION_FOLDER", "procesados"))

MAX_TOKENS = int(os.getenv("MAX_TOKENS"))
MAX_SILENT_ITERS = int(os.getenv("MAX_SILENT_ITERS"))
AUDIO_DURATION = int(os.getenv("AUDIO_DURATION"))

MODEL_NAME = os.getenv("MODEL_NAME")
WHISPER_MODEL = os.getenv("WHISPER_MODEL")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


if not GOOGLE_API_KEY:
    raise ValueError("Falta la clave GOOGLE_API_KEY en el archivo .env")