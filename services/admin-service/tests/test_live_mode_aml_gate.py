from pathlib import Path


def test_live_mode_switch_has_aml_provider_gate():
    source = (Path(__file__).resolve().parents[1] / "app" / "routers" / "admin.py").read_text(
        encoding="utf-8"
    )

    assert "body.trading_mode == TradingMode.LIVE and not settings.AML_PROVIDER_URL" in source
    assert "LIVE mode cannot be enabled while AML provider is not configured." in source
    assert "status_code=503" in source
