import hashlib
import json
import uuid
from confsentinel.models.rules import RuleDefinitionModel

NAMESPACE_CONFSENTINEL = uuid.UUID("a9e0f31c-5d82-4b2a-bf32-7c81604a11c2")


class RuleHasher:
    @staticmethod
    def compute_rule_hash(rule: RuleDefinitionModel) -> str:
        canonical_map = {
            "category": rule.category.value,
            "check_type": rule.check_type.value,
            "key_path": rule.key_path,
            "max_value": rule.max_value if rule.max_value is not None else None,
            "min_value": rule.min_value if rule.min_value is not None else None,
            "name": rule.name,
            "parameter": rule.parameter if rule.parameter is not None else None,
            "remediation": rule.remediation,
            "rule_code": rule.rule_code,
            "severity": rule.severity.value,
            "target_pattern": rule.target_pattern,
        }
        canonical_json = json.dumps(canonical_map, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    @classmethod
    def assign_identifiers(cls, rule: RuleDefinitionModel) -> RuleDefinitionModel:
        rule_hash = cls.compute_rule_hash(rule)
        name_string = f"{rule.rule_code}:{rule_hash}"
        rule.rule_hash = rule_hash
        rule.id = str(uuid.uuid5(NAMESPACE_CONFSENTINEL, name_string))
        return rule