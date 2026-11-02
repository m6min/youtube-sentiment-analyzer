"""Build the runtime artifact locally or in the Docker build stage."""

import argparse
import json
import shutil
from pathlib import Path

from huggingface_hub import snapshot_download
from onnxruntime.quantization import QuantType, quantize_dynamic
from onnxruntime.quantization.shape_inference import quant_pre_process
from optimum.exporters.onnx import main_export
from transformers import AutoTokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--revision", default="f6070864c69990a669bf9b8c659a0093062d73e8")
    args = parser.parse_args()
    model_id = "savasy/bert-base-turkish-sentiment-cased"
    snapshot = snapshot_download(
        model_id, revision=args.revision,
        allow_patterns=["config.json", "*.safetensors", "tokenizer*", "vocab.txt", "special_tokens_map.json"],
    )
    args.output.mkdir(parents=True, exist_ok=True)
    args.work_dir.mkdir(parents=True, exist_ok=True)
    fp32_dir = args.work_dir / "fp32"
    main_export(snapshot, output=fp32_dir, task="text-classification", opset=18,
                device="cpu", framework="pt", do_validation=True)
    preprocessed = args.work_dir / "preprocessed.onnx"
    # Standard ONNX shape inference supports this exported graph; ORT's optional
    # symbolic shape pass cannot resolve all of its dynamic attention shapes.
    quant_pre_process(str(fp32_dir / "model.onnx"), str(preprocessed),
                      skip_optimization=True, skip_symbolic_shape=True)
    quantize_dynamic(
        str(preprocessed), str(args.output / "model.int8.onnx"),
        weight_type=QuantType.QInt8,
        op_types_to_quantize=["MatMul", "Gather"],
        per_channel=True,
        extra_options={"DefaultTensorType": 1},
    )
    tokenizer = AutoTokenizer.from_pretrained(snapshot, use_fast=True)
    tokenizer.backend_tokenizer.save(str(args.output / "tokenizer.json"))
    shutil.copyfile(Path(snapshot) / "config.json", args.output / "config.json")
    manifest = {"model_id": model_id, "revision": Path(snapshot).name,
                "format": "onnx-dynamic-int8", "max_length": 128}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest))
    print(f"INT8 artifact: {(args.output / 'model.int8.onnx').stat().st_size / 1024**2:.1f} MiB")


if __name__ == "__main__":
    main()
