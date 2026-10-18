import argparse
import asyncio
from collections.abc import Callable
import rio

from state.gateway import BackendApiGateway, get_gateway
from views.catalog import CatalogPage
from views.drift import DriftPage
from views.overview import OverviewPage
from views.settings import SettingsPage
from views.triage import TriagePage


class ConfSentinelApp(rio.Component):
    current_page: str = "Overview"

    async def on_mount(self) -> None:
        gateway = get_gateway()
        await gateway.refresh_all()
        self.session.create_task(self._background_poll_loop())

    async def _background_poll_loop(self) -> None:
        gateway = get_gateway()
        while True:
            await asyncio.sleep(gateway.poll_interval)
            await gateway.refresh_all()
            self.force_refresh()

    def build(self) -> rio.Component:
        gateway = get_gateway()

        body_components: list[rio.Component] = []

        # Only mount the connection banner if backend is unreachable
        if not gateway.is_connected:
            body_components.append(self._connection_banner(gateway))

        body_components.append(
            rio.Row(
                self._sidebar(),
                rio.Container(
                    content=self._render_active_page(),
                    grow_x=True,
                    grow_y=True,
                    margin=1.0,
                ),
                grow_y=True,
                spacing=1.0,
            )
        )

        return rio.Column(
            *body_components,
            grow_y=True,
        )

    def _nav(self, page_name: str) -> None:
        self.current_page = page_name

    def _make_nav_handler(self, page_name: str) -> Callable[[], None]:
        def handler() -> None:
            self._nav(page_name)
        return handler

    def _sidebar(self) -> rio.Component:
        nav_items = [
            ("Overview", "material/dashboard"),
            ("Run Explorer", "material/history"),
            ("Policy Catalog", "material/shield"),
            ("Parity Drift", "material/compare-arrows"),
            ("Settings", "material/settings"),
        ]

        buttons = []
        for label, icon in nav_items:
            is_active = self.current_page == label
            buttons.append(
                rio.Button(
                    label,
                    icon=icon,
                    style="major" if is_active else "plain-text",
                    on_press=self._make_nav_handler(label),
                )
            )

        return rio.Card(
            content=rio.Column(
                rio.Row(
                    rio.Icon("material/security", fill=rio.Color.from_hex("#0284C7")),
                    rio.Text("ConfSentinel", style="heading2"),
                    spacing=0.5,
                    margin_y=0.5,
                ),
                rio.Separator(),
                rio.Spacer(min_height=0.5),
                *buttons,
                rio.Spacer(),
                spacing=0.5,
                margin=0.8,
            ),
            min_width=14,
        )

    def _render_active_page(self) -> rio.Component:
        if self.current_page == "Overview":
            return OverviewPage()
        if self.current_page == "Run Explorer":
            return TriagePage()
        if self.current_page == "Policy Catalog":
            return CatalogPage()
        if self.current_page == "Parity Drift":
            return DriftPage()
        return SettingsPage()

    def _connection_banner(self, gateway: BackendApiGateway) -> rio.Component:
        msg = gateway.last_error or f"Control plane unreachable at {gateway.base_url}."
        return rio.Banner(
            text=f"Connection Alert: {msg} — Configure connection parameters in Settings.",
            style="danger",
        )


def parse_cli_args() -> tuple[str, str, float, int]:
    parser = argparse.ArgumentParser(description="ConfSentinel Rio Governance Dashboard")
    parser.add_argument("--engine-url", default=None)
    parser.add_argument("--token", default=None)
    parser.add_argument("--poll-interval", type=float, default=10.0)
    parser.add_argument("--port", type=int, default=8000)
    args, _ = parser.parse_known_args()
    return args.engine_url, args.token, args.poll_interval, args.port


cli_url, cli_token, cli_interval, cli_port = parse_cli_args()
gateway = get_gateway()
if cli_url:
    gateway.base_url = cli_url.rstrip("/")
if cli_token:
    gateway.auth_token = cli_token
if cli_interval:
    gateway.poll_interval = cli_interval

app = rio.App(
    build=ConfSentinelApp,
    theme=rio.Theme.from_colors(
        primary_color=rio.Color.from_hex("#0284C7"),
        background_color=rio.Color.from_hex("#F8FAFC"),
    ),
)

if __name__ == "__main__":
    app.run_in_browser(port=cli_port)