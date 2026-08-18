"""
DistilBERT + dropout + linear classification head.

Why DistilBERT and not training from scratch:
  - Training a transformer's language understanding from raw text takes massive data + compute. DistilBERT already learned general English
    representations from pretraining. We're only teaching it a NEW task (credibility) on top of representations it already has. This is
    transfer learning: reuse the expensive part, cheaply adapt the rest.

[CLS] token:
  - DistilBERT prepends a [CLS] token to every input. After running through all transformer layers, self-attention has let [CLS] attend
    to every other token in the sequence, so its final hidden state is a learned summary of the whole input. That's why we take the [CLS]
    position's output and feed it into a linear head, rather than pooling over all tokens.
"""
import torch
import torch.nn as nn
from transformers import DistilBertModel

class CredibilityClassifier(nn.Module):
    def __init__(self, model_name: str = "distilbert-base-uncased",
                 num_labels: int = 2, dropout: float = 0.1):
        super().__init__()
        self.encoder = DistilBertModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size  # 768
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, num_labels)
    
    def forward(self, input_ids: torch.Tensor,
                attention_mask: torch.Tensor) -> torch.Tensor:
        outputs = self.encoder(input_ids=input_ids,
                                attention_mask=attention_mask)
        last_hidden_state = outputs.last_hidden_state  # (B, seq_len, 768)
        cls_hidden = last_hidden_state[:, 0, :]         # (B, 768) — the [CLS] rep
        cls_hidden = self.dropout(cls_hidden)
        logits = self.classifier(cls_hidden)             # (B, num_labels)
        return logits

