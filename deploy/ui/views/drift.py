from collections.abc import Callable
import rio
from state.gateway import get_gateway


class DriftPage(rio.Component):
    selected_service_id: str = ""
    drift_details: dict = {}

    def _select_service(self, service_id: str) -> None:
        self.selected_service_id = service_id
        self.session.create_task(self._fetch_drift(service_id))

    def _make_service_handler(self, service_id: str) -> Callable[[], None]:
        def handler() -> None:
            self._select_service(service_id)
        return handler

    async def _fetch_drift(self, service_id: str) -> None:
        gateway = get_gateway()
        self.drift_details = await gateway.fetch_service_drift(service_id)
        self.force_refresh()

    def build(self) -> rio.Component:
        gateway = get_gateway()
        summary = gateway.summary_cache
        matrix = summary.get("matrix", [])

        if not self.selected_service_id and matrix:
            self.selected_service_id = matrix[0].get("id", "")

        service_buttons = [
            rio.Button(
                m.get("name", "Service"),
                style="major" if self.selected_service_id == m.get("id") else "plain-text",
                on_press=self._make_service_handler(m.get("id", "")),
            )
            for m in matrix
        ]

        components: list[rio.Component] = [
            rio.Text("Environment Configuration Parity & Drift", style="heading1"),
            rio.Text("Detect configuration parameter drift between non-prod profiles and production", style="dim"),
            rio.Spacer(min_height=1.0),
        ]

        if service_buttons:
            components.append(rio.Row(*service_buttons, spacing=0.5))
            components.append(rio.Spacer(min_height=1.0))

        components.append(self._render_drift_view())

        return rio.Column(
            *components,
            spacing=1.0,
            grow_x=True,
        )

    def _render_drift_view(self) -> rio.Component:
        if not self.selected_service_id:
            return rio.Card(content=rio.Text("No microservices available to analyze drift.", style="dim", margin=1.5))

        status = self.drift_details.get("status", "NO_DRIFT_DATA")
        unbound = self.drift_details.get("unboundBaseKeys", [])

        unbound_items = (
            [rio.Text(f"• {k}", style="dim") for k in unbound]
            if unbound
            else [
                rio.Text(
                    "✔ Configuration parity preserved across environments.",
                    style=rio.TextStyle(fill=rio.Color.from_hex("#16A34A"), font_weight="bold"),
                )
            ]
        )

        return rio.Card(
            content=rio.Column(
                rio.Row(
                    rio.Text(f"Drift Status for {self.selected_service_id}:", style="heading2"),
                    rio.Text(
                        status,
                        style=rio.TextStyle(
                            fill=rio.Color.from_hex("#16A34A" if status == "PARITY_MATCH" else "#DC2626"),
                            font_weight="bold",
                        ),
                    ),
                    spacing=1.0,
                ),
                rio.Separator(),
                rio.Spacer(min_height=0.5),
                rio.Text("Unbound or Missing Keys in Target Environment:", style=rio.TextStyle(font_weight="bold")),
                *unbound_items,
                spacing=0.5,
                margin=1.0,
            ),
            grow_x=True,
        )