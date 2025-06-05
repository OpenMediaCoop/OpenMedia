# download_model.py
from sentence_transformers import SentenceTransformer

# Ruta local donde guardar el modelo
output_path = "./models/paraphrase-multilingual-MiniLM-L12-v2"

print(f"Descargando modelo a: {output_path}")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
model.save(output_path)
print("✅ Descarga completa.")