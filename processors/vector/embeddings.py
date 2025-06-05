from sentence_transformers import SentenceTransformer
from functools import lru_cache
from pathlib import Path
import os

BASE_MODEL_DIR = Path(__file__).parent.parent / "models"

@lru_cache(maxsize=1)
def get_model(model_name: str = "") -> SentenceTransformer:
    if os.getenv("ENV") == "dev":
        model_path = BASE_MODEL_DIR / model_name
    else:
        model_path = Path(model_name)
    return SentenceTransformer(str(model_path), device="cpu")

def generate_embedding(text: str, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
    model = get_model(model_name)
    return model.encode(text, convert_to_numpy=True).tolist()


###################
################### Este diccionario contiene los modelos disponibles y sus descripciones
###################
# ###################
# EMBEDDING_DIMENSIONS = {
#     f"{LLM_SOURCE}/paraphrase-multilingual-MiniLM-L12-v2": 384,
#     f"{LLM_SOURCE}/all-MiniLM-L6-v2": 384,
#     f"{LLM_SOURCE}/all-mpnet-base-v2": 768,
#     f"{LLM_SOURCE}/paraphrase-MiniLM-L3-v2": 384,
#     f"{LLM_SOURCE}/paraphrase-albert-small-v2": 768,
#     f"{LLM_SOURCE}/gtr-t5-base": 768,
#     f"{LLM_SOURCE}/gtr-t5-large": 1024,
#     f"{LLM_SOURCE}/distiluse-base-multilingual-cased-v2": 512,
#     f"{LLM_SOURCE}/msmarco-distilbert-base-v3": 768,
#     f"{LLM_SOURCE}/multi-qa-MiniLM-L6-cos-v1": 384
# }