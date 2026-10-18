import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from confsentinel.core.parser import FlattenedProperty
from confsentinel.models.rules import CheckType, RuleDefinitionModel, RuleSeverity


@dataclass
class ViolationRecord:
    rule_id: str
    rule_code: str
    severity: RuleSeverity
    file_path: Path
    line_number: int
    key_path: str
    detected_snippet: str
    remediation: str
    rule_hash: str
    rule_name: str
    rule_category: str


class RuleEvaluationEngine:
    @staticmethod
    def evaluate(
        properties: Dict[str, FlattenedProperty],
        rules: List[RuleDefinitionModel],
        target_environment: str = "prod",
    ) -> List[ViolationRecord]:
        violations: List[ViolationRecord] = []

        if "syntax.error" in properties:
            err_prop = properties["syntax.error"]
            violations.append(ViolationRecord(
                rule_id="00000000-0000-0000-0000-000000000000",
                rule_code="SYNTAX-001",
                severity=RuleSeverity.BLOCKER,
                file_path=err_prop.file_path,
                line_number=err_prop.line_number,
                key_path="syntax.error",
                detected_snippet=err_prop.literal_str[:120],
                remediation="Correct YAML syntax or indentation error.",
                rule_hash="0000000000000000000000000000000000000000000000000000000000000000",
                rule_name="YAML Syntax Error",
                rule_category="COMPLIANCE",
            ))

        virtual_target_filename = f"application-{target_environment}.yml"

        for rule in rules:
            target_re = re.compile(rule.target_pattern)
            rule_applies_to_target = bool(target_re.search(virtual_target_filename))

            # Match properties if file matches target pattern OR if property is inherited from base
            matched_props = [
                p for p in properties.values()
                if target_re.search(p.file_path.name)
                or (rule_applies_to_target and "application" in p.file_path.name)
            ]

            if rule.check_type == CheckType.KEY_MUST_EXIST:
                exists = any(p.key_path == rule.key_path for p in matched_props)
                if not exists and rule_applies_to_target:
                    sample = matched_props[0].file_path if matched_props else Path(virtual_target_filename)
                    violations.append(ViolationRecord(
                        rule_id=rule.id or "",
                        rule_code=rule.rule_code,
                        severity=rule.severity,
                        file_path=sample,
                        line_number=1,
                        key_path=rule.key_path,
                        detected_snippet=f"# Missing Mandatory Key: {rule.key_path}",
                        remediation=rule.remediation,
                        rule_hash=rule.rule_hash or "",
                        rule_name=rule.name,
                        rule_category=rule.category.value,
                    ))
                continue

            for prop in matched_props:
                is_direct = prop.key_path == rule.key_path
                is_array_element = prop.key_path.startswith(f"{rule.key_path}[")
                if not (is_direct or is_array_element):
                    continue

                val_str = str(prop.value)

                if rule.check_type == CheckType.KEY_MUST_NOT_EXIST:
                    violations.append(RuleEvaluationEngine._build(rule, prop, f"{prop.key_path}: {val_str}"))

                elif rule.check_type == CheckType.REGEX_MUST_NOT_MATCH:
                    param_re = re.compile(rule.parameter)  # type: ignore[arg-type]
                    if param_re.search(val_str):
                        violations.append(RuleEvaluationEngine._build(rule, prop, f"{prop.key_path}: {val_str}"))

                elif rule.check_type == CheckType.REGEX_MUST_MATCH:
                    param_re = re.compile(rule.parameter)  # type: ignore[arg-type]
                    if not param_re.search(val_str):
                        violations.append(RuleEvaluationEngine._build(rule, prop, f"{prop.key_path}: {val_str}"))

                elif rule.check_type == CheckType.NUMERIC_RANGE:
                    try:
                        num = float(prop.value)
                        if num < rule.min_value or num > rule.max_value:  # type: ignore[operator]
                            snippet = f"{prop.key_path}: {num} (Bounds: [{rule.min_value}, {rule.max_value}])"
                            violations.append(RuleEvaluationEngine._build(rule, prop, snippet))
                    except (ValueError, TypeError):
                        snippet = f"{prop.key_path}: {val_str} (Type Mismatch: Expected Float)"
                        violations.append(RuleEvaluationEngine._build(rule, prop, snippet))

        return violations

    @staticmethod
    def _build(rule: RuleDefinitionModel, prop: FlattenedProperty, snippet: str) -> ViolationRecord:
        return ViolationRecord(
            rule_id=rule.id or "",
            rule_code=rule.rule_code,
            severity=rule.severity,
            file_path=prop.file_path,
            line_number=prop.line_number,
            key_path=prop.key_path,
            detected_snippet=snippet,
            remediation=rule.remediation,
            rule_hash=rule.rule_hash or "",
            rule_name=rule.name,
            rule_category=rule.category.value,
        )