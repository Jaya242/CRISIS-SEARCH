"""
Full pipeline: query -> crisis detector -> retrieval -> ranker -> top 5.
This is the single entry point app.py will call.
"""
from sentence_transformers import SentenceTransformer

from src.crisis_detector import detect_urgency
from src.ranker import rank
from src.retrieval import load_corpus, get_or_build_embeddings

_model = None
_corpus = None
_corpus_embeddings = None


def _lazy_init():
    """
    Loads the MiniLM model, corpus, and embeddings ONCE, the first time
    the pipeline runs — not on every query. Subsequent calls reuse the
    already-loaded objects (module-level globals).
    """
    global _model, _corpus, _corpus_embeddings
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        _corpus = load_corpus()
        _corpus_embeddings = get_or_build_embeddings(_corpus, _model)


def run_pipeline(query: str, top_k: int = 5) -> dict:
    """
    Returns:
        {
            "mode": "standard" | "emergency",
            "results": [ {title, source, publish_date, final_score,
                          breakdown: {relevance, credibility, freshness, weights_used}}, ... ]
        }
    """
    _lazy_init()

    mode = detect_urgency(query)
    results = rank(query, _corpus, _corpus_embeddings, _model, mode=mode, top_k=top_k)

    return {"mode": mode, "results": results}


if __name__ == "__main__":
    test_queries = [
        "wildfire evacuation Napa right now",
        "history of earthquakes in Japan",
    ]
    for q in test_queries:
        output = run_pipeline(q)
        print(f"\n=== Query: '{q}' | Mode: {output['mode']} ===")
        for r in output["results"]:
            print(f"  [{r['final_score']:.3f}] {r['title']}")