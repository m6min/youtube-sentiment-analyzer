"""Compare FP32 and INT8 on a small, explicit smoke set (not an accuracy benchmark)."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.sentiment import SentimentAnalyzer

TEXTS = [
    "Harika bir video, çok beğendim.",
    "Berbat bir video, hiç beğenmedim.",
    "Çok güzel anlatmışsınız, teşekkür ederim.",
    "Zaman kaybı, izlediğime pişman oldum.",
    "Anlatım çok başarılı ve anlaşılır.",
    "Ses kalitesi çok kötü, hiçbir şey anlaşılmıyor.",
    "Emeğinize sağlık, çok faydalı oldu.",
    "Tam bir hayal kırıklığı.",
    "Bu konuyu sonunda anladım, harikasınız.",
    "Yanlış bilgilerle dolu, tavsiye etmiyorum.",
    "Fena değil ama daha iyi olabilirdi.",
    "Başlıkta söylenen şeyi videoda bulamadım.",
    "Yeni bölüm ne zaman gelecek?",
    "Bu videoyu dün izledim.",
    "Keşke daha uzun olsaydı, çok sevdim.",
    "Hiç güzel olmamış.",
    "Güzel değil diyemem.",
    "Çok güzel olmuş gerçekten!",
    "Mükemmel! Böyle kötü bir anlatım görmedim.",
    "Bu videodaki açıklamaları beğenmedim. " * 100,
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--fp32", type=Path, required=True)
    args = parser.parse_args()
    model = SentimentAnalyzer(args.model_dir)
    quantized = model.predict(TEXTS)
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    reference = ort.InferenceSession(str(args.fp32), sess_options=options, providers=["CPUExecutionProvider"])
    expected = []
    for text in TEXTS:
        encoded = model.tokenizer.encode(text)
        inputs = {"input_ids": np.array([encoded.ids], dtype=np.int64),
                "attention_mask": np.array([encoded.attention_mask], dtype=np.int64),
                "token_type_ids": np.array([encoded.type_ids], dtype=np.int64)}
        expected.append(int(reference.run(None, inputs)[0].argmax(axis=1)[0]))
    agreement = sum(a == b for a, b in zip(expected, quantized))
    print(json.dumps({"sample_count": len(TEXTS), "matching_labels": agreement,
                    "fp32_labels": expected, "int8_labels": quantized,
                    "note": "Smoke comparison only; not a held-out quality evaluation."}, indent=2))
    if agreement / len(TEXTS) < 0.9:
        raise SystemExit("INT8 changed more than 10% of smoke-test labels")


if __name__ == "__main__":
    main()
