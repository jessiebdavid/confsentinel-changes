import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from confsentinel.core.differ import ConfigurationParityDiffer
from confsentinel.core.evaluator import RuleEvaluationEngine
from confsentinel.core.hasher import RuleHasher
from confsentinel.core.parser import LayeredASTParser
from confsentinel.core.redactor import ClientSideSecretRedactor
from confsentinel.models.rules import RuleBatchLoader
from confsentinel.reporting.terminal import TerminalDiagnosticsGate
from confsentinel.transport.client import ResilientRuleTransportClient
from confsentinel.transport.spooler import SynchronousDiskSpooler

app = typer.Typer(
    name="confsentinel",
    help="ConfSentinel: Shift-Left Cloud-Native Configuration Governance CLI",
    add_completion=False,
    no_args_is_help=True,
)
console = Console(stderr=True)


def resolve_file_path(config_dir: Path, filename: str) -> Path:
    std_path = config_dir / "src" / "main" / "resources" / filename
    if std_path.exists():
        return std_path
    return config_dir / filename


def get_git_context() -> tuple[str, str, str]:
    commit = os.getenv("GITHUB_SHA") or os.getenv("CI_COMMIT_SHA")
    branch = os.getenv("GITHUB_REF_NAME") or os.getenv("CI_COMMIT_REF_NAME")
    author = os.getenv("GITHUB_ACTOR") or os.getenv("GITLAB_USER_EMAIL")

    if not commit:
        try:
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except Exception:
            commit = "HEAD-LOCAL"

    if not branch:
        try:
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except Exception:
            branch = "local"

    if not author:
        try:
            author = subprocess.check_output(
                ["git", "config", "user.email"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except Exception:
            author = "developer@local"

    return commit, branch, author


def resolve_service_identity(explicit_name: Optional[str], config_dir: Path, base_props: dict) -> str:
    candidate = explicit_name

    if not candidate:
        candidate = os.getenv("CONFSENTINEL_SERVICE_NAME")
    if not candidate:
        repo = os.getenv("GITHUB_REPOSITORY")
        candidate = repo.split("/")[-1] if repo else None
    if not candidate:
        candidate = os.getenv("CI_PROJECT_NAME") or os.getenv("BITBUCKET_REPO_SLUG")

    if not candidate:
        prop = base_props.get("spring.application.name")
        if prop and str(prop.value).strip():
            candidate = str(prop.value).strip()

    if not candidate:
        candidate = config_dir.resolve().name

    cleaned = re.sub(r"[^a-z0-9-]", "-", candidate.lower().strip())
    slug = re.sub(r"-+", "-", cleaned).strip("-")
    if not slug:
        console.print("[bold red]FATAL:[/] Unable to resolve valid microservice identity. Specify --service-name.")
        raise typer.Exit(code=1)
    return slug


@app.command("publish-rules")
def publish_rules(
    rules_dir: Path = typer.Option(..., "--rules-dir", "-r", exists=True, file_okay=False, dir_okay=True, readable=True),
    engine_url: Optional[str] = typer.Option(None, "--engine-url", "-u", envvar="CONFSENTINEL_ENGINE_URL"),
    token: Optional[str] = typer.Option(None, "--token", "-t", envvar="CONFSENTINEL_GOVERNANCE_TOKEN"),
    prune: bool = typer.Option(False, "--prune", help="Deactivate omitted rules on central engine"),
) -> None:
    if not token:
        console.print("[bold red]ERROR:[/] Missing governance token. Pass --token or set CONFSENTINEL_GOVERNANCE_TOKEN.")
        raise typer.Exit(code=1)

    loader = RuleBatchLoader()
    try:
        rules = loader.load_and_deduplicate(rules_dir)
        hashed_rules = [RuleHasher.assign_identifiers(r) for r in rules]
    except Exception as ex:
        console.print(f"[bold red]Rule Validation Error:[/] {ex}")
        raise typer.Exit(code=1)

    client = ResilientRuleTransportClient(engine_url)
    success = client.publish_batch(hashed_rules, token, prune)
    if not success:
        console.print("[bold red]Publish Error:[/] Failed to publish rules batch to central engine.")
        raise typer.Exit(code=1)
    console.print(f"[bold green]✔ SUCCESS:[/] Published {len(hashed_rules)} rules to {engine_url}.")
    raise typer.Exit(code=0)


@app.command("scan")
def scan(
    config_dir: Path = typer.Option(Path("."), "--config-dir", "-c", exists=True, file_okay=False, dir_okay=True, readable=True),
    environment: str = typer.Option("prod", "--environment", "-e"),
    base_env: str = typer.Option("dev", "--base-env", "-b"),
    service_name: Optional[str] = typer.Option(None, "--service-name", "-s"),
    engine_url: Optional[str] = typer.Option(None, "--engine-url", "-u", envvar="CONFSENTINEL_ENGINE_URL"),
    ci_token: Optional[str] = typer.Option(None, "--ci-token", envvar="CONFSENTINEL_CI_TOKEN"),
    strict_warnings: bool = typer.Option(False, "--strict-warnings"),
) -> None:
    start_time = os.times().elapsed

    spooler = SynchronousDiskSpooler(config_dir / ".confsentinel" / "spool")
    if engine_url and ci_token:
        spooler.drain_pending(engine_url, ci_token)

    parser = LayeredASTParser()
    base_file = resolve_file_path(config_dir, "application.yml")
    target_file = resolve_file_path(config_dir, f"application-{environment}.yml")
    base_env_file = resolve_file_path(config_dir, f"application-{base_env}.yml")

    base_props = parser.parse_file(base_file, active_profile=base_env)
    slug = resolve_service_identity(service_name, config_dir, base_props)

    merged_props = parser.merge_profiles(base_file, target_file, active_profile=environment)
    k8s_props = parser.discover_and_parse_k8s(config_dir, active_profile=environment)
    merged_props.update(k8s_props)

    base_env_props = parser.merge_profiles(base_file, base_env_file, active_profile=base_env)
    drift = ConfigurationParityDiffer.compute_drift(base_env_props, merged_props, base_env, environment)

    transport = ResilientRuleTransportClient(engine_url)
    rules, is_fallback = transport.fetch_active_rules()
    if is_fallback:
        console.print("[dim yellow]Notice:[/] Operating on embedded baseline rules (offline fallback).")

    raw_violations = RuleEvaluationEngine.evaluate(merged_props, rules, target_environment=environment)
    clean_violations = ClientSideSecretRedactor.sanitize_violations(raw_violations)

    duration_ms = int((os.times().elapsed - start_time) * 1000)
    gate = TerminalDiagnosticsGate(console)
    exit_code = gate.render_and_evaluate_exit(clean_violations, duration_ms, len(merged_props), strict_warnings)

    status = "FAILED" if exit_code == 1 else ("WARNINGS" if clean_violations else "PASSED")
    blockers = sum(1 for v in clean_violations if v.severity.value in ["BLOCKER", "CRITICAL"])
    warnings = sum(1 for v in clean_violations if v.severity.value == "WARNING")

    commit_hash, branch, author = get_git_context()

    spooler.flush_or_spool(
        engine_url=engine_url,
        ci_token=ci_token,
        service_name=slug,
        environment=environment,
        commit_hash=commit_hash,
        branch=branch,
        author=author,
        duration_ms=duration_ms,
        status=status,
        blockers_count=blockers,
        warnings_count=warnings,
        drift=drift,
        violations=clean_violations,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    app()