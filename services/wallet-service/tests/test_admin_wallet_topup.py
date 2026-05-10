from __future__ import annotations

import sys
import uuid
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.config import settings  # noqa: E402
from app.database import get_db  # noqa: E402
from app.routers import wallet as wallet_router  # noqa: E402

app = FastAPI()
app.include_router(wallet_router.admin_router)


class _FakeResult:
    def __init__(self, wallet_obj):
        self._wallet_obj = wallet_obj

    def scalar_one_or_none(self):
        return self._wallet_obj


class _FakeSelect:
    def __init__(self, _model):
        self.conditions = ()

    def where(self, *conditions):
        self.conditions = conditions
        return self


class _FakeSession:
    def __init__(self):
        self.wallets = {}

    async def execute(self, stmt):
        user_id = None
        currency = None
        for cond in stmt.conditions:
            left_name = getattr(getattr(cond, "left", None), "name", None)
            right_value = getattr(getattr(cond, "right", None), "value", None)
            if left_name == "user_id":
                user_id = right_value
            if left_name == "currency":
                currency = right_value
        key = (str(user_id), str(currency))
        return _FakeResult(self.wallets.get(key))

    def add(self, wallet_obj):
        key = (str(wallet_obj.user_id), str(wallet_obj.currency))
        self.wallets[key] = wallet_obj

    async def commit(self):
        return None

    async def refresh(self, _obj):
        return None


def _admin_token() -> str:
    payload = {"sub": str(uuid.uuid4()), "role": "ADMIN"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _non_admin_token() -> str:
    payload = {"sub": str(uuid.uuid4()), "role": "STUDENT"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def test_admin_wallet_topup_persists_balance_across_calls(monkeypatch):
    fake_db = _FakeSession()

    async def _override_get_db():
        yield fake_db

    monkeypatch.setattr(wallet_router, "select", lambda model: _FakeSelect(model))
    app.dependency_overrides[get_db] = _override_get_db

    try:
        client = TestClient(app)
        user_id = str(uuid.uuid4())
        headers = {"Authorization": f"Bearer {_admin_token()}"}

        first = client.post(
            "/api/admin/wallet/topup",
            headers=headers,
            json={"user_id": user_id, "currency": "USDT", "amount": "100.00"},
        )
        assert first.status_code == 200
        assert Decimal(first.json()["new_balance"]) == Decimal("100.00")

        second = client.post(
            "/api/admin/wallet/topup",
            headers=headers,
            json={"user_id": user_id, "currency": "USDT", "amount": "50.00"},
        )
        assert second.status_code == 200
        assert Decimal(second.json()["new_balance"]) == Decimal("150.00")
    finally:
        app.dependency_overrides.clear()


def test_admin_wallet_topup_rejects_missing_auth():
    client = TestClient(app)
    user_id = str(uuid.uuid4())

    response = client.post(
        "/api/admin/wallet/topup",
        json={"user_id": user_id, "currency": "USDT", "amount": "100.00"},
    )

    assert response.status_code == 401


def test_admin_wallet_topup_rejects_non_admin_role():
    client = TestClient(app)
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {_non_admin_token()}"}

    response = client.post(
        "/api/admin/wallet/topup",
        headers=headers,
        json={"user_id": user_id, "currency": "USDT", "amount": "100.00"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"
