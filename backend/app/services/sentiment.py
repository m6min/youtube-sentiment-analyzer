"""CPU-only sentiment inference; no Transformers/PyTorch dependency at runtime."""

import json
from pathlib import Path
from threading import Lock

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer


class SentimentAnalyzer:
    def __init__(self, model_dir: Path, batch_size: int = 1, max_length: int = 128):
        if batch_size < 1 or not 2 <= max_length <= 512:
            raise ValueError("Invalid sentiment batch size or token limit")
        self.batch_size = batch_size
        self._lock = Lock()
        config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
        labels = {int(k): v.lower() for k, v in config["id2label"].items()}
        if set(labels.values()) != {"negative", "positive"}:
            raise ValueError("Expected a binary positive/negative sentiment model")
        self.negative_id = next(k for k, v in labels.items() if v == "negative")
        self.tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=max_length)
        self.tokenizer.enable_padding(pad_id=config["pad_token_id"], pad_token="[PAD]")
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.enable_cpu_mem_arena = False
        options.enable_mem_pattern = False
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        self.session = ort.InferenceSession(
            str(model_dir / "model.int8.onnx"),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        self.input_names = {item.name for item in self.session.get_inputs()}

    def predict(self, texts: list[str]) -> list[int]:
        """Return one class ID per text, bounding memory across concurrent calls."""
        predictions = []
        with self._lock:
            for start in range(0, len(texts), self.batch_size):
                encoded = self.tokenizer.encode_batch(texts[start:start + self.batch_size])
                inputs = {
                    "input_ids": np.asarray([item.ids for item in encoded], dtype=np.int64),
                    "attention_mask": np.asarray([item.attention_mask for item in encoded], dtype=np.int64),
                    "token_type_ids": np.asarray([item.type_ids for item in encoded], dtype=np.int64),
                }
                logits = self.session.run(None, {k: v for k, v in inputs.items() if k in self.input_names})[0]
                if logits.shape != (len(encoded), 2) or not np.isfinite(logits).all():
                    raise RuntimeError("Sentiment model returned invalid logits")
                predictions.extend(logits.argmax(axis=1).tolist())
        return predictions

    def negative_percentage(self, comments: list[dict]) -> float:
        texts = [comment["text"] for comment in comments if comment["text"].strip()]
        if not texts:
            return 0.0
        predictions = self.predict(texts)
        return round(100 * predictions.count(self.negative_id) / len(predictions), 2)
