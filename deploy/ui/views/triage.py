from collections.abc import Callable
import rio
from state.gateway import get_gateway


class TriagePage(rio.Component):
    selected_run_index: int = 0
    filter_env: str = "ALL"

    def _set_env(self, env: str) -> None:
        self.filter_env = env
        self.selected_run_index = 0

    def _select_run(self, idx: int) -> None:
        self.selected_run_index = idx

    def _make_env_handler(self, env: str) -> Callable[[], None]:
        def handler() -> None:
            self._set_env(env)
        return handler

    def _make_run_handler(self, idx: int) -> Callable[[], None]:
        def handler() -> None:
            self._select_run(idx)
        return handler

    def build(self) -> rio.Component:
        gateway = get_gateway()
        runs = gateway.runs_cache

        if self.filter_env != "ALL":
            runs = [r for r in runs if r.get("environment", "").lower() == self.filter_env.lower()]

        return rio.Column(
            rio.Text("Run Explorer & Violation Triage", style="heading1"),
            rio.Text("Inspect historical CI/CD policy evaluations, commit telemetry, and remediation snippets", style="dim"),
            rio.Spacer(min_height=1.0),
            rio.Row(
                rio.Text("Filter Environment:", style=rio.TextStyle(font_weight="bold")),
                *[
                    rio.Button(
                        env,
                        style="major" if self.filter_env == env else "plain-text",
                        on_press=self._make_env_handler(env),
                    )
                    for env in ["ALL", "dev", "staging", "prod"]
                ],
                spacing=0.5,
            ),
            rio.Spacer(min_height=1.0),
            rio.Row(
                self._render_runs_list(runs),
                self._render_run_details(runs),
                spacing=1.0,
                grow_y=True,
            ),
            spacing=1.0,
            grow_y=True,
        )

    def _render_runs_list(self, runs: list) -> rio.Component:
        if not runs:
            return rio.Card(
                content=rio.Text("No evaluation telemetry runs found.", style="dim", margin=1.5),
                min_width=20,
            )

        items = []
        for idx, run in enumerate(runs):
            is_selected = idx == self.selected_run_index
            svc = run.get("serviceName", "Service")
            env = run.get("environment", "env")
            status = run.get("status", "UNKNOWN")

            items.append(
                rio.Button(
                    f"{svc} [{env.upper()}] - {status}",
                    style="major" if is_selected else "plain-text",
                    on_press=self._make_run_handler(idx),
                )
            )

        return rio.Card(
            content=rio.Column(
                rio.Text("Evaluations", style=rio.TextStyle(font_weight="bold")),
                rio.Separator(),
                *items,
                spacing=0.4,
                margin=0.8,
            ),
            min_width=22,
        )

    def _render_run_details(self, runs: list) -> rio.Component:
        if not runs or self.selected_run_index >= len(runs):
            return rio.Card(content=rio.Text("Select a run to view details", style="dim", margin=1.5), grow_x=True)

        run = runs[self.selected_run_index]
        violations = run.get("violations", [])

        violation_components = []
        for v in violations:
            violation_components.append(
                rio.Card(
                    content=rio.Column(
                        rio.Row(
                            rio.Text(v.get("ruleCode", "RULE"), style=rio.TextStyle(font_weight="bold")),
                            rio.Text(
                                v.get("severity", "BLOCKER"),
                                style=rio.TextStyle(fill=rio.Color.from_hex("#DC2626"), font_weight="bold"),
                            ),
                            rio.Spacer(),
                            rio.Text(f"{v.get('filePath', '')}:{v.get('lineNumber', 0)}", style="dim"),
                            spacing=1.0,
                        ),
                        rio.Text(f"Snippet: {v.get('snippet', '')}", style="dim"),
                        rio.Text(f"Remediation: {v.get('remediation', '')}", style=rio.TextStyle(font_weight="bold")),
                        spacing=0.4,
                        margin=0.8,
                    )
                )
            )

        if not violation_components:
            violation_components.append(
                rio.Text(
                    "No violations reported for this run. Clean execution! ✔",
                    style=rio.TextStyle(fill=rio.Color.from_hex("#16A34A"), font_weight="bold"),
                )
            )

        return rio.Card(
            content=rio.Column(
                rio.Text(f"Run Details: {run.get('serviceName')} ({run.get('environment')})", style="heading2"),
                rio.Separator(),
                rio.Text(f"Commit: {run.get('commitHash', 'N/A')} | Author: {run.get('author', 'N/A')}", style="dim"),
                rio.Spacer(min_height=0.5),
                rio.Text("Violations Intercepted", style=rio.TextStyle(font_weight="bold")),
                *violation_components,
                spacing=0.6,
                margin=1.0,
            ),
            grow_x=True,
        )