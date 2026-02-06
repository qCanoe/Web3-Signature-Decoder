import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from src.core.pipeline import SemanticPipeline


FIXTURES_DIR = Path(__file__).parent / "fixtures"
BASELINE_PATH = Path(__file__).parent / "baseline_metrics.json"


def _load_samples() -> List[Dict[str, Any]]:
    samples: List[Dict[str, Any]] = []
    for fixture in sorted(FIXTURES_DIR.glob("*.jsonl")):
        with open(fixture, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                samples.append(json.loads(line))
    return samples


def _normalize_risk(level: str) -> str:
    if level == "critical":
        return "high"
    return level


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _macro_f1(expected: List[str], predicted: List[str], labels: List[str]) -> float:
    f1_scores: List[float] = []
    for label in labels:
        tp = sum(1 for exp, pred in zip(expected, predicted) if exp == label and pred == label)
        fp = sum(1 for exp, pred in zip(expected, predicted) if exp != label and pred == label)
        fn = sum(1 for exp, pred in zip(expected, predicted) if exp == label and pred != label)
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        if precision + recall == 0:
            f1_scores.append(0.0)
        else:
            f1_scores.append(2 * precision * recall / (precision + recall))
    return sum(f1_scores) / len(labels)


def test_eval_fixture_distribution():
    samples = _load_samples()
    assert len(samples) == 240

    signature_counts = defaultdict(int)
    risk_counts = defaultdict(int)
    for sample in samples:
        signature_counts[sample["signature_type"]] += 1
        risk_counts[sample["expected_risk_level"]] += 1

    assert signature_counts["eth_signTypedData_v4"] == 140
    assert signature_counts["eth_sendTransaction"] == 100
    assert risk_counts["high"] == 108
    assert risk_counts["medium"] == 72
    assert risk_counts["low"] == 60


def test_risk_metrics_gate():
    samples = _load_samples()
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    pipeline = SemanticPipeline()

    expected_risks: List[str] = []
    predicted_risks: List[str] = []
    expected_actions: List[str] = []
    predicted_actions: List[str] = []

    high_tp = 0
    high_fp = 0
    high_fn = 0

    for sample in samples:
        result = pipeline.process(sample["input"])
        predicted_action = result["pipeline_result"]["semantic"]["action"]["type"]
        predicted_risk = _normalize_risk(result["pipeline_result"]["ui"]["risk_level"])

        expected_action = sample["expected_action"]
        expected_risk = _normalize_risk(sample["expected_risk_level"])

        expected_risks.append(expected_risk)
        predicted_risks.append(predicted_risk)
        expected_actions.append(expected_action)
        predicted_actions.append(predicted_action)

        expected_high = expected_risk == "high"
        predicted_high = predicted_risk == "high"
        if expected_high and predicted_high:
            high_tp += 1
        elif not expected_high and predicted_high:
            high_fp += 1
        elif expected_high and not predicted_high:
            high_fn += 1

    high_risk_recall = _safe_div(high_tp, high_tp + high_fn)
    high_risk_precision = _safe_div(high_tp, high_tp + high_fp)
    risk_macro_f1 = _macro_f1(expected_risks, predicted_risks, ["low", "medium", "high"])

    action_matches = [
        1 if exp == pred else 0 for exp, pred in zip(expected_actions, predicted_actions)
    ]
    action_top1_accuracy = _safe_div(sum(action_matches), len(action_matches))

    assert high_risk_recall >= 0.95
    assert high_risk_precision >= 0.75
    assert action_top1_accuracy >= 0.88

    baseline_macro_f1 = float(baseline["risk_macro_f1"])
    assert risk_macro_f1 >= baseline_macro_f1 * 1.10
