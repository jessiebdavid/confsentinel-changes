import re
from typing import List
from confsentinel.core.evaluator import ViolationRecord


class ClientSideSecretRedactor:
    KEY_PATTERN = re.compile(
        r"(?i)(^|[._-])(password|secret|credential|token|private[_-]?key|api[_-]?key)($|[._-])"
    )
    URI_CREDENTIAL_PATTERN = re.compile(r"([a-zA-Z][a-zA-Z0-9+.-]*:\/\/)([^:]+):([^@]+)@")
    REDACTION_MARKER = "[REDACTED_BY_CONFSENTINEL]"

    @classmethod
    def sanitize_violations(cls, violations: List[ViolationRecord]) -> List[ViolationRecord]:
        sanitized: List[ViolationRecord] = []
        for v in violations:
            clean_snippet = cls.sanitize_snippet(v.key_path, v.detected_snippet)
            sanitized.append(ViolationRecord(
                rule_id=v.rule_id,
                rule_code=v.rule_code,
                severity=v.severity,
                file_path=v.file_path,
                line_number=v.line_number,
                key_path=v.key_path,
                detected_snippet=clean_snippet,
                remediation=v.remediation,
                rule_hash=v.rule_hash,
                rule_name=v.rule_name,
                rule_category=v.rule_category,
            ))
        return sanitized

    @classmethod
    def sanitize_snippet(cls, key_path: str, snippet: str) -> str:
        # Pass 1: Sensitive Key Matching with delimiter boundaries
        if cls.KEY_PATTERN.search(key_path):
            if ":" in snippet:
                k, _ = snippet.split(":", 1)
                return f"{k}: {cls.REDACTION_MARKER}"
            return f"{key_path}: {cls.REDACTION_MARKER}"

        # Pass 2: Embedded URI Credential Pattern Scrubbing
        if cls.URI_CREDENTIAL_PATTERN.search(snippet):
            return cls.URI_CREDENTIAL_PATTERN.sub(
                rf"\g<1>\g<2>:{cls.REDACTION_MARKER}@", snippet
            )

        return snippet