from collections.abc import Callable
import rio
from state.gateway import get_gateway


class CatalogPage(rio.Component):
    search_query: str = ""
    selected_category: str = "ALL"

    async def on_mount(self) -> None:
        gateway = get_gateway()
        await gateway.refresh_all()
        self.force_refresh()

    async def _on_manual_refresh(self) -> None:
        gateway = get_gateway()
        await gateway.refresh_all()
        self.force_refresh()

    def _set_cat(self, cat: str) -> None:
        self.selected_category = cat

    def _make_cat_handler(self, cat: str) -> Callable[[], None]:
        def handler() -> None:
            self._set_cat(cat)
        return handler

    def build(self) -> rio.Component:
        gateway = get_gateway()
        rules = gateway.rules_cache

        categories = ["ALL", "SECURITY", "RELIABILITY", "RESOURCE", "PARITY"]

        filtered_rules = []
        for r in rules:
            if not isinstance(r, dict):
                continue
            if self.selected_category != "ALL" and r.get("category", "").upper() != self.selected_category:
                continue
            if self.search_query.strip():
                query = self.search_query.lower()
                matches_code = query in r.get("ruleCode", "").lower()
                matches_name = query in r.get("name", "").lower()
                if not (matches_code or matches_name):
                    continue
            filtered_rules.append(r)

        return rio.Column(
            rio.Row(
                rio.Column(
                    rio.Text("Central Policy Catalog", style="heading1"),
                    rio.Text(f"Total Rules Loaded: {len(rules)}", style="dim"),
                    spacing=0.2,
                ),
                rio.Spacer(),
                rio.Button(
                    "Refresh Rules",
                    icon="material/history",
                    style="plain-text",
                    on_press=self._on_manual_refresh,
                ),
            ),
            rio.Spacer(min_height=0.8),
            rio.Row(
                rio.TextInput(
                    text=self.bind().search_query,
                    label="Search rules by name or code...",
                ),
                *[
                    rio.Button(
                        cat,
                        style="major" if self.selected_category == cat else "plain-text",
                        on_press=self._make_cat_handler(cat),
                    )
                    for cat in categories
                ],
                spacing=0.5,
            ),
            rio.Spacer(min_height=1.0),
            self._render_rule_cards(filtered_rules),
            spacing=1.0,
            grow_x=True,
        )

    def _render_rule_cards(self, rules: list) -> rio.Component:
        if not rules:
            return rio.Card(
                content=rio.Column(
                    rio.Text("No rules match current filter criteria.", style="bold"),
                    rio.Text("If you recently published rules, click 'Refresh Rules' above.", style="dim"),
                    margin=1.5,
                    spacing=0.5,
                )
            )

        cards = []
        for r in rules:
            is_active = r.get("active", True)
            cards.append(
                rio.Card(
                    content=rio.Column(
                        rio.Row(
                            rio.Text(r.get("ruleCode", "RULE-000"), style="heading2"),
                            rio.Text(r.get("name", "Rule Name"), style=rio.TextStyle(font_weight="bold")),
                            rio.Spacer(),
                            rio.Text(
                                "ACTIVE" if is_active else "INACTIVE",
                                style=rio.TextStyle(
                                    fill=rio.Color.from_hex("#16A34A" if is_active else "#94A3B8"),
                                    font_weight="bold",
                                ),
                            ),
                            spacing=1.0,
                        ),
                        rio.Separator(),
                        rio.Row(
                            rio.Text(f"Category: {r.get('category', 'GENERAL')}", style="dim"),
                            rio.Text(f"Severity: {r.get('severity', 'BLOCKER')}", style=rio.TextStyle(font_weight="bold")),
                            rio.Text(f"Check: {r.get('checkType', '')}", style="dim"),
                            rio.Text(f"Pattern: {r.get('targetPattern', '')}", style="dim"),
                            spacing=1.5,
                        ),
                        rio.Text(f"Remediation: {r.get('remediation', '')}"),
                        spacing=0.5,
                        margin=1.0,
                    ),
                    grow_x=True,
                )
            )

        return rio.Column(*cards, spacing=0.8, grow_x=True)