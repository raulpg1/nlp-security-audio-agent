import os
import numpy as np
import sounddevice as sd
from pydub import AudioSegment
from datetime import datetime

def record_audio(duration):
    """
    Graba audio desde el micrófono durante un tiempo especificado, lo guarda en formato MP3
    dentro de una carpeta con timestamp, y devuelve la ruta del archivo generado.

    Parámetros:
        duration (float): Duración de la grabación en segundos.

    Retorna:
        str: Ruta completa del archivo de audio MP3 guardado.
    """
    print("[record]\t Grabando un nuevo audio")
    sample_rate = 16000
    channels = 1

    ahora = datetime.now()
    timestamp = ahora.strftime("%Y-%m-%d_%H-%M-%S")

    carpeta_base = "grabaciones"
    os.makedirs(carpeta_base, exist_ok=True)

    archivo = f"{timestamp}_record.mp3"
    ruta_completa = os.path.join(carpeta_base, archivo)
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype='int16')
    sd.wait()

    audio_np = np.array(audio)
    audio_segment = AudioSegment(
        audio_np.tobytes(),
        frame_rate=sample_rate,
        sample_width=audio_np.dtype.itemsize,
        channels=channels
    )

    audio_segment.export(ruta_completa, format="mp3")
    print(f"[record]\t Audio guardado en: {ruta_completa}")
    return ruta_completa

if __name__ == "__main__":
    while True:
        record_audio(30)