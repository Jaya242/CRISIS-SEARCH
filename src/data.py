"""
LIAR dataset loading + label collapse.

NOTE: the original 'liar' dataset on HF is dead — its loading script
pulls from cs.ucsb.edu, which now returns 403. We use 'chengxuphd/liar2'
instead: a maintained, expanded successor (23K statements vs 12.8K),
same PolitiFact methodology, hosted as real data files (no fetch script).
Its label column is a plain int 0-5 (not a HF ClassLabel), confirmed via
paper + spot-checking justification text against sample rows:
    0=pants-fire, 1=false, 2=barely-true, 3=half-true, 4=mostly-true, 5=true

DECISION (yours to defend in the interview, not mine):
We collapse to a binary credibility signal and DROP the two middle
categories (barely-true, half-true) rather than folding them into one
side or the other. Rationale to internalize:
  - barely-true / half-true are genuinely ambiguous — a classifier forced
    to pick a side for them is learning noise, not signal.
  - Folding them in either direction (e.g. half-true -> credible) teachesl
    the model a fuzzy, defensible-either-way boundary that will hurt
    precision on the clear cases you actually care about.
  - Dropping them gives you a cleaner separating hyperplane: the model
    only ever has to learn "this is confidently false" vs "this is
    confidently true," which is the actual product requirement.
Be ready to say this out loud.

Final mapping:
    pants-fire, false        -> 0  (not credible)
    mostly-true, true        -> 1  (credible)
    barely-true, half-true   -> dropped
"""

from datasets import load_dataset
import pandas as pd

DATASET_PATH="chengxuphd/liar2"
LABEL_NAMES_6WAY = [
    "pants-fire",   # 0
    "false",        # 1
    "barely-true",  # 2
    "half-true",    # 3
    "mostly-true",  # 4
    "true",         # 5
]
DROP_LABELS = {"barely-true", "half-true"}
NOT_CREDIBLE = {"pants-fire", "false"}
CREDIBLE = {"mostly-true", "true"}


def _collapse_label(label_idx:int)->int|None:
    name=LABEL_NAMES_6WAY[label_idx]
    if name in DROP_LABELS:
        return None
    return 0 if name in NOT_CREDIBLE else 1

def load_liar(split:str="train") -> pd.DataFrame:
    """
    Load one split of LIAR2 and return a DataFrame with columns:
        text, label (0=not credible, 1=credible)
    Rows with barely-true/half-true are dropped.
    """
    ds = load_dataset(DATASET_PATH, split=split)
    df=ds.to_pandas()
    df["label"] = df["label"].apply(_collapse_label)
    before = len(df)
    df = df.dropna(subset=["label"]).copy()
    df["label"] = df["label"].astype(int)
    dropped = before - len(df)

    df = df.rename(columns={"statement": "text"})
    df = df[["text", "label"]].reset_index(drop=True)

    print(f"[{split}] loaded {before} rows, dropped {dropped} "
          f"(barely-true/half-true), kept {len(df)}")
    print(f"[{split}] label distribution:\n{df['label'].value_counts()}")
    return df

if __name__ == "__main__":
    train_df = load_liar("train")
    print(train_df.head(5))
    val_df = load_liar("validation")
    test_df = load_liar("test")