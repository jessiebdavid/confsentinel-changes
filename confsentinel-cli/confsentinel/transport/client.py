import importlib.resources
import json
from typing import List, Optional
import httpx
from confsentinel.models.rules import RuleDefinitionModel


class ResilientRuleTransportClient:
    def __init__(self, engine_url: Optional[str], timeout_sec: float = 0.200):
        self.engine_url = engine_url.rstrip("/") if engine_url else None
        self.timeout = timeout_sec

    def fetch_active_rules(self) -> tuple[List[RuleDefinitionModel], bool]:
        if self.engine_url:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(f"{self.engine_url}/api/v1/rules/active")
                    if resp.status_code == 200:
                        rules_data = resp.json().get("rules", [])
                        return [RuleDefinitionModel(**r) for r in rules_data], False
            except (httpx.RequestError, httpx.TimeoutException):
                pass
        return self._load_baseline(), True

    def publish_batch(self, rules: List[RuleDefinitionModel], token: str, prune: bool) -> bool:
        if not self.engine_url:
            return False
        # by_alias=True emits camelCase keys expected by Spring Boot
        payload = {
            "batchId": "sync-batch",
            "publishedBy": "confsentinel-cli",
            "rules": [r.model_dump(by_alias=True) for r in rules],
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{self.engine_url}/api/v1/rules?prune={str(prune).lower()}",
                    json=payload,
                    headers={"X-Governance-Token": token, "Content-Type": "application/json"},
                )
                return resp.status_code in (200, 201)
        except Exception:
            return False

    def _load_baseline(self) -> List[RuleDefinitionModel]:
        ref = importlib.resources.files("confsentinel.resources").joinpath("baseline_rules.json")
        data = json.loads(ref.read_text(encoding="utf-8"))
        return [RuleDefinitionModel(**r) for r in data.get("rules", [])]