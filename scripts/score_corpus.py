"""
Batch-score all corpus articles with the Day-1 credibility classifier.
Runs ONCE, offline — the runtime app never loads the classifier per-query,
it just reads corpus_scores.json.
Run: python scripts/score_corpus.py
"""
import json
import os

import torch
from transformers import DistilBertTokenizerFast

from src.model import CredibilityClassifier
from src.train import DEVICE

CORPUS_PATH = "data/corpus.json"
SCORES_PATH = "data/corpus_scores.json"
CKPT_PATH = "checkpoints/best_model.pt"  # Day-1 full fine-tune checkpoint


def main():
    with open(CORPUS_PATH, "r") as f:
        corpus = json.load(f)

    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

    model = CredibilityClassifier().to(DEVICE)
    model.load_state_dict(torch.load(CKPT_PATH, map_location=DEVICE))
    model.eval()

    scores = []
    with torch.no_grad():
        for article in corpus:
            text = f"{article['title']}. {article['text']}"
            enc = tokenizer(
                text, padding="max_length", truncation=True,
                max_length=64, return_tensors="pt",
            )
            input_ids = enc["input_ids"].to(DEVICE)
            attention_mask = enc["attention_mask"].to(DEVICE)

            logits = model(input_ids, attention_mask)
            probs = torch.softmax(logits, dim=-1)
            credibility_score = probs[0][1].item()  # P(class=1, credible)

            scores.append({
                "title": article["title"],
                "credibility": credibility_score,
            })

    with open(SCORES_PATH, "w") as f:
        json.dump(scores, f, indent=2)

    print(f"Scored {len(scores)} articles -> {SCORES_PATH}")
    print(f"Sample: {scores[0]}")
    print(f"Range: min={min(s['credibility'] for s in scores):.3f}, "
          f"max={max(s['credibility'] for s in scores):.3f}")


if __name__ == "__main__":
    main()
