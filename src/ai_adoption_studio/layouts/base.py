from fasthtml.common import *  # noqa: F403

from ai_adoption_studio import __version__


def sidebar(active: str) -> FT:
    links = [
        ("leads", "Leads", "/"),
        ("export", "Export", "/export"),
        ("eoi", "Public EOI", "/eoi-form"),
    ]
    return Aside(cls="w-64 bg-slate-900 text-white min-h-screen p-4")(
        H2("Adoption Studio", cls="text-lg font-semibold mb-6"),
        Nav(
            *[
                A(
                    label,
                    href=href,
                    cls="block py-2 px-3 rounded hover:bg-slate-700 "
                    + ("bg-slate-700" if key == active else ""),
                )
                for key, label, href in links
            ],
        ),
        P(f"v{__version__}", cls="text-xs text-slate-400 mt-8"),
    )


def page_layout(title: str, active: str, *content: FT) -> FT:
    return Html(
        Head(
            Title(title),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Script(src="https://cdn.tailwindcss.com"),
            Script(src="https://unpkg.com/htmx.org@2.0.4"),
        ),
        Body(cls="flex bg-slate-50")(sidebar(active), Main(cls="flex-1 p-8")(*content)),
    )
