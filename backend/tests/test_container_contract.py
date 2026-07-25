from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_container_initializes_only_nova_directories_then_drops_privileges() -> None:
    dockerfile = (REPOSITORY_ROOT / "backend" / "Dockerfile").read_text()
    entrypoint = (
        REPOSITORY_ROOT / "backend" / "docker-entrypoint.sh"
    ).read_text()

    assert "gosu" in dockerfile
    assert 'ENTRYPOINT ["nova-entrypoint"]' in dockerfile
    assert "USER nova" not in dockerfile
    assert "/files/intake /files/library /files/backups" in entrypoint
    assert 'exec gosu nova "$@"' in entrypoint


def test_compose_uses_the_directories_initialized_by_the_container() -> None:
    compose = (REPOSITORY_ROOT / "docker-compose.yml").read_text()

    assert "NOVA_INTAKE_PATH: /files/intake" in compose
    assert "NOVA_LIBRARY_PATH: /files/library" in compose
    assert "NOVA_BACKUP_PATH: /files/backups" in compose
    assert "NOVA_DATABASE_PATH: /data/nova.db" in compose
