"""Frame composition and ANSI rendering.

The renderer turns a Starfield into a string of terminal escape codes.
It is deliberately separate from the animation loop: given a starfield
and a size, `render_frame` returns a complete frame string, which makes
it easy to test (no terminal needed) and easy to snapshot.

Colours: stars use a white-blue tint scaled by their twinkle brightness,
the aurora uses truecolour backgrounds. With --no-color everything is
plain characters, which also keeps the output pipeable.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import aurora
from .starfield import ShootingStar, Starfield

ESC = "\x1b"
RESET = f"{ESC}[0m"


@dataclass
class Cell:
    """One terminal cell: a character plus optional colours."""

    char: str = " "
    fg: tuple[int, int, int] | None = None
    bg: tuple[int, int, int] | None = None


def _star_fg(brightness: float) -> tuple[int, int, int]:
    """White with a cold blue tint, dimmed by the star's brightness."""
    v = int(200 * brightness + 55)
    return (v, v, 255)


def _dim(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(int(c * factor) for c in rgb)  # type: ignore[return-value]


def compose(field: Starfield, use_color: bool = True) -> list[list[Cell]]:
    """Build the cell grid for the current frame, aurora first, stars over it."""
    width, height = field.width, field.height
    grid: list[list[Cell]] = [[Cell() for _ in range(width)] for _ in range(height)]

    if use_color:
        for y in range(height):
            strength = aurora.intensity_at(y, height, field.time)
            if strength <= 0:
                continue
            for x in range(width):
                rgb = aurora.colour_at(y, height, field.time, x, width)
                grid[y][x].bg = _dim(rgb, strength)

    for star in field.stars:
        x, y = int(star.x), int(star.y)
        if 0 <= x < width and 0 <= y < height:
            cell = grid[y][x]
            cell.char = star.char
            if use_color:
                cell.fg = _star_fg(star.brightness(field.time))

    if field.shooting is not None:
        _paint_shooting_star(grid, field.shooting, width, height, use_color)

    return grid


def _paint_shooting_star(
    grid: list[list[Cell]],
    meteor: ShootingStar,
    width: int,
    height: int,
    use_color: bool,
) -> None:
    """Draw head + fading tail along the velocity direction."""
    # Tail steps backwards from the head; each step fainter.
    steps = meteor.TAIL_LENGTH
    for i in range(steps):
        frac = i / steps
        x = int(meteor.x - meteor.vx * frac * 0.05)
        y = int(meteor.y - meteor.vy * frac * 0.05)
        if 0 <= x < width and 0 <= y < height:
            cell = grid[y][x]
            cell.char = "-" if i else "*"
            if use_color:
                fade = 1.0 - frac
                cell.fg = (int(255 * fade), int(255 * fade), int(255 * fade))


def _cell_to_ansi(cell: Cell, prev_fg: tuple[int, int, int] | None,
                  prev_bg: tuple[int, int, int] | None) -> tuple[str, tuple[int, int, int] | None, tuple[int, int, int] | None]:
    """Encode one cell, only emitting colour codes when they change."""
    out = ""
    if cell.fg != prev_fg or cell.bg != prev_bg:
        out += RESET
        if cell.fg is not None:
            out += f"{ESC}[38;2;{cell.fg[0]};{cell.fg[1]};{cell.fg[2]}m"
        if cell.bg is not None:
            out += f"{ESC}[48;2;{cell.bg[0]};{cell.bg[1]};{cell.bg[2]}m"
    out += cell.char
    return out, cell.fg, cell.bg


def render_frame(field: Starfield, use_color: bool = True) -> str:
    """Full frame: cursor-home + one line per row, colours reset at the end."""
    grid = compose(field, use_color=use_color)
    lines = []
    for row in grid:
        parts: list[str] = []
        fg: tuple[int, int, int] | None = None
        bg: tuple[int, int, int] | None = None
        for cell in row:
            text, fg, bg = _cell_to_ansi(cell, fg, bg)
            parts.append(text)
        lines.append("".join(parts))
    return f"{ESC}[H" + f"\r\n".join(lines) + RESET
