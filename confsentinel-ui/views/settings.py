import rio
from state.gateway import BackendApiGateway, get_gateway


class SettingsPage(rio.Component):
    engine_url_input: str = ""
    auth_token_input: str = ""
    poll_interval_input: str = "10"
    test_status_message: str = ""
    test_status_color: str = "#64748B"
    save_notification: str = ""

    async def on_mount(self) -> None:
        gateway = get_gateway()
        self.engine_url_input = gateway.base_url
        self.auth_token_input = gateway.auth_token
        self.poll_interval_input = str(gateway.poll_interval)

    def build(self) -> rio.Component:
        gateway = get_gateway()

        test_msg_component = (
            rio.Text(
                self.test_status_message,
                style=rio.TextStyle(fill=rio.Color.from_hex(self.test_status_color)),
            )
            if self.test_status_message
            else rio.Spacer(min_height=0)
        )

        save_msg_component = (
            rio.Text(
                self.save_notification,
                style=rio.TextStyle(fill=rio.Color.from_hex("#16A34A"), font_weight="bold"),
            )
            if self.save_notification
            else rio.Spacer(min_height=0)
        )

        return rio.Column(
            rio.Text("Control Plane Connectivity & Settings", style="heading1"),
            rio.Text("Configure Governance API endpoints, authentication tokens, and polling frequencies", style="dim"),
            rio.Spacer(min_height=1.0),
            self._render_current_status(gateway),
            rio.Spacer(min_height=1.5),
            rio.Card(
                content=rio.Column(
                    rio.Text("Engine Connection Parameters", style="heading2"),
                    rio.Separator(),
                    rio.Spacer(min_height=0.5),
                    rio.Text("Governance Engine Base URL", style=rio.TextStyle(font_weight="bold")),
                    rio.TextInput(
                        text=self.bind().engine_url_input,
                        label="e.g. http://localhost:8080",
                    ),
                    rio.Text("Root HTTP endpoint exposing /api/v1/reports/* and /api/v1/rules", style="dim"),
                    rio.Spacer(min_height=0.8),
                    rio.Text("API / Governance Token (Optional)", style=rio.TextStyle(font_weight="bold")),
                    rio.TextInput(
                        text=self.bind().auth_token_input,
                        label="Token for authorized gateway ingress",
                    ),
                    rio.Text("Sent in X-Governance-Token and Authorization: Bearer headers", style="dim"),
                    rio.Spacer(min_height=0.8),
                    rio.Text("Background Sync Interval (Seconds)", style=rio.TextStyle(font_weight="bold")),
                    rio.TextInput(
                        text=self.bind().poll_interval_input,
                        label="Default: 10",
                    ),
                    rio.Spacer(min_height=1.0),
                    rio.Row(
                        rio.Button(
                            "Test Connection",
                            icon="material/compare-arrows",
                            style="plain-text",
                            on_press=self._on_test_connection,
                        ),
                        rio.Button(
                            "Save & Reconnect",
                            icon="material/settings",
                            style="major",
                            on_press=self._on_save_and_reconnect,
                        ),
                        spacing=1.0,
                    ),
                    rio.Spacer(min_height=0.5),
                    test_msg_component,
                    save_msg_component,
                    margin=1.5,
                    spacing=0.6,
                )
            ),
            margin=1.5,
            spacing=1.0,
        )

    def _render_current_status(self, gateway: BackendApiGateway) -> rio.Component:
        status_text = "CONNECTED" if gateway.is_connected else "DISCONNECTED"
        status_color = rio.Color.from_hex("#16A34A") if gateway.is_connected else rio.Color.from_hex("#DC2626")

        return rio.Card(
            content=rio.Row(
                rio.Icon(
                    "material/shield" if gateway.is_connected else "material/warning",
                    fill=status_color,
                ),
                rio.Column(
                    rio.Row(
                        rio.Text("Control Plane Status:", style=rio.TextStyle(font_weight="bold")),
                        rio.Text(
                            status_text,
                            style=rio.TextStyle(fill=status_color, font_weight="bold"),
                        ),
                        spacing=0.5,
                    ),
                    rio.Text(
                        f"Active Target: {gateway.base_url} (Round-trip: {gateway.last_latency_ms}ms)"
                        if gateway.is_connected
                        else f"Connection Error: {gateway.last_error or 'Engine unreachable'}",
                        style="dim",
                    ),
                    spacing=0.2,
                ),
                spacing=1.0,
                margin=1.0,
            )
        )

    async def _on_test_connection(self) -> None:
        self.save_notification = ""
        self.test_status_message = "Probing control plane endpoint..."
        self.test_status_color = "#0284C7"
        self.force_refresh()

        temp_gateway = BackendApiGateway(
            base_url=self.engine_url_input,
            auth_token=self.auth_token_input,
        )
        success, message, latency = await temp_gateway.test_connection()

        if success:
            self.test_status_message = f"✔ Success: {message} ({latency}ms)"
            self.test_status_color = "#16A34A"
        else:
            self.test_status_message = f"✖ Error: {message} ({latency}ms)"
            self.test_status_color = "#DC2626"
        self.force_refresh()

    async def _on_save_and_reconnect(self) -> None:
        gateway = get_gateway()
        try:
            interval = float(self.poll_interval_input.strip() or "10")
        except ValueError:
            interval = 10.0

        gateway.update_configuration(
            new_url=self.engine_url_input.strip(),
            new_token=self.auth_token_input.strip(),
            new_interval=interval,
            persist=True,
        )
        await gateway.refresh_all()
        self.save_notification = f"✔ Saved! Reconnected to {gateway.base_url}. Cache re-hydrated."
        self.test_status_message = ""
        self.force_refresh()