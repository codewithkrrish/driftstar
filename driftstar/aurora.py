"""Aurora bands: the soft coloured glow near the top of the sky.

The aurora is a vertical gradient of truecolour (RGB) values that slowly
shifts phase over time, so the colours breathe instead of sitting still.
It only occupies the top slice of the screen -- the rest of the sky stays
dark so the stars own it.

Rendering detail: the caller paints aurora cells as background colours on
spaces. That reads as a soft glow rather than a wall of characters, which
is the whole point -- it should feel like light, not text.
"""

from __future__ import annotations

import math

# Keyframes of the aurora palette, left to right across the band's height.
# Teal -> green -> violet, the colours I keep coming back to for night skies.
PALETTE: tuple[tuple[int, int, int], ...] = (
    (45, 212, 191),   # teal
    (74, 222, 128),   # green
    (167, 139, 250),  # violet
    (45, 212, 191),   # back to teal, so the band loops cleanly
)

# Fraction of screen height the aurora occupies at most.
BAND_FRACTION = 0.30


def _lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def _blend(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (_lerp(c1[0], c2[0], t), _lerp(c1[1], c2[1], t), _lerp(c1[2], c2[2], t))


def band_height(screen_height: int) -> int:
    """Rows the aurora occupies (never the whole screen)."""
    return max(1, int(screen_height * BAND_FRACTION))


def colour_at(row: int, height: int, time: float, x: int = 0, width: int = 1) -> tuple[int, int, int]:
    """Truecolour for one aurora cell.

    The gradient runs down the band, and a slow sine wave across x and
    time makes the colours drift sideways -- that's the "breathing".
    Returns black for rows below the band.
    """
    band = band_height(height)
    if row >= band:
        return (0, 0, 0)
    # Position through the palette, 0..1 down the band, plus sideways drift.
    pos = row / max(band - 1, 1)
    drift = 0.08 * math.sin(time * 0.25 + (x / max(width, 1)) * 2 * math.pi)
    pos = min(max(pos + drift, 0.0), 1.0)
    scaled = pos * (len(PALETTE) - 1)
    i = min(int(scaled), len(PALETTE) - 2)
    return _blend(PALETTE[i], PALETTE[i + 1], scaled - i)


def intensity_at(row: int, height: int, time: float) -> float:
    """How strong the glow is at this row: bright mid-band, fading at edges.

    Returns 0.0 below the band. Used to dim the colour so the top edge
    fades into black instead of cutting off hard.
    """
    band = band_height(height)
    if row >= band:
        return 0.0
    # Sine hump: 0 at the very top, peak mid-band, back towards 0 at the
    # bottom edge of the band. The bottom fade is gentler so the glow
    # melts into the starfield rather than stopping abruptly.
    t = row / max(band - 1, 1)
    return math.sin(math.pi * (0.15 + 0.85 * t)) * 0.55
