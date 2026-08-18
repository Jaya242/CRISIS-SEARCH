# Fact-Checker Credibility & Freshness Ranker

## Day 1 — Classifier
- Model: DistilBERT (distilbert-base-uncased) + dropout + linear head on [CLS]
- Task: binary credibility classification on LIAR2 (6-way collapsed to 2,
  barely-true/half-true dropped)
- Val accuracy: TBD
- Test accuracy: TBD
- Per-class F1 [not_credible, credible]: TBD
