# Signal — Crisis-Aware Search Reranker

> Rank news the way a newsroom would — not the way a search engine does.

Signal is a live search reranker that auto-detects whether a query is an **active emergency** or a **standard lookup** and re-weights three signals — relevance, credibility, and freshness — accordingly. Search engines optimize for relevance under the assumption that all queries are equal. They aren't. A person searching *"wildfire evacuation Napa right now"* has different needs than one searching *"history of California wildfires"*, and Signal ranks results with that difference in mind.

**Live demo:** [https://crisis-search.streamlit.app](https://crisis-search.streamlit.app)

---

## Table of contents

1. [What Signal does](#what-signal-does)
2. [How the ranking works](#how-the-ranking-works)
3. [Architecture](#architecture)
4. [Tech stack](#tech-stack)
5. [Repository structure](#repository-structure)
6. [Local installation](#local-installation)
7. [Training the credibility classifier](#training-the-credibility-classifier)
8. [Deployment](#deployment)
9. [Limitations and next steps](#limitations-and-next-steps)

---

## What Signal does

Given a natural-language query, Signal:

1. **Fetches live news** from Google News RSS (Reuters, AP, BBC, NYT, Guardian, NPR, USGS, NOAA, and hundreds of other publishers).
2. **Classifies the query intent** as `emergency` or `standard` using a keyword-based crisis detector (word-boundary matching, emergency signals win ties — because missing a real emergency is worse than a false alarm).
3. **Scores each article** on three axes:
   - **Relevance** — semantic similarity between the query and article, computed with `sentence-transformers/all-MiniLM-L6-v2` (a bi-encoder, used off-the-shelf).
   - **Credibility** — hybrid score: `0.6 × publisher_prior + 0.4 × classifier`. The publisher prior is a curated reputation table (`src/publisher_trust.py`) covering ~70 outlets; the classifier is a DistilBERT fine-tuned on LIAR2 (75.7% validation accuracy). The blend fixes a real problem — LIAR2 is political-claim data, so on news headlines the classifier's output clusters low. Combining it with a per-publisher prior restores the source-level signal it can't recover from text alone.
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

**Credibility model.** Two components combined:

1. **Publisher prior** — a hand-curated reputation table in `src/publisher_trust.py` covering ~70 outlets (wire services, mainstream, state media, tabloids). Scores are informed by widely-cited factuality assessments (Ad Fontes, Media Bias/Fact Check, NewsGuard). Unknown publishers fall back to a slightly-above-neutral default of 0.55. This table is a hypothesis, not a fitted result.

2. **Text classifier** — DistilBERT encoder + dropout + linear head. Trained on LIAR2 (18,369 rows down to 12,520 after dropping the ambiguous "barely-true" and "half-true" labels), binary classification (`credible` vs `not_credible`). One-epoch training reached 75.7% validation accuracy. A LoRA-adapted variant is in `src/train_lora.py`.

**Blend:** `final_credibility = 0.6 · publisher_prior + 0.4 · classifier_score`. This is the honest fix for a real domain mismatch — LIAR2 was politicians' claims, not news headlines, so on this data the classifier is out of distribution and its output clusters low (0.01–0.10). The publisher prior is what stops NPR from ranking below BuzzFeed on the same query, which the pure-classifier version did.

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
                          │   C = 0.6·prior + 0.4·classifier      │
                          │   F = exp(-age_days / 30)             │
                          │                                       │
                          │   score = w_r·R + w_c·C + w_f·F       │
                          └───────────────────────────────────────┘
                                          │
                                          ▼
                          ┌────────────────────────┐
                          │  Streamlit UI          │  Top-K results + signal breakdown
                          │  (streamlit_app.py)    │
                          └────────────────────────┘
```

## Tech stack

| Layer            | Choice                                     | Why                                                                        |
| ---------------- | ------------------------------------------ | -------------------------------------------------------------------------- |
| Language         | Python 3.11                                | Ecosystem match for the ML libraries used.                                 |
| Deep learning    | PyTorch (CPU)                              | Runtime doesn't need a GPU. Small, cheap to deploy.                        |
| Transformers     | `transformers` (4.43)                      | DistilBERT for credibility, tokenizer utilities.                           |
| Semantic search  | `sentence-transformers` 2.7 (all-MiniLM-L6-v2) | 90MB embedding model — fast, competitive quality for short news snippets. |
| Fine-tuning      | `peft` (LoRA) — optional path              | Adapter-based fine-tuning if you want to keep the base frozen.             |
| Training data    | LIAR2 (via HuggingFace `datasets`)         | Widely used political-fact-check corpus; 6-way collapsed to binary here.   |
| Retrieval        | Google News RSS                            | No API key, hundreds of publishers, real freshness signal.                 |
| UI               | Streamlit + custom CSS                     | Fast to build, easy to deploy, injects raw HTML for the animated radar and result cards. |
| Deployment       | Streamlit Community Cloud (CPU, free tier) | Zero cost, sleeps and wakes on demand, permanent URL.                      |

## Repository structure

```
factchecker/
├── streamlit_app.py           # Main entry point — Streamlit UI
├── requirements.txt           # pip dependencies
├── runtime.txt                # Pins Python 3.11 (tokenizers doesn't build on 3.14)
├── training_log.txt           # Latest classifier training run
│
├── src/
│   ├── crisis_detector.py     # Query intent: "emergency" vs "standard"
│   ├── freshness.py           # exp(-age/30) time-decay
│   ├── ranker.py              # Composite scoring, weight profiles
│   ├── publisher_trust.py     # Curated per-publisher trust table
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
│   └── best_model.pt          # Downloaded at boot from GitHub Release
│
├── scripts/
│   └── score_corpus.py        # One-off: batch-score the cached corpus
│
└── tests/
    ├── test_freshness.py
    └── test_ranker.py
```

## Local installation

**Prerequisites:** Python 3.11, git, ~2GB free disk (dependencies + models).

```bash
# 1. Clone the repo
git clone https://github.com/jaya242/crisis-search.git
cd crisis-search

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate         # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501`. First search downloads the MiniLM embedding model (~90MB) and the fine-tuned classifier checkpoint (~250MB, from GitHub Releases) — those take about 30 seconds the first time, then are cached.

**Note on the checkpoint.** `checkpoints/best_model.pt` is not committed (gitignored, ~250MB). The app fetches it from the repo's GitHub Release on first run. If you want to train your own instead, see the next section.

## Training the credibility classifier

```bash
# Full fine-tune (updates all DistilBERT weights)
python -m src.train

# Or LoRA fine-tune (freezes DistilBERT, trains low-rank adapters — smaller checkpoint)
python -m src.train_lora
```

Training uses the LIAR2 dataset (auto-downloaded via `datasets`). The default config: 1 epoch, batch size 32, AdamW, lr=2e-5. Expected result: ~76% validation accuracy in ~10 minutes on CPU.

The classifier binary-collapses LIAR2's 6-way labels by dropping the ambiguous middle classes (`barely-true`, `half-true`) and merging the rest into `credible` (`true`, `mostly-true`) vs `not_credible` (`false`, `pants-fire`). This is a modeling choice made to keep the binary crisp — half-truths are their own hard problem.

## Deployment

Signal is deployed on [Streamlit Community Cloud](https://share.streamlit.io), a free hosting tier for Streamlit apps.

**How it works:**
- Push code to GitHub → Streamlit Cloud auto-detects changes → rebuilds the app.
- Free CPU tier: sleeps after ~48 hours of no traffic, wakes on incoming request in ~15–30 seconds.
- Persistent URL: [crisis-search.streamlit.app](https://crisis-search.streamlit.app) — works forever, no credit card required.

**Deploying your own copy:**

1. Fork this repo.
2. Upload `checkpoints/best_model.pt` as a GitHub Release asset in your fork (tag `v1.0`, filename `best_model.pt`).
3. Update the `CKPT_URL` fallback in `src/live_pipeline.py` to point at your release URL, or set the `SIGNAL_CKPT_URL` env var in Streamlit Cloud's secrets.
4. Go to [share.streamlit.io](https://share.streamlit.io) → connect your fork → set main file to `streamlit_app.py` → in **Advanced settings**, set Python version to **3.11** (critical — 3.14 doesn't build `tokenizers`).
5. Deploy.

Total cost: $0. Total setup time: ~30 minutes.

## Limitations and next steps

**Honest limitations:**

- **75.7% classifier accuracy** means ~1 in 4 credibility scores from the text classifier alone would be wrong. The publisher-prior blend (60/40) compensates for this in practice, but the underlying model still isn't strong. Longer training and a bigger backbone (e.g., DeBERTa-v3) would push it up.
- **Publisher table is hand-curated.** ~70 outlets, informed by external factuality assessments but ultimately a hypothesis, not a fitted result. A model that learned publisher trust from source-labeled ranking data would be more principled.
- **Google News RSS gives descriptions, not full text.** Snippet-only credibility scoring is noisier than full-article scoring. A production version would fetch and cache article bodies.
- **The crisis detector is a keyword rule engine.** It handles "right now", "urgent", "evacuate" well and everything else as `standard`. An LLM classifier (Claude Haiku, stub already in code) would catch subtler urgency cues like *"which highway is closed"*.

**Next steps under consideration:**

- Swap the keyword classifier for a Claude-Haiku call, with keyword fallback.
- Learn publisher trust from labeled ranking data instead of hand-curating.
- Cache retrieval results per (query, hour) to cut per-request latency.
- Log ranking decisions for offline evaluation against a labeled crisis-search benchmark.

---

Built by [@jaya242](https://github.com/jaya242). Live at [crisis-search.streamlit.app](https://crisis-search.streamlit.app).
