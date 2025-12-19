import importlib
import sys

MODULES_TO_CLEAR = [
    "main",
    "core.config",
    "core.database_sql",
    "core.security",
    "models.user",
    "models.user_settings",
    "models.share",
    "models.reverse_share",
    "models.file",
    "routers.auth",
    "routers.user",
    "routers.shares",
    "routers.reverse",
    "routers.files",
]


def load_app(monkeypatch, tmp_path, project_name: str):
    monkeypatch.setenv("SLYNK_PROJECT_NAME", project_name)
    monkeypatch.setenv("SLYNK_DATABASE_URL", f"sqlite:///{tmp_path/'test.db'}")
    monkeypatch.setenv("SLYNK_UPLOAD_DIR", str(tmp_path / "uploads"))

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