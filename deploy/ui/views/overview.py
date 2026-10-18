import rio
from state.gateway import get_gateway


class OverviewPage(rio.Component):
    def build(self) -> rio.Component:
        gateway = get_gateway()
        summary = gateway.summary_cache
        matrix = summary.get("matrix", [])

        total_scans = summary.get("totalScans", 0)
        pass_rate = summary.get("overallPassRate", 100.0)
        active_rules = summary.get("activeRulesCount", 0)
        blockers = summary.get("totalBlockersPrevented", 0)

        return rio.Column(
            rio.Text("Governance Overview & Compliance Rollup", style="heading1"),
            rio.Text("Real-time policy adherence and deployment readiness across microservices", style="dim"),
            rio.Spacer(min_height=1.0),
            rio.Row(
                self._metric_card("Total Scans Executed", str(total_scans), "material/history", "#0284C7"),
                self._metric_card(
                    "Overall Pass Rate",
                    f"{pass_rate:.1f}%",
                    "material/shield",
                    "#16A34A" if pass_rate >= 80 else "#EAB308",
                ),
                self._metric_card("Active Governance Rules", str(active_rules), "material/security", "#8B5CF6"),
                self._metric_card("Blockers Prevented", str(blockers), "material/warning", "#DC2626"),
                spacing=1.0,
                grow_x=True,
            ),
            rio.Spacer(min_height=1.5),
            rio.Card(
                content=rio.Column(
                    rio.Text("Service Compliance Matrix", style="heading2"),
                    rio.Separator(),
                    rio.Spacer(min_height=0.5),
                    self._render_matrix_table(matrix),
                    margin=1.0,
                    spacing=0.6,
                ),
                grow_x=True,
            ),
            spacing=1.0,
            grow_x=True,
        )

    def _metric_card(self, title: str, value: str, icon_name: str, hex_color: str) -> rio.Component:
        color = rio.Color.from_hex(hex_color)
        return rio.Card(
            content=rio.Row(
                rio.Icon(icon_name, fill=color),
                rio.Column(
                    rio.Text(title, style="dim"),
                    rio.Text(value, style="heading1"),
                    spacing=0.2,
                ),
                spacing=1.0,
                margin=1.0,
            ),
            grow_x=True,
        )

    def _render_matrix_table(self, matrix: list) -> rio.Component:
        if not matrix:
            return rio.Text("No microservice evaluation telemetry recorded yet.", style="dim")

        rows = [
            rio.Row(
                rio.Text("Microservice", style=rio.TextStyle(font_weight="bold"), min_width=12),
                rio.Text("Team", style=rio.TextStyle(font_weight="bold"), min_width=10),
                rio.Text("Dev", style=rio.TextStyle(font_weight="bold"), min_width=6),
                rio.Text("Staging", style=rio.TextStyle(font_weight="bold"), min_width=6),
                rio.Text("Prod", style=rio.TextStyle(font_weight="bold"), min_width=6),
                rio.Text("Last Evaluated", style=rio.TextStyle(font_weight="bold"), min_width=12),
                spacing=1.0,
            ),
            rio.Separator(),
        ]

        for row in matrix:
            svc_name = row.get("name", "Unknown")
            team = row.get("team", "Unassigned")
            env_states = row.get("envStates", {})
            last_eval = row.get("latestEvaluationTimestamp", "N/A")
            if last_eval != "N/A" and "T" in last_eval:
                last_eval = last_eval.split("T")[0]

            rows.append(
                rio.Row(
                    rio.Text(svc_name, min_width=12),
                    rio.Text(team, style="dim", min_width=10),
                    self._status_badge(env_states.get("dev", "NO_DATA")),
                    self._status_badge(env_states.get("staging", "NO_DATA")),
                    self._status_badge(env_states.get("prod", "NO_DATA")),
                    rio.Text(last_eval, style="dim", min_width=12),
                    spacing=1.0,
                )
            )

        return rio.Column(*rows, spacing=0.5)

    def _status_badge(self, status: str) -> rio.Component:
        color_map = {
            "PASSED": "#16A34A",
            "BLOCKED": "#DC2626",
            "WARNING": "#EAB308",
            "NO_DATA": "#94A3B8",
        }
        hex_c = color_map.get(status, "#94A3B8")
        return rio.Text(
            status,
            style=rio.TextStyle(fill=rio.Color.from_hex(hex_c), font_weight="bold"),
            min_width=6,
        )