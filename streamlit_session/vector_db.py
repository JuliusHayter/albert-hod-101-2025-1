import os
import pickle
from typing import List
import openai
from dotenv import load_dotenv
import faiss
import numpy as np

load_dotenv()


def load_text_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def split_text_into_chunks(text: str, chunk_size: int = 1000, 
                           overlap: int = 200) -> List[str]:
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks


def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding


def generate_embeddings(text_chunks: List[str]) -> np.ndarray:
    print(f"Génération des embeddings pour {len(text_chunks)} chunks...")
    embeddings = []
    
    for i, chunk in enumerate(text_chunks):
        if (i + 1) % 50 == 0:
            print(f"Traitement du chunk {i + 1}/{len(text_chunks)}")
        embedding = get_embedding(chunk)
        embeddings.append(embedding)
    
    return np.array(embeddings).astype('float32')


def create_vector_database(text_chunks: List[str]) -> tuple:
    embeddings_array = generate_embeddings(text_chunks)
    dimension = embeddings_array.shape[1]
    
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)
    
    print(f"Base de données vectorielle créée avec {index.ntotal} vecteurs")
    return index, dimension


def save_vector_database(index: faiss.Index, chunks: List[str], 
                        dimension: int, index_path: str, 
                        chunks_path: str):
    faiss.write_index(index, index_path)
    with open(chunks_path, 'wb') as f:
        pickle.dump(chunks, f)
    print(f"Base de données sauvegardée dans {index_path}")
    print(f"Chunks sauvegardés dans {chunks_path}")


def process_text_file(text_file: str) -> List[str]:
    print(f"Chargement du fichier {text_file}...")
    text = load_text_file(text_file)
    print("Découpage du texte en chunks...")
    chunks = split_text_into_chunks(text)
    print(f"Nombre de chunks créés: {len(chunks)}")
    return chunks


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY n'est pas définie dans le fichier .env")
    
    text_file = "othello.txt"
    index_path = "othello_index.faiss"
    chunks_path = "othello_chunks.pkl"
    
    chunks = process_text_file(text_file)
    index, dimension = create_vector_database(chunks)
    save_vector_database(index, chunks, dimension, index_path, chunks_path)
    print("Terminé!")


if __name__ == "__main__":
    main()
