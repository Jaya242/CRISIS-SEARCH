# Signal — Crisis-Aware Search Reranker

> Rank news the way a newsroom would — not the way a search engine does.

Signal is a live search reranker that auto-detects whether a query is an **active emergency** or a **standard lookup** and re-weights three signals — relevance, credibility, and freshness — accordingly. Search engines optimize for relevance under the assumption that all queries are equal. They aren't. A person searching *"wildfire evacuation Napa right now"* has different needs than one searching *"history of California wildfires"*, and Signal ranks results with that difference in mind.

**Live demo:** [https://jaya242--signal-ui.modal.run](https://jaya242--signal-ui.modal.run)

---

## Table of contents

1. [What Signal does](#what-signal-does)
2. [How the ranking works](#how-the-ranking-works)
3. [Architecture](#architecture)
4. [Tech stack](#tech-stack)
5. [Repository structure](#repository-structure)
6. [Local installation](#local-installation)
7. [Training the credibility classifier](#training-the-credibility-classifier)
8. [Running the app](#running-the-app)
9. [Deploying to Modal](#deploying-to-modal)
10. [Limitations and next steps](#limitations-and-next-steps)

---

## What Signal does

Given a natural-language query, Signal:

1. **Fetches live news** from Google News RSS (Reuters, AP, BBC, NYT, Guardian, NPR, USGS, NOAA, and hundreds of other publishers).
2. **Classifies the query intent** as `emergency` or `standard` using a keyword-based crisis detector (word-boundary matching, emergency signals win ties — because missing a real emergency is worse than a false alarm).
3. **Scores each article** on three axes:
   - **Relevance** — semantic similarity between the query and article, computed with `sentence-transformers/all-MiniLM-L6-v2`.
   - **Credibility** — a per-article score from a fine-tuned DistilBERT classifier trained on the LIAR2 dataset (75.7% validation accuracy).
   - **Freshness** — exponential time-decay `exp(-age_in_days / 30)`.
4. **Combines the three signals** with mode-specific weights, sorts by the composite score, and returns the top K with a full breakdown of *why each result ranked where it did*.

This is the "reranker" pattern: a fast retriever pulls a candidate set (Google News RSS), and a more careful model reorders them using signals a search engine can't see (source credibility, urgency-adjusted freshness).

## How the ranking works

The composite score is a plain weighted sum:

```
score = w_r · R + w_c · C + w_f · F
```

Where R, C, F ∈ [0, 1] are the three per-article signals. Signal ships two weight profiles:

| Signal          | Weight (Standard) | Weight (Emergency) | Rationale                                                                 |
| --------------- | ----------------- | ------------------ | ------------------------------------------------------------------------- |
| **Relevance**   | 0.75              | 0.45               | Dominant in normal lookups. Still matters in emergencies but less alone.  |
| **Credibility** | 0.10              | 0.25               | Rumor is expensive in a crisis. Trusted publishers weigh more.            |
| **Freshness**   | 0.15              | 0.30               | A three-day-old hurricane article is nearly useless; a history query, no. |

The mode is selected by `src/crisis_detector.py`, which does word-boundary regex matching against two vocabularies (emergency signals: `"right now"`, `"evacuate"`, `"breaking"`, `"warning"`; standard signals: `"history of"`, `"overview"`, `"what is"`, etc.). It's intentionally simple — the interesting engineering is the reranker, not the classifier for it. A Claude-Haiku LLM classifier is stubbed in `crisis_detector.py` as a documented upgrade path.

**Freshness formula.** Age is measured in days from the article's publish date. The score is `exp(-age / 30)`:

| Age (days) | Freshness score |
| ---------- | --------------- |
| 0          | 1.00            |
| 7          | 0.79            |
| 30         | 0.37            |
| 90         | 0.05            |

The `30` constant sets the decay speed — an article halves in freshness every ~21 days.

**Credibility model.** A DistilBERT encoder + dropout + linear head. Trained on LIAR2 (18,369 rows down to 12,520 after dropping the ambiguous "barely-true" and "half-true" labels), binary classification (`credible` vs `not_credible`). One-epoch training reached 75.7% validation accuracy. Also included in `src/train_lora.py`: a LoRA-adapted variant if you want to keep the base model frozen and swap adapters.

## Architecture

```
                          ┌────────────────────────┐
   query "wildfire        │  crisis_detector.py    │  "emergency" or "standard"
   evacuation napa   ──▶  │  (keyword rules)       │  ──┐
   right now"             └────────────────────────┘    │
                                                        │  selects weight profile
                          ┌────────────────────────┐    │
                          │  live_retrieval.py     │    │
   Google News RSS  ────▶ │  fetch_live_articles   │ ──┐│
                          └────────────────────────┘   ││
                                                       ▼▼
                          ┌───────────────────────────────────────┐
                          │             ranker (src/ranker.py)    │
                          │                                       │
                          │   R = MiniLM-L6-v2 cos(query, doc)    │
                          │   C = DistilBERT(finetuned) on doc    │
                          │   F = exp(-age_days / 30)             │
                          │                                       │
                          │   score = w_r·R + w_c·C + w_f·F       │
                          └───────────────────────────────────────┘
                                          │
                                          ▼
                          ┌────────────────────────┐
                          │  Gradio UI (app.py)    │  Top-K results + signal breakdown
                          │  Signal frontend       │
                          └────────────────────────┘
```

## Tech stack

| Layer            | Choice                                     | Why                                                                        |
| ---------------- | ------------------------------------------ | -------------------------------------------------------------------------- |
| Language         | Python 3.11                                | Ecosystem match for the ML libraries used.                                 |
| Deep learning    | PyTorch 2.4 (CPU)                          | Runtime doesn't need a GPU. Small, cheap to deploy.                        |
| Transformers     | `transformers` 4.43                        | DistilBERT for credibility, tokenizer utilities.                           |
| Semantic search  | `sentence-transformers` 3.0 (all-MiniLM-L6-v2) | 90MB embedding model — fast, competitive quality for short news snippets. |
| Fine-tuning      | `peft` (LoRA) — optional path              | Adapter-based fine-tuning if you want to keep the base frozen.             |
| Training data    | LIAR2 (via HuggingFace `datasets`)         | Widely used political-fact-check corpus; 6-way collapsed to binary here.   |
| Retrieval        | Google News RSS                            | No API key, hundreds of publishers, real freshness signal.                 |
| UI               | Gradio 4.44 (Blocks + custom CSS)          | Fast prototyping, mounts cleanly into FastAPI/Modal.                       |
| Serving          | FastAPI + `gr.mount_gradio_app`            | ASGI, plays nicely with Modal's `@modal.asgi_app()`.                       |
| Deployment       | Modal (CPU, scale-to-zero)                 | Serverless, purpose-built for ML inference, generous free tier.            |

## Repository structure

```
factchecker/
├── app.py                     # Gradio Blocks UI (the frontend you see)
├── modal_deploy.py            # Modal deploy config — image, volume, ASGI app
├── requirements.txt           # Local dev dependencies
├── training_log.txt           # Latest classifier training run
│
├── src/
│   ├── crisis_detector.py     # Query intent: "emergency" vs "standard"
│   ├── freshness.py           # exp(-age/30) time-decay
│   ├── ranker.py              # Composite scoring, weight profiles
│   ├── model.py               # DistilBERT + head architecture
│   ├── train.py               # Full fine-tune loop
│   ├── train_lora.py          # LoRA fine-tune loop
│   ├── data.py                # LIAR2 loader (drops barely/half-true labels)
│   ├── retrieval.py           # Cached corpus retrieval (offline eval)
│   ├── live_retrieval.py      # Google News RSS fetcher (production path)
│   ├── pipeline.py            # Offline end-to-end (cached corpus)
│   ├── live_pipeline.py       # Live end-to-end (fetched per-query) — production
│   └── eval.py                # Metrics on held-out set
│
├── data/
│   ├── corpus.json            # Cached 80-article evaluation corpus
│   └── corpus_scores.json     # Per-article credibility scores (cached)
│
├── checkpoints/               # Fine-tuned model weights (gitignored, ~250MB)
│   ├── best_model.pt          # Full fine-tune
│   └── best_model_lora.pt     # LoRA adapter
│
├── scripts/
│   └── score_corpus.py        # One-off: batch-score the cached corpus
│
├── tests/
│   ├── test_freshness.py
│   └── test_ranker.py
│
└── notebooks/                 # Exploratory (empty in git)
```

## Local installation

**Prerequisites:** Python 3.11 or 3.12, git, ~2GB free disk (dependencies + models).

```bash
# 1. Clone the repo
git clone https://github.com/Jaya242/CRISIS-SEARCH.git
cd CRISIS-SEARCH

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate         # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. (First run only) The embedding model downloads on first query.
#    If you want to warm it up:
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

**Note on the credibility checkpoint.** `checkpoints/best_model.pt` is not committed (gitignored, ~250MB). You have two options:

- **Train your own** (see next section) — takes ~10 minutes on a laptop CPU, ~1 minute on a GPU.
- **Skip credibility scoring** — the ranker falls back to `C = 0.5` for every article, so relevance + freshness still work.

## Training the credibility classifier

```bash
# Full fine-tune (updates all DistilBERT weights)
python -m src.train

# Or LoRA fine-tune (freezes DistilBERT, trains low-rank adapters — smaller checkpoint)
python -m src.train_lora
```

Training uses the LIAR2 dataset (auto-downloaded via `datasets`). The default config: 1 epoch, batch size 32, AdamW, lr=2e-5. Expected result: ~76% validation accuracy in ~10 minutes on CPU.

The classifier binary-collapses LIAR2's 6-way labels by dropping the ambiguous middle classes (`barely-true`, `half-true`) and merging the rest into `credible` (`true`, `mostly-true`) vs `not_credible` (`false`, `pants-fire`). This is a modeling choice made to keep the binary crisp — half-truths are their own hard problem.

## Running the app

**Locally:**

```bash
python app.py
```

Prints two URLs:

- `http://127.0.0.1:7860` — local only
- `https://<random>.gradio.live` — public 72-hour tunnel (works when `share=True` is set in `app.py`, which it is by default)

Share the `.gradio.live` URL with anyone. Note this only works while `python app.py` is running.

**On Modal (permanent URL):** see next section.

## Deploying to Modal

Signal is deployed on [Modal](https://modal.com), a serverless platform purpose-built for ML inference. The container scales to zero when idle (no charge) and cold-starts on the first request (~15s). Warm requests are ~2–3s.

**Prerequisites:** a Modal account (free — sign up at [modal.com](https://modal.com)).

```bash
# 1. Install and authenticate
pip install modal
modal setup                                              # opens browser

# 2. Create a persistent volume for the fine-tuned checkpoint
modal volume create signal-checkpoints
modal volume put signal-checkpoints checkpoints/best_model.pt best_model.pt

# 3. Deploy
modal deploy modal_deploy.py
```

Modal prints a URL like `https://<username>--signal-ui.modal.run`. That's your permanent shareable link.

**Cost.** On Modal's free tier ($30/mo credits when a payment method is attached), Signal's realistic monthly cost is well under $1 for portfolio traffic. Breakdown: idle container = $0 (scale-to-zero), per-query compute ≈ $0.0007, image storage ≈ $0.05/mo, volume storage ≈ $0.04/mo.

Config lives in `modal_deploy.py`:

- Image: Debian slim + Python 3.11 + CPU-only torch + pinned transformers/gradio/starlette/fastapi (to dodge a known TemplateResponse signature mismatch between newer starlette and older gradio).
- Container: 2 vCPU, 2GB RAM, scale-to-zero after 10 minutes idle.
- Checkpoint: mounted at `/checkpoints/` from the Modal Volume, accessed via `SIGNAL_CKPT_PATH` env var (set in the image).

## Limitations and next steps

**Honest limitations:**

- **Credibility is source-agnostic per query.** The classifier scores an article's *text*, not the publisher's historical accuracy. A well-written but wrong AP article and a well-written but wrong tabloid article get similar scores. A per-publisher trust prior would help.
- **75.7% classifier accuracy** means ~1 in 4 credibility scores is wrong. For a live newsroom tool this bar is too low; for a demo showing the pattern, it's acceptable. Longer training and a bigger backbone (e.g., DeBERTa-v3) would push it up.
- **Google News RSS gives descriptions, not full text.** Snippet-only credibility scoring is noisier than full-article scoring. A production version would fetch and cache article bodies.
- **The crisis detector is a keyword rule engine.** It handles "right now", "urgent", "evacuate" well and everything else as `standard`. An LLM classifier (Claude Haiku, stub already in code) would catch subtler urgency cues like *"which highway is closed"*.

**Next steps under consideration:**

- Swap the keyword classifier for a Claude-Haiku call, with keyword fallback.
- Add a per-publisher credibility prior (MediaBiasFactCheck-style).
- Cache retrieval results per (query, hour) to cut cold-start latency.
- Log ranking decisions for offline evaluation against a labeled crisis-search benchmark.

---

Built by [@Jaya242](https://github.com/Jaya242). Live at [jaya242--signal-ui.modal.run](https://jaya242--signal-ui.modal.run).
