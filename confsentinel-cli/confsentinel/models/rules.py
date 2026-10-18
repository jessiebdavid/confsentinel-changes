import re
from enum import Enum
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel
from ruamel.yaml import YAML


class RuleCategory(str, Enum):
    SECURITY = "SECURITY"
    RELIABILITY = "RELIABILITY"
    OBSERVABILITY = "OBSERVABILITY"
    COMPLIANCE = "COMPLIANCE"


class RuleSeverity(str, Enum):
    BLOCKER = "BLOCKER"
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"


class CheckType(str, Enum):
    REGEX_MUST_NOT_MATCH = "REGEX_MUST_NOT_MATCH"
    REGEX_MUST_MATCH = "REGEX_MUST_MATCH"
    KEY_MUST_EXIST = "KEY_MUST_EXIST"
    KEY_MUST_NOT_EXIST = "KEY_MUST_NOT_EXIST"
    NUMERIC_RANGE = "NUMERIC_RANGE"


class RuleDefinitionModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    rule_code: str = Field(..., pattern=r"^[A-Z]{3,4}-[0-9]{3,4}$")
    name: str = Field(..., min_length=10, max_length=100)
    category: RuleCategory
    severity: RuleSeverity
    target_pattern: str = Field(..., min_length=1)
    key_path: str = Field(..., min_length=1)
    check_type: CheckType
    parameter: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    remediation: str = Field(..., min_length=10)
    id: Optional[str] = None
    rule_hash: Optional[str] = None

    @field_validator("parameter")
    @classmethod
    def validate_regex_syntax(cls, v: Optional[str], info) -> Optional[str]:
        check_type = info.data.get("check_type")
        if check_type in [CheckType.REGEX_MUST_NOT_MATCH, CheckType.REGEX_MUST_MATCH]:
            if not v or not v.strip():
                raise ValueError(f"check_type {check_type} requires a non-empty regex parameter.")
            try:
                re.compile(v)
            except re.error as ex:
                raise ValueError(f"Invalid regex syntax: {ex.msg}") from ex
        return v

    @model_validator(mode="after")
    def validate_numeric_bounds(self) -> "RuleDefinitionModel":
        if self.check_type == CheckType.NUMERIC_RANGE:
            if self.min_value is None or self.max_value is None:
                raise ValueError("Both min_value and max_value are required for NUMERIC_RANGE.")
            if self.min_value > self.max_value:
                raise ValueError(f"min_value ({self.min_value}) cannot exceed max_value ({self.max_value}).")
        return self


class RuleBatchLoader:
    def __init__(self):
        self.yaml = YAML(typ="safe")

    def load_and_deduplicate(self, directory: Path) -> List[RuleDefinitionModel]:
        seen_codes: dict[str, Path] = {}
        rules: List[RuleDefinitionModel] = []
        for path in sorted(directory.rglob("*.y*ml")):
            with open(path, "r", encoding="utf-8") as f:
                docs = list(self.yaml.load_all(f))
                for doc in docs:
                    if not doc:
                        continue
                    rule = RuleDefinitionModel(**doc)
                    if rule.rule_code in seen_codes:
                        raise ValueError(
                            f"Rule collision: Code '{rule.rule_code}' in {path} "
                            f"conflicts with {seen_codes[rule.rule_code]}."
                        )
                    seen_codes[rule.rule_code] = path
                    rules.append(rule)
        return rules