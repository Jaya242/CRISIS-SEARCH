"""
Training loop: AdamW + linear warmup, save best checkpoint by val accuracy.
Run: python -m src.train
"""
import argparse
import os

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizerFast, get_linear_schedule_with_warmup
from sklearn.metrics import accuracy_score

from src.data import load_liar
from src.model import CredibilityClassifier

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class LiarDataset(Dataset):
    def __init__(self, df, tokenizer, max_len: int = 64):
        self.texts = df["text"].tolist()
        self.labels = df["label"].tolist()
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            padding="max_length",
            truncation=True,
            max_length=self.max_len,
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "label": torch.tensor(self.labels[idx], dtype=torch.long),
        }


def evaluate(model, loader) -> float:
    model.eval()
    preds, labels = [], []
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            logits = model(input_ids, attention_mask)
            preds.extend(logits.argmax(dim=-1).cpu().tolist())
            labels.extend(batch["label"].tolist())
    return accuracy_score(labels, preds)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max_len", type=int, default=64)
    parser.add_argument("--warmup_ratio", type=float, default=0.06)
    parser.add_argument("--ckpt_dir", type=str, default="checkpoints")
    args = parser.parse_args()

    os.makedirs(args.ckpt_dir, exist_ok=True)

    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

    train_df = load_liar("train")
    val_df = load_liar("validation")

    train_ds = LiarDataset(train_df, tokenizer, args.max_len)
    val_ds = LiarDataset(val_df, tokenizer, args.max_len)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    model = CredibilityClassifier().to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(total_steps * args.warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )

    loss_fn = torch.nn.CrossEntropyLoss()
    best_val_acc = 0.0

    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        for batch in train_loader:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["label"].to(DEVICE)

            optimizer.zero_grad()
            logits = model(input_ids, attention_mask)
            loss = loss_fn(logits, labels)
            loss.backward()
            optimizer.step()
            scheduler.step()

            running_loss += loss.item()

        val_acc = evaluate(model, val_loader)
        avg_loss = running_loss / len(train_loader)
        print(f"Epoch {epoch+1}/{args.epochs} | train_loss={avg_loss:.4f} | val_acc={val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            ckpt_path = os.path.join(args.ckpt_dir, "best_model.pt")
            torch.save(model.state_dict(), ckpt_path)
            print(f"  -> new best ({val_acc:.4f}), saved to {ckpt_path}")

    print(f"Training done. Best val_acc={best_val_acc:.4f}")


if __name__ == "__main__":
    main()