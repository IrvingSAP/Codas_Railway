"""Generación y verificación TOTP (CODAS_SECURITY §3, §8)."""

from __future__ import annotations

import base64
import io

import pyotp
import qrcode
from qrcode.image.pil import PilImage


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_provisioning_uri(*, secret: str, account_name: str, issuer: str = "CODAS") -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=account_name, issuer_name=issuer)


def verify_totp_code(*, secret: str, code: str) -> bool:
    if not (secret or "").strip() or not (code or "").strip():
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code.strip(), valid_window=1)


def qr_code_png_data_uri(*, provisioning_uri: str) -> str:
    """Imagen PNG en data URI para <img src="...">."""
    img = qrcode.make(provisioning_uri, image_factory=PilImage)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"
