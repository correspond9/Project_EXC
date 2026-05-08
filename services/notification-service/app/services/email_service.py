"""
Email notification service using aiosmtplib.

Sends HTML emails for:
  - Order fills
  - Margin call warnings
  - Liquidation notices
  - Price alert triggers

All sends are fire-and-forget: failures are logged but never raise.
"""
import logging

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import settings

log = logging.getLogger(__name__)


def _html_wrap(title: str, body_html: str) -> str:
    """Minimal HTML email template."""
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }}
    .card {{ background: #fff; border-radius: 8px; padding: 24px; max-width: 560px; margin: auto; }}
    h2 {{ color: #1a1a2e; margin-top: 0; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
    .badge-green  {{ background: #d4edda; color: #155724; }}
    .badge-yellow {{ background: #fff3cd; color: #856404; }}
    .badge-red    {{ background: #f8d7da; color: #721c24; }}
    .footer {{ margin-top: 24px; font-size: 11px; color: #888; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>{title}</h2>
    {body_html}
    <div class="footer">
      XChange Simulation Platform &mdash; This is an automated message. Do not reply.
    </div>
  </div>
</body>
</html>"""


async def _send(to_email: str, subject: str, html_body: str) -> None:
    """Internal: send a single HTML email."""
    if not settings.SMTP_HOST or not to_email:
        log.debug("Email send skipped — SMTP not configured or no recipient")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            use_tls=settings.SMTP_PORT == 465,
            start_tls=settings.SMTP_PORT == 587,
        )
        log.info("Email sent to %s: %s", to_email, subject)
    except Exception as exc:
        log.warning("Email send failed to %s: %s", to_email, exc)


async def send_fill_email(
    to_email: str,
    symbol: str,
    side: str,
    quantity: str,
    price: str,
) -> None:
    subject = f"XChange — Order Filled: {side} {symbol}"
    html = _html_wrap(
        f"Order Filled — {symbol}",
        f"""
        <p><span class="badge badge-green">FILLED</span></p>
        <table style="width:100%; border-collapse:collapse; margin-top:12px;">
          <tr><td style="padding:6px 0; color:#555;">Symbol</td><td><strong>{symbol}</strong></td></tr>
          <tr><td style="padding:6px 0; color:#555;">Side</td><td><strong>{side}</strong></td></tr>
          <tr><td style="padding:6px 0; color:#555;">Quantity</td><td><strong>{quantity}</strong></td></tr>
          <tr><td style="padding:6px 0; color:#555;">Fill Price</td><td><strong>{price} USDT</strong></td></tr>
        </table>
        """,
    )
    await _send(to_email, subject, html)


async def send_margin_call_email(
    to_email: str,
    symbol: str,
    margin_ratio: str,
) -> None:
    subject = "XChange — Margin Call Warning"
    html = _html_wrap(
        "Margin Call Warning",
        f"""
        <p><span class="badge badge-yellow">MARGIN CALL</span></p>
        <p>Your margin ratio on <strong>{symbol}</strong> has dropped to
           <strong>{margin_ratio}%</strong>.</p>
        <p>Please top up your margin balance to avoid liquidation.</p>
        """,
    )
    await _send(to_email, subject, html)


async def send_liquidation_email(
    to_email: str,
    symbol: str,
    side: str,
    liquidation_price: str,
    realised_pnl: str,
) -> None:
    subject = f"XChange — Position Liquidated: {symbol}"
    html = _html_wrap(
        f"Position Liquidated — {symbol}",
        f"""
        <p><span class="badge badge-red">LIQUIDATED</span></p>
        <table style="width:100%; border-collapse:collapse; margin-top:12px;">
          <tr><td style="padding:6px 0; color:#555;">Symbol</td><td><strong>{symbol}</strong></td></tr>
          <tr><td style="padding:6px 0; color:#555;">Side</td><td><strong>{side}</strong></td></tr>
          <tr><td style="padding:6px 0; color:#555;">Liquidation Price</td><td><strong>{liquidation_price} USDT</strong></td></tr>
          <tr><td style="padding:6px 0; color:#555;">Realised P&L</td><td><strong>{realised_pnl} USDT</strong></td></tr>
        </table>
        """,
    )
    await _send(to_email, subject, html)


async def send_price_alert_email(
    to_email: str,
    symbol: str,
    condition: str,
    target_price: str,
    current_price: str,
) -> None:
    subject = f"XChange — Price Alert Triggered: {symbol}"
    html = _html_wrap(
        f"Price Alert — {symbol}",
        f"""
        <p><span class="badge badge-green">ALERT TRIGGERED</span></p>
        <p>Your price alert for <strong>{symbol}</strong> has been triggered.</p>
        <table style="width:100%; border-collapse:collapse; margin-top:12px;">
          <tr><td style="padding:6px 0; color:#555;">Condition</td><td><strong>Price {condition} {target_price} USDT</strong></td></tr>
          <tr><td style="padding:6px 0; color:#555;">Current Price</td><td><strong>{current_price} USDT</strong></td></tr>
        </table>
        """,
    )
    await _send(to_email, subject, html)


async def send_kyc_submitted_email(to_email: str) -> None:
    subject = "XChange — KYC Submission Received"
    html = _html_wrap(
        "KYC Submission Received",
        """
        <p><span class="badge badge-yellow">UNDER REVIEW</span></p>
        <p>We have received your KYC submission. Our compliance team will review
           your documents within <strong>1–3 business days</strong>.</p>
        <p>You will be notified by email once a decision has been made.</p>
        """,
    )
    await _send(to_email, subject, html)


async def send_kyc_approved_email(to_email: str) -> None:
    subject = "XChange — KYC Approved"
    html = _html_wrap(
        "KYC Approved",
        """
        <p><span class="badge badge-green">APPROVED</span></p>
        <p>Congratulations! Your KYC verification has been <strong>approved</strong>.</p>
        <p>Your account is now eligible to be activated for Live trading. Please
           contact your account manager or wait for your administrator to activate
           Live mode on your account.</p>
        """,
    )
    await _send(to_email, subject, html)


async def send_kyc_rejected_email(to_email: str, reason: str) -> None:
    subject = "XChange — KYC Rejected"
    reason_html = f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""
    html = _html_wrap(
        "KYC Rejected",
        f"""
        <p><span class="badge badge-red">REJECTED</span></p>
        <p>Unfortunately your KYC submission has been <strong>rejected</strong>.</p>
        {reason_html}
        <p>Please re-submit with the correct documents. If you believe this is an
           error, contact support.</p>
        """,
    )
    await _send(to_email, subject, html)
