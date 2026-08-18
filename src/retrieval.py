"""
Retrieval: embed the corpus with MiniLM, retrieve top-k by cosine
similarity to a query. Embeddings cached to disk so we never
re-embed the corpus at query time.
"""

import json
import os

import numpy as np
from sentence_transformers import SentenceTransformer

CORPUS_PATH = "data/corpus.json"
EMBEDDINGS_PATH = "data/corpus_embeddings.npy"
MODEL_NAME = "all-MiniLM-L6-v2"

def load_corpus(path: str = CORPUS_PATH) -> list[dict]:
    with open(path, "r") as f:
        return json.load(f)


def embed_corpus(corpus: list[dict], model: SentenceTransformer) -> np.ndarray:
    texts = [f"{a['title']}. {a['text']}" for a in corpus]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return embeddings


def get_or_build_embeddings(corpus: list[dict], model: SentenceTransformer,
                             cache_path: str = EMBEDDINGS_PATH) -> np.ndarray:
    if os.path.exists(cache_path):
        print(f"Loading cached embeddings from {cache_path}")
        return np.load(cache_path)
    print("No cache found — embedding corpus now...")
    embeddings = embed_corpus(corpus, model)
    np.save(cache_path, embeddings)
    print(f"Saved embeddings to {cache_path}")
    return embeddings


def cosine_similarity(query_vec: np.ndarray, corpus_vecs: np.ndarray) -> np.ndarray:
    query_norm = query_vec / np.linalg.norm(query_vec)
    corpus_norms = corpus_vecs / np.linalg.norm(corpus_vecs, axis=1, keepdims=True)
    return corpus_norms @ query_norm


def retrieve(query: str, corpus: list[dict], corpus_embeddings: np.ndarray,
             model: SentenceTransformer, top_k: int = 5) -> list[dict]:
    query_vec = model.encode(query, convert_to_numpy=True)
    sims = cosine_similarity(query_vec, corpus_embeddings)
    top_indices = np.argsort(sims)[::-1][:top_k]
    results = []
    for idx in top_indices:
        result = dict(corpus[idx])
        result["similarity"] = float(sims[idx])
        results.append(result)
    return results


if __name__ == "__main__":
    model = SentenceTransformer(MODEL_NAME)
    corpus = load_corpus()
    corpus_embeddings = get_or_build_embeddings(corpus, model)

    test_queries = [
        "wildfire evacuation Napa",
        "earthquake warning Japan right now",
        "history of earthquakes in Japan",
        "hurricane landfall Gulf Coast",
        "vaccine microchip conspiracy",
    ]

    for q in test_queries:
        print(f"\n=== Query: '{q}' ===")
        results = retrieve(q, corpus, corpus_embeddings, model, top_k=5)
        for r in results:
            print(f"  [{r['similarity']:.3f}] {r['title']} ({r['source']}, {r['publish_date']})")