from typing import Dict, List
from pydantic import BaseModel
from confsentinel.core.parser import FlattenedProperty


class DriftSummary(BaseModel):
    baseEnv: str
    targetEnv: str
    baseKeysCount: int
    targetKeysCount: int
    unboundBaseKeys: List[str]


class ConfigurationParityDiffer:
    @staticmethod
    def compute_drift(
        base_props: Dict[str, FlattenedProperty],
        target_props: Dict[str, FlattenedProperty],
        base_env: str,
        target_env: str,
    ) -> DriftSummary:
        base_keys = set(base_props.keys())
        target_keys = set(target_props.keys())
        unbound = sorted(list(base_keys - target_keys))

        return DriftSummary(
            baseEnv=base_env,
            targetEnv=target_env,
            baseKeysCount=len(base_keys),
            targetKeysCount=len(target_keys),
            unboundBaseKeys=unbound,
        )