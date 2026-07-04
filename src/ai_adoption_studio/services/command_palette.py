"""Allow-listed operator command palette.

The operator console exposes a **fixed** set of vetted actions — never
free-form command input. Each action maps to a background job spawned via
``JobRunner``. Unknown actions are rejected. See ADR-005 and
SPEC-deployment-orchestration-v1.md §6.2.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_adoption_studio.models.job_record import JobRecord


@dataclass(frozen=True)
class CommandSpec:
    """A single allow-listed console action."""

    action: str
    label: str
    job_type: str
    description: str


# The complete allow-list. Anything not here is refused.
COMMAND_ALLOW_LIST: dict[str, CommandSpec] = {
    "health": CommandSpec(
        action="health",
        label="Health check",
        job_type="health",
        description="Poll Gateway, Runtime Manager and Control Centre health.",
    ),
    "deploy_lab": CommandSpec(
        action="deploy_lab",
        label="Deploy lab",
        job_type="deploy_lab",
        description="Deploy the playground lab for this lead (cp2 approved).",
    ),
    "validate": CommandSpec(
        action="validate",
        label="Validate",
        job_type="validate",
        description="Run delivery validation against the deployed lab.",
    ),
    "tail": CommandSpec(
        action="tail",
        label="Tail logs",
        job_type="tail",
        description="Stream the log of the selected job.",
    ),
}


class UnknownCommandError(ValueError):
    """Raised when an action is not on the allow-list."""


def is_allowed(action: str) -> bool:
    return action in COMMAND_ALLOW_LIST


def get_command(action: str) -> CommandSpec:
    """Return the spec for an allow-listed action or raise ``UnknownCommandError``."""
    try:
        return COMMAND_ALLOW_LIST[action]
    except KeyError as exc:
        raise UnknownCommandError(action) from exc


def list_commands() -> list[CommandSpec]:
    return list(COMMAND_ALLOW_LIST.values())


class CommandPalette:
    """Resolve allow-listed actions to spawned jobs.

    ``spawn_handlers`` maps a ``job_type`` to a callable that performs the work
    (injected so the palette never embeds infrastructure logic). Actions absent
    from the allow-list or without a handler are refused before any execution.
    """

    def __init__(self, jobs, spawn_handlers: dict[str, object]) -> None:
        self._jobs = jobs
        self._handlers = spawn_handlers

    def run(self, lead_id: str, action: str) -> JobRecord:
        spec = get_command(action)
        handler = self._handlers.get(spec.job_type)
        if handler is None:
            raise UnknownCommandError(f"No handler registered for {spec.job_type}")
        return self._jobs.spawn(lead_id, spec.job_type, handler)
