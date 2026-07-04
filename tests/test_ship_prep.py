from __future__ import annotations

from ai_adoption_studio.services.ship_prep import write_nginx_reference


def test_write_nginx_reference_uses_manifest_hostname(tmp_path) -> None:
    manifest = {"access": {"public_url": "https://playground-acme.example.com"}}
    out = write_nginx_reference(tmp_path, manifest)
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "playground-acme.example.com" in text
    assert "ship-prep/nginx.reference.conf" in str(out).replace("\\", "/")
