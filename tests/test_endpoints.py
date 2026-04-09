import importlib
import sys

MODULES_TO_CLEAR = [
    "main",
    "core.config",
    "routers.slynk",
]


def load_app(monkeypatch, tmp_path, project_name: str):
    monkeypatch.setenv("SLYNK_PROJECT_NAME", project_name)

    for module in MODULES_TO_CLEAR:
        sys.modules.pop(module, None)

    main = importlib.import_module("main")
    return importlib.reload(main)


def test_root_endpoint_uses_env_project_name(monkeypatch, tmp_path):
    main_module = load_app(monkeypatch, tmp_path, project_name="Testable Slynk")

    body = main_module.root()

    assert body["status"] == "ok"
    assert body["service"] == "Testable Slynk"
    assert str(main_module.app.url_path_for("root")) == "/"


def test_app_registers_lite_routes(monkeypatch, tmp_path):
    main_module = load_app(monkeypatch, tmp_path, project_name="Testable Slynk")

    route_paths = {route.path for route in main_module.app.routes}

    assert "/lite/sessions" in route_paths
    assert "/lite/analytics/overview" in route_paths
