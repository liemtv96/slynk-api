import importlib

import boto3

import app.config as config_module
import app.storage.s3 as s3_module


def test_get_s3_client_omits_empty_endpoint(monkeypatch):
    captured = {}

    def fake_client(service_name, **kwargs):
        captured["service_name"] = service_name
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setenv("SLYNK_S3_ENDPOINT_URL", "   ")
    monkeypatch.setattr(boto3, "client", fake_client)

    importlib.reload(config_module)
    importlib.reload(s3_module)
    s3_module.get_s3_client.cache_clear()
    s3_module.get_s3_client()

    assert captured["service_name"] == "s3"
    assert "endpoint_url" not in captured["kwargs"]


def test_get_s3_client_uses_configured_endpoint(monkeypatch):
    captured = {}

    def fake_client(service_name, **kwargs):
        captured["service_name"] = service_name
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setenv("SLYNK_S3_ENDPOINT_URL", "https://s3.ap-southeast-1.amazonaws.com")
    monkeypatch.setattr(boto3, "client", fake_client)

    importlib.reload(config_module)
    importlib.reload(s3_module)
    s3_module.get_s3_client.cache_clear()
    s3_module.get_s3_client()

    assert captured["service_name"] == "s3"
    assert captured["kwargs"]["endpoint_url"] == "https://s3.ap-southeast-1.amazonaws.com"


def test_get_s3_client_includes_session_token(monkeypatch):
    captured = {}

    def fake_client(service_name, **kwargs):
        captured["service_name"] = service_name
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setenv("AWS_SESSION_TOKEN", "session-token")
    monkeypatch.setattr(boto3, "client", fake_client)

    importlib.reload(config_module)
    importlib.reload(s3_module)
    s3_module.get_s3_client.cache_clear()
    s3_module.get_s3_client()

    assert captured["service_name"] == "s3"
    assert captured["kwargs"]["aws_session_token"] == "session-token"
