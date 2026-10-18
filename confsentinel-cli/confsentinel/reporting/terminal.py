from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from confsentinel.core.evaluator import ViolationRecord
from confsentinel.models.rules import RuleSeverity


class TerminalDiagnosticsGate:
    def __init__(self, console: Console):
        self.console = console

    def render_and_evaluate_exit(
        self,
        violations: List[ViolationRecord],
        duration_ms: int,
        scanned_count: int,
        strict_warnings: bool = False,
    ) -> int:
        blockers = [v for v in violations if v.severity in (RuleSeverity.BLOCKER, RuleSeverity.CRITICAL)]
        warnings = [v for v in violations if v.severity == RuleSeverity.WARNING]

        if not violations:
            self.console.print(Panel(
                f"[bold green]✔ PASS:[/] All {scanned_count} properties verified compliant in {duration_ms}ms.",
                title="ConfSentinel Policy Gate",
                border_style="green",
            ))
            return 0

        table = Table(title="Configuration Governance Violations", show_header=True, header_style="bold cyan")
        table.add_column("Severity", width=10)
        table.add_column("Rule", width=10)
        table.add_column("Location", width=32)
        table.add_column("Masked Snippet", width=30)
        table.add_column("Remediation", width=40)

        for v in violations:
            color = "red" if v.severity in (RuleSeverity.BLOCKER, RuleSeverity.CRITICAL) else "yellow"
            table.add_row(
                f"[{color}]{v.severity.value}[/]",
                v.rule_code,
                f"{v.file_path.name}:{v.line_number}",
                v.detected_snippet,
                v.remediation,
            )

        self.console.print(table)
        self.console.print(f"[dim]Scanned {scanned_count} properties in {duration_ms}ms.[/dim]\n")

        if blockers:
            self.console.print(f"[bold red]Pipeline Blocked:[/] {len(blockers)} blocker/critical violations detected.")
            return 1

        if strict_warnings and warnings:
            self.console.print(f"[bold red]Pipeline Blocked:[/] Strict warnings mode halted build on {len(warnings)} warnings.")
            return 1

        self.console.print(f"[bold yellow]Pipeline Passed with Warnings:[/] {len(warnings)} advisory violations detected.")
        return 0