"""Operator ops layer — single-command startup orchestration.

This package is a thin operator convenience layer. It shells out to
``deployment-catalog`` docker compose and launches processes; it never
generates compose files or manages container lifecycle. See
docs/design/SPEC-operator-single-command-v1.md and ADR-005.
"""
