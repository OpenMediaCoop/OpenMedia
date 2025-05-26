from sentence_transformers import SentenceTransformer
from functools import lru_cache

@lru_cache(maxsize=1)
def get_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
    return SentenceTransformer(model_name)

def generate_embedding(text: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    model = get_model(model_name)
    return model.encode(text).tolist()