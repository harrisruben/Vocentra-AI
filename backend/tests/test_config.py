import importlib
import sys
from pathlib import Path


def test_settings_load_env_from_backend_directory(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(repo_root)
    sys.modules.pop("app.core.config", None)

    import app.core.config as config_module
    config_module = importlib.reload(config_module)

    assert config_module.settings.VAPI_API_KEY == "a3beda73-96e4-47c3-b00d-b7c0248e9dee"
    assert config_module.settings.ENVIRONMENT == "development"
