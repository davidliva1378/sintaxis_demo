
def limpiar_texto(texto):
    return texto.replace("\n\n", " ").replace("\n", " ").strip()

def normalizar_texto(t):
    import unicodedata
    return unicodedata.normalize("NFKD", t.strip().lower()).encode("ascii", "ignore").decode("utf-8")
