from pathlib import Path


def test_compliance_service_fails_closed_when_provider_missing():
    source = (Path(__file__).resolve().parents[1] / "app" / "services" / "compliance_service.py").read_text(
        encoding="utf-8"
    )

    assert "class AMLProviderNotConfiguredError" in source
    assert "if not settings.AML_PROVIDER_URL:" in source
    assert "raise AMLProviderNotConfiguredError" in source
    assert "INTERNAL_STUB" not in source


def test_kyc_approval_failure_path_writes_audit_log():
    source = (Path(__file__).resolve().parents[1] / "app" / "routers" / "kyc.py").read_text(
        encoding="utf-8"
    )

    assert "action=\"AML_CHECK_FAILED\"" in source
    assert "status_code=503" in source
    assert "AML screening failed" in source
