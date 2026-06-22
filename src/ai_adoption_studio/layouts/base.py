"""MonsterUI layout shell with sidebar navigation."""

from __future__ import annotations

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio import __version__


def theme_headers():
    return Theme.slate.headers(highlightjs=True)


def sidebar(active: str, *, lead_id: str | None = None) -> FT:
    links = [
        ("inbox", "Inbox", "/"),
        ("export", "Export", "/export"),
        ("eoi", "Public EOI", "/eoi-form"),
    ]
    nav_items = []
    for key, label, href in links:
        cls = "block py-2 px-3 rounded hover:bg-slate-700"
        if key == active:
            cls += " bg-slate-700"
        nav_items.append(A(label, href=href, cls=cls))

    if lead_id:
        nav_items.append(
            Div(cls="mt-4 pt-4 border-t border-slate-700")(
                P(f"Lead: {lead_id}", cls="text-xs text-slate-400 mb-2"),
                A("Wizard", href=f"/wizard/{lead_id}", cls="block py-2 px-3 rounded text-sm"),
            )
        )

    return Aside(cls="w-64 bg-slate-900 text-white min-h-screen p-4 shrink-0")(
        H2("Adoption Studio", cls="text-lg font-semibold mb-6"),
        Nav(*nav_items),
        P(f"v{__version__}", cls="text-xs text-slate-400 mt-8"),
    )


def page_layout(title: str, active: str, *content: FT, lead_id: str | None = None) -> FT:
    return Html(
        Head(Title(title), Meta(charset="utf-8"), Meta(name="viewport", content="width=device-width"), *theme_headers()),
        Body(cls="flex min-h-screen bg-slate-50")(
            sidebar(active, lead_id=lead_id),
            Main(cls="flex-1 p-6")(Container(*content)),
        ),
    )


def wizard_layout(
    title: str,
    lead_id: str,
    stepper: FT,
    step_content: FT,
    *,
    org_name: str = "",
) -> FT:
    header = Div(cls="flex justify-between items-center mb-4")(
        H1(f"Wizard — {org_name or lead_id}", cls="text-2xl font-bold"),
        A("← Inbox", href="/", cls="text-blue-600 underline text-sm"),
    )
    return Html(
        Head(Title(title), Meta(charset="utf-8"), Meta(name="viewport", content="width=device-width"), *theme_headers()),
        Body(cls="flex min-h-screen bg-slate-50")(
            Div(id="wizard-stepper", cls="shrink-0")(stepper),
            Main(cls="flex-1 p-6")(
                header,
                Div(id="step-content")(step_content),
            ),
        ),
    )
