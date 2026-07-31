from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_container_initializes_only_nova_directories_then_drops_privileges() -> None:
    dockerfile = (REPOSITORY_ROOT / "backend" / "Dockerfile").read_text()
    entrypoint_path = REPOSITORY_ROOT / "backend" / "docker-entrypoint.sh"
    entrypoint_bytes = entrypoint_path.read_bytes()
    entrypoint = entrypoint_bytes.decode("utf-8")

    assert "gosu" in dockerfile
    assert 'ENTRYPOINT ["nova-entrypoint"]' in dockerfile
    assert "USER nova" not in dockerfile
    assert entrypoint_bytes.startswith(b"#!/bin/sh\n")
    assert b"\r\n" not in entrypoint_bytes
    assert "/files/intake /files/library /files/backups" in entrypoint
    assert 'exec gosu nova "$@"' in entrypoint


def test_repository_preserves_container_line_endings_on_windows() -> None:
    attributes = (REPOSITORY_ROOT / ".gitattributes").read_text(encoding="utf-8")

    assert "*.sh text eol=lf" in attributes
    assert "Dockerfile text eol=lf" in attributes


def test_compose_uses_the_directories_initialized_by_the_container() -> None:
    compose = (REPOSITORY_ROOT / "docker-compose.yml").read_text()

    assert "NOVA_INTAKE_PATH: /files/intake" in compose
    assert "NOVA_LIBRARY_PATH: /files/library" in compose
    assert "NOVA_BACKUP_PATH: /files/backups" in compose
    assert "NOVA_DATABASE_PATH: /data/nova.db" in compose


def test_dashboard_entry_page_revalidates_after_updates() -> None:
    nginx = (
        REPOSITORY_ROOT / "frontend" / "default.conf.template"
    ).read_text()

    assert "location = /index.html" in nginx
    assert "location = /chat.html" in nginx
    assert "location = /focus.html" in nginx
    assert "expires -1;" in nginx


def test_frontend_uses_a_strict_same_origin_api_gateway() -> None:
    compose = (REPOSITORY_ROOT / "docker-compose.yml").read_text()
    dockerfile = (REPOSITORY_ROOT / "frontend" / "Dockerfile").read_text()
    nginx = (
        REPOSITORY_ROOT / "frontend" / "default.conf.template"
    ).read_text()
    api = (
        REPOSITORY_ROOT / "frontend" / "src" / "lib" / "api.ts"
    ).read_text()

    assert 'const API_URL = import.meta.env.VITE_API_URL || "";' in api
    assert "VITE_API_URL: ${VITE_API_URL:-}" in compose
    assert (
        "NOVA_TAILSCALE_DNS_NAME: "
        "${NOVA_TAILSCALE_DNS_NAME:-nova.invalid}"
    ) in compose
    assert "ARG VITE_API_URL=" in dockerfile
    assert (
        "COPY default.conf.template "
        "/etc/nginx/templates/default.conf.template"
    ) in dockerfile
    assert (
        "server_name localhost 127.0.0.1 "
        "${NOVA_TAILSCALE_DNS_NAME};"
    ) in nginx
    assert "location /api/" in nginx
    assert "proxy_pass http://backend:8000;" in nginx
    assert "proxy_set_header Host localhost;" in nginx
    assert "proxy_buffering off;" in nginx
    assert "connect-src 'self';" in nginx
    assert "http://localhost:8000" not in nginx
