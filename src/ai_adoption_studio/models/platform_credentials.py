"""Per-lead Gateway credentials provisioned at deploy."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LabUserCredential(BaseModel):
    username: str
    email: str
    role: str
    password: str | None = None


class OperatorCredential(BaseModel):
    username: str
    email: str
    role: str = "developer"
    api_key: str
    key_prefix: str
    user_id: str | None = None


class PlatformCredentials(BaseModel):
    schema_version: str = "1.0.0"
    lead_id: str
    gateway_base_url: str
    provisioned_at: str
    super_user: LabUserCredential
    operator: OperatorCredential
