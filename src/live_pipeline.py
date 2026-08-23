"""
Live pipeline: query -> crisis detector -> live news fetch -> live embed
+ live credibility scoring -> ranker -> top k.

Unlike pipeline.py (which uses the cached 80-article corpus), this fetches
real, current articles per query. Embeddings and credibility scores can't
be cached here since content is unknown ahead of time — computed live,
every query. This is the direct trade-off against pipeline.py's design.
"""
import os

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import DistilBertTokenizerFast

from src.crisis_detector import detect_urgency
from src.freshness import freshness_score
from src.live_retrieval import fetch_live_articles
from src.model import CredibilityClassifier
from src.publisher_trust import (
    CLASSIFIER_WEIGHT,
    PRIOR_WEIGHT,
    get_publisher_trust,
)
from src.ranker import WEIGHT_PROFILES

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_embed_model = None
_tokenizer = None
_classifier = None

CKPT_PATH = os.getenv("SIGNAL_CKPT_PATH", "checkpoints/best_model.pt")


def _lazy_init():
    global _embed_model, _tokenizer, _classifier
    if _embed_model is None:
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        _tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
        _classifier = CredibilityClassifier().to(DEVICE)
        _classifier.load_state_dict(torch.load(CKPT_PATH, map_location=DEVICE))
        _classifier.eval()


def _score_credibility(text: str) -> float:
    enc = _tokenizer(text, padding="max_length", truncation=True,
                      max_length=64, return_tensors="pt")
    input_ids = enc["input_ids"].to(DEVICE)
    attention_mask = enc["attention_mask"].to(DEVICE)
    with torch.no_grad():
        logits = _classifier(input_ids, attention_mask)
        probs = torch.softmax(logits, dim=-1)
    return probs[0][1].item()


def run_pipeline_live(query: str, top_k: int = 5, fetch_n: int = 15) -> dict:
    _lazy_init()

    mode = detect_urgency(query)
    weights = WEIGHT_PROFILES[mode]

    articles = fetch_live_articles(query, max_results=fetch_n)
    if not articles:
        return {"mode": mode, "results": [], "error": "No live results found."}

    query_vec = _embed_model.encode(query, convert_to_numpy=True)
    texts = [f"{a['title']}. {a['text']}" for a in articles]
    article_vecs = _embed_model.encode(texts, convert_to_numpy=True)

    query_norm = query_vec / np.linalg.norm(query_vec)
    article_norms = article_vecs / np.linalg.norm(article_vecs, axis=1, keepdims=True)
    similarities = article_norms @ query_norm

    scored = []
    for article, R in zip(articles, similarities):
        classifier_C = _score_credibility(f"{article['title']}. {article['text']}")
        publisher_C = get_publisher_trust(article.get("source", ""))
        C = PRIOR_WEIGHT * publisher_C + CLASSIFIER_WEIGHT * classifier_C
        F = freshness_score(article["publish_date"])

        score = weights["w_r"] * R + weights["w_c"] * C + weights["w_f"] * F

        scored.append({
            **article,
            "final_score": float(score),
            "breakdown": {
                "relevance": float(R),
                "credibility": float(C),
                "credibility_prior": float(publisher_C),
                "credibility_classifier": float(classifier_C),
                "freshness": F,
                "weights_used": weights,
            },
        })

    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return {"mode": mode, "results": scored[:top_k]}


if __name__ == "__main__":
    test_queries = [
        "India earthquake 2015",
        "wildfire evacuation right now",
    ]
    for q in test_queries:
        output = run_pipeline_live(q)
        print(f"\n=== Query: '{q}' | Mode: {output['mode']} ===")
        for r in output["results"]:
            b = r["breakdown"]
            print(f"  [{r['final_score']:.3f}] {r['title']} "
                  f"(R={b['relevance']:.2f} C={b['credibility']:.2f} F={b['freshness']:.2f}) — {r['source']}")