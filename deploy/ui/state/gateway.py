import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import httpx

CONFIG_FILE_PATH = Path(os.getenv("CONFSENTINEL_UI_CONFIG_PATH", ".confsentinel/ui_config.json"))


class BackendApiGateway:
    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        poll_interval: float = 10.0,
    ):
        saved_config = self._load_from_disk()

        self.base_url = (
            base_url
            or saved_config.get("base_url")
            or os.getenv("CONFSENTINEL_ENGINE_URL", "http://localhost:8080")
        ).rstrip("/")

        self.auth_token = (
            auth_token
            or saved_config.get("auth_token")
            or os.getenv("CONFSENTINEL_ENGINE_TOKEN", "")
        )

        self.poll_interval = float(
            saved_config.get("poll_interval")
            or os.getenv("CONFSENTINEL_POLL_INTERVAL", str(poll_interval))
        )

        self.summary_cache: Dict[str, Any] = {
            "totalScans": 0,
            "overallPassRate": 100.0,
            "activeRulesCount": 0,
            "totalBlockersPrevented": 0,
            "matrix": [],
        }
        self.runs_cache: List[Dict[str, Any]] = []
        self.rules_cache: List[Dict[str, Any]] = []
        self.drift_cache: Dict[str, Dict[str, Any]] = {}

        self.is_connected: bool = False
        self.last_latency_ms: int = 0
        self.last_error: Optional[str] = None

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.auth_token:
            headers["X-Governance-Token"] = self.auth_token
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def _load_from_disk(self) -> Dict[str, Any]:
        if CONFIG_FILE_PATH.exists():
            try:
                return json.loads(CONFIG_FILE_PATH.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_to_disk(self) -> None:
        try:
            CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "base_url": self.base_url,
                "auth_token": self.auth_token,
                "poll_interval": self.poll_interval,
            }
            CONFIG_FILE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def update_configuration(
        self,
        new_url: str,
        new_token: Optional[str] = None,
        new_interval: Optional[float] = None,
        persist: bool = True,
    ) -> None:
        self.base_url = new_url.rstrip("/")
        if new_token is not None:
            self.auth_token = new_token
        if new_interval is not None:
            self.poll_interval = new_interval
        self.drift_cache.clear()
        if persist:
            self._save_to_disk()

    async def test_connection(self) -> tuple[bool, str, int]:
        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/actuator/health",
                    headers=self._get_headers(),
                )
                latency = int((time.perf_counter() - start) * 1000)
                if resp.status_code == 200:
                    return True, "Connected to Actuator probe (HTTP 200 OK)", latency

                resp2 = await client.get(
                    f"{self.base_url}/api/v1/reports/summary",
                    headers=self._get_headers(),
                )
                latency = int((time.perf_counter() - start) * 1000)
                if resp2.status_code == 200:
                    return True, "Connected to Governance API (HTTP 200 OK)", latency
                return False, f"HTTP Error {resp2.status_code}: {resp2.text[:80]}", latency
            except Exception as ex:
                latency = int((time.perf_counter() - start) * 1000)
                return False, f"Connection failed ({type(ex).__name__}): {ex}", latency

    async def refresh_all(self) -> None:
        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                start = time.perf_counter()
                headers = self._get_headers()

                r_sum = await client.get(f"{self.base_url}/api/v1/reports/summary", headers=headers)
                if r_sum.status_code == 200:
                    self.summary_cache = r_sum.json()

                r_eval = await client.get(f"{self.base_url}/api/v1/evaluations", headers=headers)
                if r_eval.status_code == 200:
                    self.runs_cache = r_eval.json()

                r_rules = await client.get(f"{self.base_url}/api/v1/rules", headers=headers)
                if r_rules.status_code == 200:
                    self.rules_cache = r_rules.json()

                self.last_latency_ms = int((time.perf_counter() - start) * 1000)
                self.is_connected = True
                self.last_error = None
            except Exception as ex:
                self.is_connected = False
                self.last_error = f"Engine unreachable at {self.base_url} ({type(ex).__name__})"

    async def fetch_service_drift(self, service_id: str) -> Dict[str, Any]:
        if service_id in self.drift_cache:
            return self.drift_cache[service_id]

        async with httpx.AsyncClient(timeout=2.0) as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/api/v1/reports/drift/{service_id}",
                    headers=self._get_headers(),
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.drift_cache[service_id] = data
                    return data
            except Exception:
                pass
        return {"status": "NO_DRIFT_DATA", "unboundBaseKeys": []}


_shared_gateway: Optional[BackendApiGateway] = None


def get_gateway() -> BackendApiGateway:
    global _shared_gateway
    if _shared_gateway is None:
        _shared_gateway = BackendApiGateway()
    return _shared_gateway