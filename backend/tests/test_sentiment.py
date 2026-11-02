import json
from types import SimpleNamespace

import numpy as np
import pytest

from app.services.sentiment import SentimentAnalyzer


@pytest.fixture
def analyzer(tmp_path, monkeypatch):
    from app.services import sentiment

    # Reversed mapping verifies that the negative label is read from config.
    (tmp_path / "config.json").write_text(json.dumps({
        "id2label": {"0": "positive", "1": "negative"}, "pad_token_id": 0,
    }))
    class Tokenizer:
        def enable_truncation(self, **kwargs):
            pass
        def enable_padding(self, **kwargs):
            pass
        def encode_batch(self, texts):
            return [SimpleNamespace(ids=[int(text == "bad")], attention_mask=[1], type_ids=[0]) for text in texts]
    class Session:
        def __init__(self, *args, **kwargs):
            self.batch_lengths = []
        def get_inputs(self):
            return [SimpleNamespace(name="input_ids"), SimpleNamespace(name="attention_mask")]
        def run(self, outputs, inputs):
            assert set(inputs) == {"input_ids", "attention_mask"}
            self.batch_lengths.append(len(inputs["input_ids"]))
            return [np.array([[0, 1] if row[0] else [1, 0] for row in inputs["input_ids"]])]
    monkeypatch.setattr(sentiment, "Tokenizer", SimpleNamespace(from_file=lambda _: Tokenizer()))
    monkeypatch.setattr(sentiment.ort, "InferenceSession", Session)
    return SentimentAnalyzer(tmp_path, batch_size=3)


def test_all_comments_are_counted_including_last_partial_batch(analyzer):
    comments = [{"text": "bad"}] * 31 + [{"text": "good"}] * 9
    assert analyzer.negative_percentage(comments) == 77.5
    assert sum(analyzer.session.batch_lengths) == 40
    assert max(analyzer.session.batch_lengths) == 3
    assert analyzer.session.batch_lengths[-1] == 1


def test_empty_comments_do_not_call_model(analyzer):
    assert analyzer.negative_percentage([]) == 0.0
    assert analyzer.negative_percentage([{"text": "  "}]) == 0.0
    assert analyzer.session.batch_lengths == []


def test_invalid_output_is_not_silently_reported_as_positive(analyzer):
    analyzer.session.run = lambda *_: [np.array([[float("nan"), 1]])]
    with pytest.raises(RuntimeError, match="invalid logits"):
        analyzer.negative_percentage([{"text": "bad"}])
