import os
import re
from collections import deque
from transformers import WhisperTokenizer
from config.settings import MAX_TOKENS

def clean_text(texto: str) -> str:
    """
    Cleans the input text by removing excess characters, whitespace, and non-printable symbols.

    Args:
        texto (str): The raw transcribed text.

    Returns:
        str: The cleaned text.
    """
    texto = re.sub(r'(.)\1{3,}', r'\1\1\1', texto)
    texto = re.sub(r'\s+', ' ', texto)
    texto = ''.join(c for c in texto if c.isprintable())
    return texto.strip()


def update_context(nuevo_texto: str, context_tokens: deque, tokenizer: WhisperTokenizer) -> deque:
    """
    Updates the token context with the new transcribed text, respecting a maximum token limit.

    Args:
        nuevo_texto (str): New transcribed and cleaned text.
        context_tokens (deque): Current deque of context tokens.
        tokenizer (WhisperTokenizer): Tokenizer used for encoding text.

    Returns:
        deque: Updated deque with the new tokens.
    """
    nuevo_texto = clean_text(nuevo_texto)
    nuevos_tokens = tokenizer.tokenize(nuevo_texto + " ")

    if len(nuevos_tokens) > MAX_TOKENS:
        context_tokens = deque((tok, None) for tok in nuevos_tokens)
    else:
        exceso = max(0, len(context_tokens) + len(nuevos_tokens) - MAX_TOKENS)
        for _ in range(exceso):
            context_tokens.popleft()
        context_tokens.extend((tok, None) for tok in nuevos_tokens)

    return context_tokens

def get_actual_context(context_tokens: deque, tokenizer: WhisperTokenizer) -> str:
    """
    Converts the current context tokens back into a string.

    Args:
        context_tokens (deque): Token context deque.
        tokenizer (WhisperTokenizer): Tokenizer used to decode tokens.

    Returns:
        str: Decoded string from context tokens.
    """
    solo_tokens = [tok for tok, _ in context_tokens]
    return tokenizer.convert_tokens_to_string(solo_tokens)