import json
import sys
import time
from pathlib import Path
from typing import List, Optional
import httpx
from confsentinel.core.differ import DriftSummary
from confsentinel.core.evaluator import ViolationRecord


class SynchronousDiskSpooler:
    def __init__(self, spool_dir: Path):
        self.spool_dir = spool_dir
        self.spool_dir.mkdir(parents=True, exist_ok=True)

    def drain_pending(self, engine_url: str, ci_token: str, max_files: int = 5) -> None:
        count = 0
        for spool_file in sorted(self.spool_dir.glob("eval-*.json")):
            if count >= max_files:
                break
            try:
                payload = json.loads(spool_file.read_text(encoding="utf-8"))
                with httpx.Client(timeout=0.300) as client:
                    resp = client.post(
                        f"{engine_url.rstrip('/')}/api/v1/evaluations",
                        json=payload,
                        headers={"X-CI-Token": ci_token, "Content-Type": "application/json"},
                    )
                    if resp.status_code in (200, 201):
                        spool_file.unlink(missing_ok=True)
                        count += 1
            except Exception:
                break

    def flush_or_spool(
        self,
        engine_url: Optional[str],
        ci_token: Optional[str],
        service_name: str,
        environment: str,
        commit_hash: str,
        branch: str,
        author: str,
        duration_ms: int,
        status: str,
        blockers_count: int,
        warnings_count: int,
        drift: DriftSummary,
        violations: List[ViolationRecord],
    ) -> None:
        payload = {
            "serviceName": service_name,
            "environment": environment,
            "commitHash": commit_hash,
            "branch": branch,
            "author": author,
            "durationMs": duration_ms,
            "status": status,
            "blockersCount": blockers_count,
            "warningsCount": warnings_count,
            "driftSummary": drift.model_dump(),
            "violations": [
                {
                    "ruleId": v.rule_id,
                    "ruleCode": v.rule_code,
                    "severity": v.severity.value,
                    "filePath": str(v.file_path),
                    "lineNumber": v.line_number,
                    "snippet": v.detected_snippet,
                    "remediation": v.remediation,
                    "ruleDescriptor": {
                        "ruleHash": v.rule_hash,
                        "name": v.rule_name,
                        "category": v.rule_category,
                    },
                }
                for v in violations
            ],
        }

        if not engine_url or not ci_token:
            self._spool_to_disk(payload, commit_hash)
            return

        try:
            with httpx.Client(timeout=httpx.Timeout(0.250, connect=0.100)) as client:
                resp = client.post(
                    f"{engine_url.rstrip('/')}/api/v1/evaluations",
                    json=payload,
                    headers={"X-CI-Token": ci_token, "Content-Type": "application/json"},
                )
                if resp.status_code not in (200, 201):
                    self._spool_to_disk(payload, commit_hash)
        except Exception as ex:
            sys.stderr.write(f"\n[ConfSentinel Telemetry] Network flush failed ({ex}); spooled to disk.\n")
            self._spool_to_disk(payload, commit_hash)

    def _spool_to_disk(self, payload: dict, commit_hash: str) -> None:
        filename = f"eval-{commit_hash[:8]}-{int(time.time() * 1000)}.json"
        target = self.spool_dir / filename
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")