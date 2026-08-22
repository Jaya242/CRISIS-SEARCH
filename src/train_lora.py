"""
LoRA fine-tuning: freeze DistilBERT's weights, train only small low-rank
adapter matrices injected into attention layers.
Run: python -m src.train_lora

Produces a FT-vs-LoRA comparison: accuracy, F1, trainable params, time.
"""

import argparse
import os
import time

import torch
from torch.utils.data import DataLoader
from transformers import DistilBertTokenizerFast, get_linear_schedule_with_warmup
from peft import LoraConfig, get_peft_model
from sklearn.metrics import accuracy_score, f1_score

from src.data import load_liar
from src.model import CredibilityClassifier
from src.train import LiarDataset, evaluate, DEVICE


def count_trainable_params(model) -> tuple[int, int]:
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    return trainable, total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-4)  # LoRA typically wants a higher LR
    parser.add_argument("--max_len", type=int, default=64)
    parser.add_argument("--warmup_ratio", type=float, default=0.06)
    parser.add_argument("--ckpt_dir", type=str, default="checkpoints")
    parser.add_argument("--lora_r", type=int, default=8)
    parser.add_argument("--lora_alpha", type=int, default=16)
    args = parser.parse_args()

    os.makedirs(args.ckpt_dir, exist_ok=True)

    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

    train_df = load_liar("train")
    val_df = load_liar("validation")

    train_ds = LiarDataset(train_df, tokenizer, args.max_len)
    val_ds = LiarDataset(val_df, tokenizer, args.max_len)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    # --- Build base model, then wrap with LoRA ---
    base_model = CredibilityClassifier().to(DEVICE)

    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_lin", "v_lin"],  # attention query/value projections
        lora_dropout=0.05,
        bias="none",
        # classifier head + this custom wrapper isn't a standard HF task class,
        # so we mark the linear classifier as trainable too (not frozen),
        # since LoRA alone only touches DistilBERT's attention matrices.
        modules_to_save=["classifier"],
    )

    model = get_peft_model(base_model, lora_config)
    model.to(DEVICE)

    trainable, total = count_trainable_params(model)
    print(f"\n=== LoRA setup ===")
    print(f"r={args.lora_r}, alpha={args.lora_alpha}, target_modules=['q_lin', 'v_lin']")
    print(f"Trainable params: {trainable:,} / {total:,} ({100 * trainable / total:.2f}%)\n")

    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=args.lr
    )
    # Create an AdamW optimizer that will update only the model parameters with requires_grad=True, using the learning rate stored in args.lr.

    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(total_steps * args.warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )

    loss_fn = torch.nn.CrossEntropyLoss()
    #to measure how wrong the model is
    best_val_acc = 0.0
    start_time = time.time()
    # record when training started

    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        for batch in train_loader:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["label"].to(DEVICE)

            optimizer.zero_grad()
            #Clear the gradients from the previous batch before calculating new ones.
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
            ckpt_path = os.path.join(args.ckpt_dir, "best_model_lora.pt")
            torch.save(model.state_dict(), ckpt_path)
            print(f"  -> new best ({val_acc:.4f}), saved to {ckpt_path}")

    elapsed = time.time() - start_time

    # --- Final eval for F1, to complete the comparison table ---
    model.eval()
    preds, labels = [], []
    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            logits = model(input_ids, attention_mask)
            preds.extend(logits.argmax(dim=-1).cpu().tolist())
            labels.extend(batch["label"].tolist())
    f1_per_class = f1_score(labels, preds, average=None)

    print(f"\nTraining done. Best val_acc={best_val_acc:.4f}")
    print(f"Training time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"F1 per class [not_credible, credible]: {f1_per_class}")

    print("\n=== FT vs LoRA comparison row (fill FT row from Day 1) ===")
    print(f"| LoRA | acc={best_val_acc:.4f} | f1={f1_per_class} | "
          f"trainable_params={trainable:,} | time={elapsed/60:.1f}min |")


if __name__ == "__main__":
    main()