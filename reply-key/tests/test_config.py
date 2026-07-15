from __future__ import annotations

import json

from replykey.config import AppConfig, ConfigStore, DEFAULT_BASE_URL, DEFAULT_MODEL


def test_defaults_match_product_spec() -> None:
    config = AppConfig()

    assert config.api_base_url == DEFAULT_BASE_URL == "https://api.openai.com/v1"
    assert config.model == DEFAULT_MODEL == "gpt-5.6-luna"
    assert config.hotkey == "Ctrl+Alt+R"
    assert config.session_timeout_minutes == 30
    assert config.launch_at_startup is False


def test_round_trip_uses_appdata_and_never_serializes_api_key(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    store = ConfigStore()
    config = AppConfig(model="compatible-model", tone="礼貌专业", launch_at_startup=True)

    store.save(config)

    assert store.path == tmp_path / "ReplyKey" / "config.json"
    raw = store.path.read_text(encoding="utf-8")
    assert "api_key" not in raw.lower()
    assert "secret" not in raw.lower()
    assert store.load() == config


def test_malformed_file_falls_back_to_defaults(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{not-json", encoding="utf-8")

    assert ConfigStore(path).load() == AppConfig()


def test_unknown_and_invalid_values_are_safely_normalized(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "api_base_url": "  https://example.test/v1/  ",
                "model": "  demo-model  ",
                "hotkey": "",
                "session_timeout_minutes": -5,
                "unexpected": "ignored",
                "api_key": "must-not-load",
            }
        ),
        encoding="utf-8",
    )

    config = ConfigStore(path).load()

    assert config.api_base_url == "https://example.test/v1"
    assert config.model == "demo-model"
    assert config.hotkey == "Ctrl+Alt+R"
    assert config.session_timeout_minutes == 30
    assert not hasattr(config, "api_key")

