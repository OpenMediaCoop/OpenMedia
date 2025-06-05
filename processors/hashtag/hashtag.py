from transformers import pipeline
import unicodedata
import re

# Cargar pipeline de generación de keyphrases
extractor = pipeline("text2text-generation", model="ml6team/keyphrase-extraction-t5-small-inspec")

def normalizar_a_hashtag(frase: str) -> str:
    # Quitar tildes y acentos
    nfkd = unicodedata.normalize('NFKD', frase)
    sin_acentos = "".join([c for c in nfkd if not unicodedata.combining(c)])
    
    # Quitar caracteres especiales y unir en formato hashtag
    sin_simbolos = re.sub(r"[^a-zA-Z0-9\s]", "", sin_acentos)
    hashtag = "#" + "".join(sin_simbolos.strip().split())
    return hashtag.lower()

def generar_hashtags(texto: str, max_hashtags: int = 5):
    salida = extractor(texto, max_length=32, clean_up_tokenization_spaces=True)[0]['generated_text']
    
    # Separar keyphrases por coma
    keyphrases = [k.strip() for k in salida.split(',') if k.strip()]
    
    # Convertir a hashtags
    hashtags = [normalizar_a_hashtag(k) for k in keyphrases[:max_hashtags]]
    return hashtags
