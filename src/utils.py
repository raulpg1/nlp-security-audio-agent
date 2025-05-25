import re
import os
import shutil

def is_valid_text(texto: str) -> bool:
    """
    Validates if the given text is meaningful and should be processed further.

    Args:
        texto (str): Transcribed text.

    Returns:
        bool: True if the text is considered valid, False otherwise.
    """
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


def move_audio_file(origen: str, destino_directorio: str) -> None:
    """
    Moves a file from the source path to the destination directory.

    Args:
        origen (str): Full path to the source file.
        destino_directorio (str): Destination folder where the file will be moved.

    Returns:
        None
    """
    os.makedirs(destino_directorio, exist_ok=True)
    nombre_archivo = os.path.basename(origen)
    destino = os.path.join(destino_directorio, nombre_archivo)
    shutil.move(origen, destino)