"""
QR Code Generator Utility
=========================
Generates a QR code PNG (as bytes) for a given URL.
Requires: qrcode[pil] (pip install qrcode[pil])
Falls back gracefully if the library is not installed.
"""

from __future__ import annotations
import io


def generate_qr_png(
    url: str,
    box_size: int = 8,
    border: int = 3,
    fill_color: str = "#000000",
    back_color: str = "#FFFFFF",
) -> bytes | None:
    """
    Generate a QR code image as PNG bytes.

    Parameters
    ----------
    url        : Target URL to encode
    box_size   : Pixel size of each QR box
    border     : Number of boxes in the quiet zone (border)
    fill_color : Foreground color (hex or name)
    back_color : Background color (hex or name)

    Returns
    -------
    PNG image bytes, or None if `qrcode` is not installed.
    """
    try:
        import qrcode  # type: ignore
        from qrcode.image.pil import PilImage  # type: ignore

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(
            image_factory=PilImage,
            fill_color=fill_color,
            back_color=back_color,
        )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    except ImportError:
        return None
    except Exception:
        return None


GITHUB_REPO_URL = "https://github.com/60140-Ikrama/ecg-hrv-suite"
