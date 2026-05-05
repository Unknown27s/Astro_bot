"""
Offline RAGAS evaluation runner for AstroBot.

Uses local project embeddings (sentence-transformers) and Groq as the LLM judge.
Outputs per-sample metrics + summary for PPT comparison.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation on AstroBot dataset.")
    parser.add_argument(
        "--dataset",
        default=str(PROJECT_ROOT / "tests" / "ragas_dataset.csv"),
        help="Path to CSV with question,ground_truth columns.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "tests" / "ragas_outputs"),
        help="Directory for CSV/JSON outputs.",
    )
    parser.add_argument("--run-name", default="run", help="Label for this run (used in output file names).")
    parser.add_argument("--top-k", type=int, default=None, help="Override TOP_K_RESULTS for retrieval.")
    parser.add_argument(
        "--retrieval-mode",
        choices=["dense", "hybrid"],
        default=None,
        help="Override RETRIEVAL_MODE for this run.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Limit number of rows for a quick run.",
    )
    parser.add_argument(
        "--disable-memory",
        action="store_true",
        help="Disable conversation memory for deterministic evaluation.",
    )
    return parser.parse_args()


def _apply_env_overrides(args: argparse.Namespace) -> None:
    if args.top_k is not None:
        os.environ["TEST_TOP_K_RESULTS"] = str(args.top_k)
    if args.retrieval_mode:
        os.environ["TEST_RETRIEVAL_MODE"] = args.retrieval_mode
    if args.disable_memory:
        os.environ["TEST_CONV_ENABLED"] = "false"


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _build_embeddings() -> Any:
    from ingestion.embedder import generate_embeddings

    class LocalEmbeddings:
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return generate_embeddings(texts)

        def embed_query(self, text: str) -> list[float]:
            return generate_embeddings([text])[0]

    return LocalEmbeddings()


def _build_nvidia_llm() -> Any:
    from langchain_openai import ChatOpenAI

    api_key = _require_env("NVIDIA_API_KEY")
    model = os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    temperature = float(os.getenv("NVIDIA_TEMPERATURE", "0.2"))
    return ChatOpenAI(
        api_key=api_key,
        model=model,
        base_url=base_url,
        temperature=temperature,
    )


def _load_dataset(csv_path: Path, max_rows: int | None) -> list[dict]:
    import pandas as pd

    df = pd.read_csv(csv_path)
    if "question" not in df.columns or "ground_truth" not in df.columns:
        raise ValueError("Dataset must contain 'question' and 'ground_truth' columns.")

    if max_rows is not None:
        df = df.head(max_rows)

    return df.to_dict(orient="records")


def _run_pipeline(rows: list[dict], top_k: int | None) -> list[dict]:
    from rag.retriever import retrieve_context, format_context_for_llm
    from rag.generator import generate_response
    from tests.config import TOP_K_RESULTS

    resolved_top_k = top_k if top_k is not None else TOP_K_RESULTS

    records: list[dict] = []

    for row in rows:
        question = str(row.get("question") or "").strip()
        ground_truth = str(row.get("ground_truth") or "").strip()

        chunks = retrieve_context(question, top_k=resolved_top_k) if question else []
        contexts = [chunk.get("text", "") for chunk in chunks if chunk.get("text")]
        context_str = format_context_for_llm(chunks)

        response = generate_response(question, context_str, sources=chunks)
        answer = response.get("response", "") if isinstance(response, dict) else str(response or "")

        records.append(
            {
                "question": question,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": ground_truth,
            }
        )

    return records


def _evaluate(records: list[dict]) -> tuple[Any, Any]:
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    from datasets import Dataset

    dataset = Dataset.from_list(records)
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]

    result = evaluate(
        dataset,
        metrics=metrics,
        llm=_build_nvidia_llm(),
        embeddings=_build_embeddings(),
    )

    return result, metrics


def _write_outputs(result: Any, metrics: list[Any], records: list[dict], output_dir: Path, run_name: str) -> dict:
    import pandas as pd

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base_name = f"ragas_{run_name}_{timestamp}"

    per_sample = result.to_pandas()
    per_sample_path = output_dir / f"{base_name}_per_sample.csv"
    per_sample.to_csv(per_sample_path, index=False)

    records_path = output_dir / f"{base_name}_dataset.json"
    records_path.write_text(json.dumps(records, ensure_ascii=True, indent=2), encoding="utf-8")

    metric_names = [metric.name for metric in metrics]
    summary = {
        "run_name": run_name,
        "rows": len(records),
        "metrics": {},
    }

    for name in metric_names:
        if name in per_sample.columns:
            summary["metrics"][name] = float(pd.to_numeric(per_sample[name], errors="coerce").mean())

    summary_path = output_dir / f"{base_name}_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")

    return {
        "per_sample": str(per_sample_path),
        "summary": str(summary_path),
        "dataset": str(records_path),
    }


def main() -> None:
    args = _parse_args()
    _apply_env_overrides(args)

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    rows = _load_dataset(dataset_path, args.max_rows)
    if not rows:
        raise RuntimeError("Dataset is empty.")

    records = _run_pipeline(rows, args.top_k)
    result, metrics = _evaluate(records)

    outputs = _write_outputs(result, metrics, records, Path(args.output_dir), args.run_name)

    print("RAGAS evaluation completed")
    print(json.dumps({"outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()
