"""Command-line entry point and the animation loop.

Thin by design: parsing lives here, the sky lives in starfield.py, and
the picture lives in renderer.py. Nothing in this file is hard to test
except the loop itself, which is why the frame-rate math is kept in the
tiny `frame_delay` helper.
"""

from __future__ import annotations

import argparse
import random
import shutil
import sys
import time

from .renderer import render_frame
from .starfield import MAX_DENSITY, MIN_DENSITY, Starfield

DEFAULT_FPS = 30
MIN_TERMINAL_WIDTH = 20
MIN_TERMINAL_HEIGHT = 10


class TerminalTooSmallError(Exception):
    """Raised when the terminal can't fit a readable sky."""


def frame_delay(fps: int) -> float:
    """Seconds per frame; fps is validated by argparse (choices below)."""
    return 1.0 / fps


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="driftstar",
        description="An animated starfield for your terminal, with a slow "
        "aurora breathing across the top. Runs until you press Ctrl+C.",
    )
    parser.add_argument(
        "--speed", type=float, default=1.0,
        help="drift speed multiplier, e.g. 0.5 is half speed, 2 is double (default: 1.0)",
    )
    parser.add_argument(
        "--density", type=float, default=1.0,
        help=f"how crowded the sky is, {MIN_DENSITY} (sparse) to {MAX_DENSITY} (busy) (default: 1.0)",
    )
    parser.add_argument(
        "--calm", action="store_true",
        help="slow, dim, no shooting stars -- for sitting in the background",
    )
    parser.add_argument(
        "--duration", type=float, default=0,
        help="stop after this many seconds (default: 0, run until Ctrl+C)",
    )
    parser.add_argument(
        "--fps", type=int, default=DEFAULT_FPS, choices=(15, 30, 60),
        help="target frame rate (default: 30)",
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="plain characters only, no ANSI colours",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="fix the random layout, so the same sky repeats (useful for screenshots)",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    args = build_parser().parse_args(argv)
    if args.speed <= 0:
        raise SystemExit("--speed must be positive")
    if not MIN_DENSITY <= args.density <= MAX_DENSITY:
        raise SystemExit(f"--density must be between {MIN_DENSITY} and {MAX_DENSITY}")
    if args.duration < 0:
        raise SystemExit("--duration must not be negative")
    return args


def terminal_size() -> tuple[int, int]:
    size = shutil.get_terminal_size()
    return size.columns, size.lines


def check_size(width: int, height: int) -> None:
    if width < MIN_TERMINAL_WIDTH or height < MIN_TERMINAL_HEIGHT:
        raise TerminalTooSmallError(
            f"terminal is {width}x{height}, driftstar needs at least "
            f"{MIN_TERMINAL_WIDTH}x{MIN_TERMINAL_HEIGHT} -- try maximising the window"
        )


def run(args: argparse.Namespace) -> int:
    """Run the animation. Returns 0 on a clean stop, 1 on a terminal error."""
    width, height = terminal_size()
    try:
        check_size(width, height)
    except TerminalTooSmallError as exc:
        print(f"driftstar: {exc}", file=sys.stderr)
        return 1

    field = Starfield(
        width=width, height=height,
        density=args.density, speed=args.speed,
        calm=args.calm, seed=args.seed,
    )
    rng = random.Random(args.seed)
    use_color = not args.no_color
    delay = frame_delay(args.fps)

    # Hide the cursor and clear the screen; restored in the finally block
    # so Ctrl+C never leaves the terminal in a weird state.
    sys.stdout.write("\x1b[?25l\x1b[2J")
    sys.stdout.flush()

    # SIGWINCH (terminal resized) is handled by re-reading the size each
    # frame -- simpler and more portable than a signal handler.
    start = time.monotonic()
    try:
        while True:
            new_width, new_height = terminal_size()
            if (new_width, new_height) != (width, height):
                width, height = new_width, new_height
                try:
                    check_size(width, height)
                except TerminalTooSmallError:
                    # Too small for a frame; wait for the user to resize back.
                    time.sleep(0.5)
                    continue
                field.resize(width, height)
            field.update(delay, rng)
            sys.stdout.write(render_frame(field, use_color=use_color))
            sys.stdout.flush()
            if args.duration and time.monotonic() - start >= args.duration:
                break
            time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        # Show cursor, clear, home -- leave the terminal as we found it.
        sys.stdout.write("\x1b[?25h\x1b[2J\x1b[H")
        sys.stdout.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return run(parse_args(argv))
    except TerminalTooSmallError as exc:  # pragma: no cover - defensive
        print(f"driftstar: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
