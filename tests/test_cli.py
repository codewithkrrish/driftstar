"""Tests for CLI parsing and terminal-size guards."""

import pytest

from driftstar.cli import (
    MIN_TERMINAL_HEIGHT,
    MIN_TERMINAL_WIDTH,
    TerminalTooSmallError,
    check_size,
    frame_delay,
    parse_args,
)


def test_defaults():
    args = parse_args([])
    assert args.speed == 1.0
    assert args.density == 1.0
    assert args.calm is False
    assert args.duration == 0
    assert args.fps == 30
    assert args.no_color is False


def test_flags_parse():
    args = parse_args(["--speed", "2", "--density", "0.5", "--calm", "--fps", "60"])
    assert args.speed == 2.0
    assert args.density == 0.5
    assert args.calm is True
    assert args.fps == 60


def test_bad_speed_rejected():
    with pytest.raises(SystemExit):
        parse_args(["--speed", "0"])
    with pytest.raises(SystemExit):
        parse_args(["--speed", "-1"])


def test_bad_density_rejected():
    with pytest.raises(SystemExit):
        parse_args(["--density", "0.05"])
    with pytest.raises(SystemExit):
        parse_args(["--density", "3"])


def test_bad_duration_rejected():
    with pytest.raises(SystemExit):
        parse_args(["--duration", "-5"])


def test_bad_fps_rejected_by_argparse():
    with pytest.raises(SystemExit):
        parse_args(["--fps", "24"])


def test_frame_delay():
    assert frame_delay(30) == pytest.approx(1 / 30)
    assert frame_delay(60) == pytest.approx(1 / 60)


def test_check_size_accepts_minimum():
    check_size(MIN_TERMINAL_WIDTH, MIN_TERMINAL_HEIGHT)  # must not raise


def test_check_size_rejects_small_terminal():
    with pytest.raises(TerminalTooSmallError):
        check_size(10, 5)
    with pytest.raises(TerminalTooSmallError):
        check_size(100, 5)
