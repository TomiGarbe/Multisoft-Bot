import re

_UNSUPPORTED_PHRASES = [
    r"\bno s[eé]\b",
    r"\bno tengo (informaci[oó]n|conocimiento|datos)\b",
    r"\bno (puedo|estoy en condiciones de) (ayudarte|responder|contestar)\b",
    r"\bfuera de mi (alcance|conocimiento|contexto|capacidad)\b",
    r"\bno est[aá] en mis capacidades\b",
    r"\bno tengo acceso\b",
    r"\bno cuento con esa informaci[oó]n\b",
    r"\besa informaci[oó]n no est[aá] disponible\b",
    r"\bno (me|es) es posible\b",
    r"\bno (dispongo|cuento con)\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _UNSUPPORTED_PHRASES]

_MIN_RESPONSE_LENGTH = 5


def is_out_of_scope(response: str) -> bool:
    text = response.strip()
    if len(text) < _MIN_RESPONSE_LENGTH:
        return True
    for pattern in _COMPILED:
        if pattern.search(text):
            return True
    return False
