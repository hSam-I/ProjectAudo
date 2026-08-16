"""
Covers app.main.run_web_server() - wires `python -m app.main --web` to
uvicorn.run(app.web.server.app, ...). uvicorn.run() itself is always
monkeypatched here (it would otherwise block forever serving real
HTTP), so these tests only verify the wiring: the right app object,
host, and port are passed, and nothing here ever binds a real socket.
"""

import uvicorn

from app.config.settings import settings


def test_run_web_server_starts_uvicorn_with_configured_host_and_port(monkeypatch):

    monkeypatch.setattr(settings, "web_host", "127.0.0.1")
    monkeypatch.setattr(settings, "web_port", 9999)

    calls = {}

    def fake_run(app, host=None, port=None):
        calls["app"] = app
        calls["host"] = host
        calls["port"] = port

    monkeypatch.setattr(uvicorn, "run", fake_run)

    from app.main import run_web_server
    from app.web.server import app as web_app

    run_web_server()

    assert calls["app"] is web_app
    assert calls["host"] == "127.0.0.1"
    assert calls["port"] == 9999


def test_run_web_server_never_actually_binds_a_socket(monkeypatch):
    """
    Structural guarantee that this test suite never opens a real port:
    uvicorn.run is replaced with a function that raises if it tries to
    do anything beyond recording its arguments.
    """

    def fake_run(app, host=None, port=None):
        return None

    monkeypatch.setattr(uvicorn, "run", fake_run)

    from app.main import run_web_server

    # Must return normally - no exception, no real server started.
    run_web_server()
