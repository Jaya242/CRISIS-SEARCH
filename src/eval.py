"""
Evaluate a trained checkpoint on a split: accuracy, per-class F1,
confusion matrix, full classification report.
Run: python -m src.eval --ckpt checkpoints/best_model.pt --split test
"""

import argparse

import torch
from torch.utils.data import DataLoader
from transformers import DistilBertTokenizerFast
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

from src.data import load_liar
from src.model import CredibilityClassifier
from src.train import LiarDataset, DEVICE


def run_eval(ckpt_path: str, split: str = "test", max_len: int = 64,
             batch_size: int = 32):
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    df = load_liar(split)
    ds = LiarDataset(df, tokenizer, max_len)
    loader = DataLoader(ds, batch_size=batch_size)

    model = CredibilityClassifier().to(DEVICE)
    model.load_state_dict(torch.load(ckpt_path, map_location=DEVICE))
    model.eval()

    preds, labels = [], []
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            logits = model(input_ids, attention_mask)
            preds.extend(logits.argmax(dim=-1).cpu().tolist())
            labels.extend(batch["label"].tolist())

    acc = accuracy_score(labels, preds)
    f1_per_class = f1_score(labels, preds, average=None)
    cm = confusion_matrix(labels, preds)
    report = classification_report(
        labels, preds, target_names=["not_credible", "credible"]
    )

    print(f"\n=== Eval on '{split}' ({len(labels)} examples) ===")
    print(f"Accuracy: {acc:.4f}")
    print(f"F1 per class [not_credible, credible]: {f1_per_class}")
    print(f"\nConfusion matrix (rows=true, cols=pred):\n{cm}")
    print(f"\n{report}")

    return {"accuracy": acc, "f1_per_class": f1_per_class.tolist(), "confusion_matrix": cm.tolist()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", type=str, default="checkpoints/best_model.pt")
    parser.add_argument("--split", type=str, default="test")
    args = parser.parse_args()
    run_eval(args.ckpt, args.split)