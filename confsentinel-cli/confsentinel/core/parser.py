import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import YAMLError


@dataclass(frozen=True)
class FlattenedProperty:
    key_path: str
    value: Any
    literal_str: str
    file_path: Path
    line_number: int


class LayeredASTParser:
    PLACEHOLDER_TOKEN_REGEX = re.compile(r"\$\{([^:]+?)(?::([^}]+?))?\}")

    def __init__(self):
        self.yaml = YAML(typ="rt")
        self.yaml.preserve_quotes = True

    def resolve_iterative_placeholders(self, raw_str: str) -> tuple[str, str]:
        resolved = raw_str
        for _ in range(5):
            match = self.PLACEHOLDER_TOKEN_REGEX.search(resolved)
            if not match:
                break

            # If placeholder has no default value (${VAR}), stop to avoid infinite substitution loop
            if match.group(2) is None:
                break

            resolved = self.PLACEHOLDER_TOKEN_REGEX.sub(
                lambda m: m.group(2) if m.group(2) is not None else m.group(0),
                resolved,
                count=1,
            )
        return resolved, raw_str

    def _is_profile_active(self, doc: Any, target_profile: str) -> bool:
        if not isinstance(doc, CommentedMap):
            return True
        spring = doc.get("spring")
        if isinstance(spring, CommentedMap):
            config = spring.get("config")
            if isinstance(config, CommentedMap):
                activate = config.get("activate")
                if isinstance(activate, CommentedMap):
                    on_profile = activate.get("on-profile")
                    if on_profile:
                        profiles = [p.strip() for p in str(on_profile).split(",")]
                        return target_profile in profiles
        return True

    def _flatten_recursive(
        self,
        node: Any,
        prefix: str,
        file_path: Path,
        anchor_line_0idx: int,
        results: Dict[str, FlattenedProperty],
    ) -> None:
        if isinstance(node, CommentedMap):
            for k, v in node.items():
                rel_line_0idx = node.lc.data.get(k, [0])[0] if hasattr(node, "lc") else 0
                abs_line_1idx = (anchor_line_0idx + rel_line_0idx) + 1
                new_key = f"{prefix}.{k}" if prefix else str(k)

                if isinstance(v, (CommentedMap, CommentedSeq)):
                    self._flatten_recursive(v, new_key, file_path, anchor_line_0idx, results)
                else:
                    resolved_val, literal_repr = self.resolve_iterative_placeholders(str(v) if v is not None else "")
                    results[new_key] = FlattenedProperty(new_key, resolved_val, literal_repr, file_path, abs_line_1idx)

        elif isinstance(node, CommentedSeq):
            for idx, item in enumerate(node):
                rel_line_0idx = node.lc.data.get(idx, [0])[0] if hasattr(node, "lc") else 0
                abs_line_1idx = (anchor_line_0idx + rel_line_0idx) + 1
                new_key = f"{prefix}[{idx}]"

                if isinstance(item, (CommentedMap, CommentedSeq)):
                    self._flatten_recursive(item, new_key, file_path, anchor_line_0idx, results)
                else:
                    resolved_val, literal_repr = self.resolve_iterative_placeholders(str(item) if item is not None else "")
                    results[new_key] = FlattenedProperty(new_key, resolved_val, literal_repr, file_path, abs_line_1idx)

    def parse_file(self, file_path: Path, active_profile: str) -> Dict[str, FlattenedProperty]:
        properties: Dict[str, FlattenedProperty] = {}
        if not file_path.exists():
            return properties

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                documents = list(self.yaml.load_all(f))
            except YAMLError as err:
                properties["syntax.error"] = FlattenedProperty(
                    "syntax.error", str(err), str(err), file_path, 1
                )
                return properties

            for doc in documents:
                if not doc:
                    continue
                if self._is_profile_active(doc, active_profile):
                    self._flatten_recursive(doc, "", file_path, 0, properties)
        return properties

    def discover_and_parse_k8s(self, config_dir: Path, active_profile: str) -> Dict[str, FlattenedProperty]:
        properties: Dict[str, FlattenedProperty] = {}
        for path in sorted(config_dir.rglob("*.y*ml")):
            if "k8s" not in path.parts and "helm" not in path.parts:
                continue
            with open(path, "r", encoding="utf-8") as f:
                try:
                    docs = list(self.yaml.load_all(f))
                except YAMLError:
                    continue

                for doc in docs:
                    if isinstance(doc, CommentedMap) and doc.get("kind") == "ConfigMap":
                        data_block = doc.get("data")
                        if isinstance(data_block, CommentedMap):
                            for key, content in data_block.items():
                                if re.search(r"application.*\.ya?ml$", str(key)):
                                    # Scalar literal content begins on the line following key
                                    anchor_line_0idx = data_block.lc.data.get(key, [0])[0] + 1
                                    try:
                                        sub_doc = self.yaml.load(str(content))
                                        if self._is_profile_active(sub_doc, active_profile):
                                            self._flatten_recursive(sub_doc, "", path, anchor_line_0idx, properties)
                                    except YAMLError as parse_err:
                                        err_key = f"k8s.configmap.syntax_error[{key}]"
                                        properties[err_key] = FlattenedProperty(
                                            err_key, str(parse_err), str(parse_err), path, anchor_line_0idx + 1
                                        )
        return properties

    def merge_profiles(self, base_file: Path, overlay_file: Path, active_profile: str) -> Dict[str, FlattenedProperty]:
        merged = self.parse_file(base_file, active_profile)
        overlay = self.parse_file(overlay_file, active_profile)
        merged.update(overlay)
        return merged