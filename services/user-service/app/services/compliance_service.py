from dataclasses import dataclass

import httpx

from ..config import get_settings

settings = get_settings()


class AMLProviderNotConfiguredError(RuntimeError):
    pass


@dataclass
class AMLScreenResult:
    provider_name: str
    decision: str
    risk_score: float
    matched_entities: list[str]
    raw: dict

    @property
    def requires_review(self) -> bool:
        if self.decision in {"MATCH", "REVIEW", "BLOCK", "BLOCKED", "FAIL", "FAILED"}:
            return True
        return self.risk_score >= settings.AML_RISK_REVIEW_THRESHOLD


async def aml_screen_user(*, user_id: str, email: str, stage: str) -> AMLScreenResult:
    """
    Call AML provider endpoint when configured.
    LIVE gating must fail closed when provider is not configured.
    """
    if not settings.AML_PROVIDER_URL:
        raise AMLProviderNotConfiguredError(
            "AML provider is not configured (AML_PROVIDER_URL missing)."
        )

    headers = {"Content-Type": "application/json"}
    if settings.AML_PROVIDER_API_KEY:
        headers["Authorization"] = f"Bearer {settings.AML_PROVIDER_API_KEY}"

    payload = {
        "user_id": user_id,
        "email": email,
        "stage": stage,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(settings.AML_PROVIDER_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    decision = str(data.get("decision") or data.get("result") or "CLEAR").upper()
    risk_score = float(data.get("risk_score", 0.0) or 0.0)

    raw_matches = data.get("matched_entities") or []
    matched_entities = [str(x) for x in raw_matches] if isinstance(raw_matches, list) else []

    return AMLScreenResult(
        provider_name=str(data.get("provider_name") or "EXTERNAL_PROVIDER"),
        decision=decision,
        risk_score=risk_score,
        matched_entities=matched_entities,
        raw=data,
    )
