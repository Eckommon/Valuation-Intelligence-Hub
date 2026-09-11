"""CLI Web command tests / CLI Web 명령 테스트."""

from __future__ import annotations

from pathlib import Path

from valuation_hub import cli


ROOT = Path(__file__).resolve().parents[1]


def test_cli_web_dispatches_to_shared_web_adapter(monkeypatch) -> None:
    called: dict[str, object] = {}

    def fake_serve(*, host: str, port: int, root: Path | None) -> None:
        called.update(host=host, port=port, root=root)

    monkeypatch.setattr(cli, "serve_web", fake_serve)
    rc = cli.main(["--root", str(ROOT), "web", "--host", "127.0.0.1", "--port", "9876"])
    assert rc == 0
    assert called == {"host": "127.0.0.1", "port": 9876, "root": ROOT}


def test_cli_web_rejects_json_mode(capsys) -> None:
    rc = cli.main(["--root", str(ROOT), "--json", "web"])
    assert rc == 2
    captured = capsys.readouterr()
    assert "not valid with web" in captured.out
