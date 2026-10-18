from collections.abc import Callable
from typing import Any, Dict
import rio

from state.gateway import get_gateway


class DriftPage(rio.Component):
    selected_service_id: str = ""
    drift_details: Dict[str, Any] = {}

    async def on_mount(self) -> None:
        """Lifecycle hook: Safe location to initialize state outside build()."""
        gateway = get_gateway()
        summary = gateway.summary_cache or {}
        matrix = summary.get("matrix") or summary.get("services") or []

        if matrix and not self.selected_service_id:
            first_svc = matrix[0]
            first_id = str(first_svc.get("id") or first_svc.get("name") or first_svc.get("serviceName") or "")
            if first_id:
                self.selected_service_id = first_id
                self.drift_details = await gateway.fetch_service_drift(first_id)
                self.force_refresh()

    def _make_service_handler(self, service_id: str) -> Callable[[], None]:
        def handler() -> None:
            self.session.create_task(self._select_service(service_id))
        return handler

    async def _select_service(self, service_id: str) -> None:
        self.selected_service_id = service_id
        gateway = get_gateway()
        self.drift_details = await gateway.fetch_service_drift(service_id)
        self.force_refresh()

    async def _on_manual_refresh(self) -> None:
        gateway = get_gateway()
        await gateway.refresh_all()
        if self.selected_service_id:
            self.drift_details = await gateway.fetch_service_drift(self.selected_service_id)
        self.force_refresh()

    def build(self) -> rio.Component:
        gateway = get_gateway()
        summary = gateway.summary_cache or {}
        matrix = summary.get("matrix") or summary.get("services") or []

        # Pure read: compute active ID into a local variable without assigning to self
        active_service_id = self.selected_service_id
        if not active_service_id and matrix:
            first_svc = matrix[0]
            active_service_id = str(first_svc.get("id") or first_svc.get("name") or first_svc.get("serviceName") or "")

        service_buttons = []
        for m in matrix:
            sid = str(m.get("id") or m.get("name") or m.get("serviceName") or "")
            sname = str(m.get("name") or m.get("serviceName") or sid or "Service")
            is_selected = (sid == active_service_id)
            service_buttons.append(
                rio.Button(
                    sname,
                    style="major" if is_selected else "plain-text",
                    on_press=self._make_service_handler(sid),
                )
            )

        components: list[rio.Component] = [
            rio.Row(
                rio.Column(
                    rio.Text("Environment Configuration Parity & Drift", style="heading1"),
                    rio.Text("Detect configuration parameter drift between non-prod profiles and production", style="dim"),
                    spacing=0.2,
                ),
                rio.Spacer(),
                rio.Button(
                    "Refresh Drift",
                    icon="material/history",
                    style="plain-text",
                    on_press=self._on_manual_refresh,
                ),
            ),
            rio.Spacer(min_height=1.0),
        ]

        if service_buttons:
            components.append(rio.Row(*service_buttons, spacing=0.5))
            components.append(rio.Spacer(min_height=1.0))

        components.append(self._render_drift_view(active_service_id))

        return rio.Column(
            *components,
            spacing=1.0,
            grow_x=True,
        )

    def _render_drift_view(self, active_service_id: str) -> rio.Component:
        if not active_service_id:
            return rio.Card(
                content=rio.Column(
                    rio.Text("No microservices available to analyze drift.", style=rio.TextStyle(font_weight="bold")),
                    rio.Text("Run an evaluation scan or publish service configurations first.", style="dim"),
                    margin=1.5,
                    spacing=0.4,
                )
            )

        status = self.drift_details.get("status", "NO_DRIFT_DATA")
        unbound = self.drift_details.get("unboundBaseKeys", []) or self.drift_details.get("unbound_base_keys", [])

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
                    rio.Text(f"Drift Status for {active_service_id}:", style="heading2"),
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