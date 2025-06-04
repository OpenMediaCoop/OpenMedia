from sentence_transformers import SentenceTransformer
from functools import lru_cache

LLM_SOURCE = "sentence-transformers"

# Diccionario útil con las dimensiones de embedding por modelo
EMBEDDING_DIMENSIONS = {
    f"{LLM_SOURCE}/paraphrase-multilingual-MiniLM-L12-v2": 384,
    f"{LLM_SOURCE}/all-MiniLM-L6-v2": 384,
    f"{LLM_SOURCE}/all-mpnet-base-v2": 768,
    f"{LLM_SOURCE}/paraphrase-MiniLM-L3-v2": 384,
    f"{LLM_SOURCE}/paraphrase-albert-small-v2": 768,
    f"{LLM_SOURCE}/gtr-t5-base": 768,
    f"{LLM_SOURCE}/gtr-t5-large": 1024,
    f"{LLM_SOURCE}/distiluse-base-multilingual-cased-v2": 512,
    f"{LLM_SOURCE}/msmarco-distilbert-base-v3": 768,
    f"{LLM_SOURCE}/multi-qa-MiniLM-L6-cos-v1": 384
}

@lru_cache(maxsize=1)
def get_model(model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2") -> SentenceTransformer:
    return SentenceTransformer(model_name, device="cpu")

def generate_embedding(text: str, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
    model = get_model(model_name)
    return model.encode(text, convert_to_numpy=True).tolist()