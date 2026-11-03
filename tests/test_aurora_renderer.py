"""Tests for the aurora gradient and the renderer."""

from driftstar import aurora
from driftstar.renderer import compose, render_frame
from driftstar.starfield import Star, Starfield


def test_band_height_is_a_fraction_of_screen():
    assert aurora.band_height(40) == 12
    assert aurora.band_height(10) >= 1
    assert aurora.band_height(40) < 40


def test_colour_below_band_is_black():
    assert aurora.colour_at(30, 40, time=0.0) == (0, 0, 0)


def test_colour_components_are_valid_bytes():
    for row in range(aurora.band_height(40)):
        r, g, b = aurora.colour_at(row, 40, time=1.5, x=10, width=80)
        assert all(0 <= c <= 255 for c in (r, g, b))


def test_intensity_fades_to_zero_below_band():
    assert aurora.intensity_at(39, 40, time=0.0) == 0.0
    assert aurora.intensity_at(0, 40, time=0.0) > 0


def test_render_frame_has_one_line_per_row():
    field = Starfield(width=20, height=10, seed=5)
    frame = render_frame(field, use_color=False)
    body = frame.replace("\x1b[H", "").replace("\x1b[0m", "")
    assert len(body.split("\r\n")) == 10


def test_render_frame_contains_stars():
    field = Starfield(width=20, height=10, seed=5)
    frame = render_frame(field, use_color=False)
    assert any(ch in frame for ch in (".", "+", "*"))


def test_no_color_frame_has_no_colour_codes():
    field = Starfield(width=20, height=10, seed=5)
    frame = render_frame(field, use_color=False)
    assert "38;2" not in frame
    assert "48;2" not in frame


def test_color_frame_uses_truecolour():
    field = Starfield(width=20, height=10, seed=5)
    frame = render_frame(field, use_color=True)
    assert "38;2" in frame  # star foregrounds


def test_star_overwrites_aurora_cell():
    # A star placed in the aurora band must win over the background glow.
    star = Star(x=2.0, y=1.0, layer=2)
    field = Starfield(width=20, height=10, stars=[star])
    grid = compose(field, use_color=True)
    assert grid[1][2].char == "*"
    assert grid[1][2].fg is not None


def test_empty_field_renders_blank_rows():
    field = Starfield(width=10, height=5, seed=1)
    field.stars = []
    frame = render_frame(field, use_color=False)
    body = frame.replace("\x1b[H", "").replace("\x1b[0m", "")
    assert body.split("\r\n") == [" " * 10] * 5
