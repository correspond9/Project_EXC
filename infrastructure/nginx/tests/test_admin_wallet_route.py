from pathlib import Path


def test_admin_wallet_route_points_to_wallet_service_before_generic_admin_route():
    config_path = Path(__file__).resolve().parents[1] / "conf.d" / "default.conf"
    config = config_path.read_text(encoding="utf-8")

    wallet_location = "location /api/admin/wallet/ {"
    wallet_proxy = "proxy_pass http://wallet_service;"
    admin_location = "location /api/admin/ {"

    wallet_idx = config.find(wallet_location)
    admin_idx = config.find(admin_location)

    assert wallet_idx != -1, "Missing /api/admin/wallet/ location block"
    assert wallet_proxy in config[wallet_idx : wallet_idx + 220], "Wallet route must proxy to wallet_service"
    assert admin_idx != -1, "Missing generic /api/admin/ location block"
    assert wallet_idx < admin_idx, "Specific /api/admin/wallet/ rule must be before /api/admin/"
