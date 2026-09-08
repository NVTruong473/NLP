from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from vietrag.config import load_config
from vietrag.pipeline import VietRAGPipeline
from vietrag.providers import GeminiProvider, OpenRouterProvider, ProviderError
from vietrag.secrets import load_provider_env


def parse_json_object(text: str) -> dict:
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        raise ValueError("Judge did not return a JSON object")
    return json.loads(match.group(0))


def clamp_score(value) -> float:
    return max(0.0, min(1.0, float(value)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--dataset", default="evaluation/sample_eval.jsonl")
    parser.add_argument("--env", default="/content/providers.env")
    args = parser.parse_args()

    load_provider_env(args.env)
    cfg = load_config(args.config)
    gemini = GeminiProvider()
    openrouter = OpenRouterProvider()
    rag = VietRAGPipeline.load(cfg, gemini, openrouter)

    rows = [
        json.loads(x)
        for x in Path(args.dataset).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    judged = []
    for row in rows:
        result = rag.ask(row["question"])
        context = "\n\n".join(
            f"[S{i}] {r.chunk.text}" for i, r in enumerate(result.sources, start=1)
        )
        citation_coverage = (
            1.0 if result.refused or re.search(r"\[S\d+\]", result.text) else 0.0
        )

        judge_prompt = f'''You are evaluating a retrieval-augmented answer. Use ONLY the evidence shown.
Return JSON only, with numeric values from 0.0 to 1.0:
{{"faithfulness":0.0,"answer_relevancy":0.0,"coherence":0.0,"evidence_completeness":0.0}}

Definitions:
- faithfulness: factual claims are supported by EVIDENCE.
- answer_relevancy: ANSWER directly addresses QUESTION.
- coherence: ANSWER is logically organized and understandable.
- evidence_completeness: ANSWER covers the important information that can reasonably be answered from EVIDENCE.
For an out-of-domain/insufficient question, a correct refusal should score highly on faithfulness and relevancy.

QUESTION:
{row["question"]}

EVIDENCE:
{context or "(none)"}

ANSWER:
{result.text}
'''
        try:
            judge_text = gemini.generate(judge_prompt)
            judge_provider = "gemini"
        except ProviderError:
            judge_text = openrouter.generate(judge_prompt)
            judge_provider = "openrouter"

        scores = parse_json_object(judge_text)
        for key in ("faithfulness", "answer_relevancy", "coherence", "evidence_completeness"):
            scores[key] = clamp_score(scores[key])
        scores["citation_coverage"] = citation_coverage
        scores["question"] = row["question"]
        scores["answer_provider"] = result.provider
        scores["judge_provider"] = judge_provider
        scores["refused"] = result.refused
        judged.append(scores)
        print(json.dumps(scores, ensure_ascii=False))

    numeric = [
        "faithfulness",
        "answer_relevancy",
        "coherence",
        "evidence_completeness",
        "citation_coverage",
    ]
    summary = {
        key: sum(float(r[key]) for r in judged) / len(judged)
        for key in numeric
        if judged and all(key in r for r in judged)
    }
    print("\nSUMMARY")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
