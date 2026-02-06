from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from ..config import Config
from ..utils.logger import Logger

logger = Logger.get_logger(__name__)


@dataclass(frozen=True)
class RiskPolicy:
    version: str
    weights: Dict[str, float]
    thresholds: Dict[str, int]
    action_adjustments: Dict[str, Dict[str, Any]]
    signal_overrides: Dict[str, Dict[str, Any]]
    reason_templates: Dict[str, str]


class RiskPolicyLoader:
    _cached_policy: RiskPolicy | None = None

    @staticmethod
    def load() -> RiskPolicy:
        if RiskPolicyLoader._cached_policy is not None:
            return RiskPolicyLoader._cached_policy

        default_policy = RiskPolicy(
            version=Config.RISK_POLICY["version"],
            weights={
                "permission": 1.5,
                "financial": 1.3,
                "reputation": 1.2,
                "technical": 1.1,
                "behavioral": 1.0,
            },
            thresholds={
                "critical": 85,
                "high": Config.RISK_THRESHOLDS["high"],
                "medium": Config.RISK_THRESHOLDS["medium"],
            },
            action_adjustments={},
            signal_overrides={},
            reason_templates={},
        )

        policy_path = Path(Config.DATA_DIR) / Config.RISK_POLICY["filename"]
        if not policy_path.exists():
            logger.warning(f"Risk policy file not found: {policy_path}. Using defaults.")
            RiskPolicyLoader._cached_policy = default_policy
            return default_policy

        try:
            with open(policy_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)

            policy = RiskPolicy(
                version=str(payload.get("version") or default_policy.version),
                weights=payload.get("weights") or default_policy.weights,
                thresholds=payload.get("thresholds") or default_policy.thresholds,
                action_adjustments=payload.get("action_adjustments") or {},
                signal_overrides=payload.get("signal_overrides") or {},
                reason_templates=payload.get("reason_templates") or {},
            )
            RiskPolicyLoader._cached_policy = policy
            return policy
        except Exception as error:
            logger.warning(f"Failed to load risk policy: {error}. Using defaults.")
            RiskPolicyLoader._cached_policy = default_policy
            return default_policy

    @staticmethod
    def reload() -> RiskPolicy:
        RiskPolicyLoader._cached_policy = None
        return RiskPolicyLoader.load()
