"""
Composite ranker: combines relevance, credibility, and freshness into
one score per document, using two weight profiles depending on
whether the query was classified as "standard" or "emergency".

Score = w_r * R + w_c * C + w_f * F
r- Relevance
c- Credibility
f- Freshness
"""
import json

from src.retrieval import load_corpus, get_or_build_embeddings, retrieve, cosine_similarity
from src.freshness import freshness_score
from sentence_transformers import SentenceTransformer

CORPUS_SCORES_PATH = "data/corpus_scores.json"

# Two weight profiles — this is the part your plan says to tune yourself
WEIGHT_PROFILES = {
    "standard": {"w_r": 0.75, "w_c": 0.10, "w_f": 0.15},
    "emergency": {"w_r": 0.45, "w_c": 0.25, "w_f": 0.30},
}


def load_credibility_scores(path: str = CORPUS_SCORES_PATH) -> dict:
    with open(path, "r") as f:
        scores = json.load(f)
    return {s["title"]: s["credibility"] for s in scores}


def rank(query: str, corpus: list[dict], corpus_embeddings, model: SentenceTransformer,
         mode: str = "standard", top_k: int = 5) -> list[dict]:
    """
    mode: "standard" or "emergency" — determines which weight profile is used.
    Returns top_k results, each with a full score breakdown for
    "why did this rank here?" explanations.
    """
    weights = WEIGHT_PROFILES[mode]
    credibility_scores = load_credibility_scores()

    # Get similarity for every article (top_k = full corpus size here,
    # since we need R for every doc before applying weights)
    candidates = retrieve(query, corpus, corpus_embeddings, model, top_k=len(corpus))

    scored = []
    for article in candidates:
        R = article["similarity"]
        C = credibility_scores.get(article["title"], 0.5)  # default if missing
        F = freshness_score(article["publish_date"])

        score = weights["w_r"] * R + weights["w_c"] * C + weights["w_f"] * F

        scored.append({
            **article,
            "final_score": score,
            "breakdown": {
                "relevance": R, "credibility": C, "freshness": F,
                "weights_used": weights,
            },
        })

    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    model = SentenceTransformer("all-MiniLM-L6-v2")
    corpus = load_corpus()
    corpus_embeddings = get_or_build_embeddings(corpus, model)

    query = "wildfire evacuation Napa"

    for mode in ["standard", "emergency"]:
        print(f"\n=== Mode: {mode} (weights: {WEIGHT_PROFILES[mode]}) ===")
        results = rank(query, corpus, corpus_embeddings, model, mode=mode, top_k=5)
        for r in results:
            b = r["breakdown"]
            print(f"  [{r['final_score']:.3f}] {r['title']} "
                  f"(R={b['relevance']:.2f} C={b['credibility']:.2f} F={b['freshness']:.2f})")