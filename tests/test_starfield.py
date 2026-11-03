"""Tests for the starfield model."""

import math

import pytest

from driftstar.starfield import (
    CELLS_PER_STAR,
    ShootingStar,
    Star,
    Starfield,
)


def test_star_count_scales_with_area_and_density():
    small = Starfield(width=20, height=10, density=0.5, seed=1)
    big = Starfield(width=80, height=40, density=1.0, seed=1)
    assert len(small.stars) < len(big.stars)
    assert len(small.stars) >= 8  # never an empty sky


def test_stars_stay_inside_after_update():
    field = Starfield(width=40, height=20, seed=7)
    for _ in range(200):
        field.update(0.1)
    for star in field.stars:
        assert 0 <= star.x < 40
        assert 0 <= star.y < 20


def test_stars_drift_down_left():
    star = Star(x=20.0, y=10.0, layer=2)
    field = Starfield(width=40, height=20, stars=[star])
    field.update(1.0)
    assert star.x < 20.0
    assert star.y > 10.0


def test_wrap_around_edges():
    star = Star(x=0.5, y=19.5, layer=2)
    field = Starfield(width=40, height=20, stars=[star])
    field.update(1.0)
    assert 0 <= star.x < 40
    assert 0 <= star.y < 20


def test_calm_mode_slows_drift():
    fast = Star(x=20.0, y=10.0, layer=2)
    calm = Star(x=20.0, y=10.0, layer=2)
    Starfield(width=40, height=20, stars=[fast]).update(1.0)
    Starfield(width=40, height=20, stars=[calm], calm=True).update(1.0)
    assert (20.0 - calm.x) < (20.0 - fast.x)


def test_invalid_dimensions_rejected():
    with pytest.raises(ValueError):
        Starfield(width=0, height=20)
    with pytest.raises(ValueError):
        Starfield(width=40, height=-1)


def test_invalid_density_and_speed_rejected():
    with pytest.raises(ValueError):
        Starfield(width=40, height=20, density=0.05)
    with pytest.raises(ValueError):
        Starfield(width=40, height=20, density=2.5)
    with pytest.raises(ValueError):
        Starfield(width=40, height=20, speed=0)


def test_negative_dt_rejected():
    field = Starfield(width=40, height=20, seed=3)
    with pytest.raises(ValueError):
        field.update(-0.1)


def test_same_seed_same_sky():
    a = Starfield(width=40, height=20, seed=42)
    b = Starfield(width=40, height=20, seed=42)
    assert [(s.x, s.y, s.layer) for s in a.stars] == [(s.x, s.y, s.layer) for s in b.stars]


def test_brightness_stays_in_range():
    star = Star(x=5.0, y=5.0, layer=2, phase=0.0)
    for t in [x * 0.25 for x in range(40)]:
        b = star.brightness(t)
        assert 0.0 < b <= 1.0


def test_shooting_star_dies():
    meteor = ShootingStar(x=10.0, y=5.0, vx=-50.0, vy=15.0, life=0.5)
    assert meteor.alive
    meteor.update(0.6)
    assert not meteor.alive


def test_resize_keeps_stars_in_bounds():
    field = Starfield(width=80, height=40, seed=9)
    field.resize(30, 12)
    assert field.width == 30 and field.height == 12
    for star in field.stars:
        assert 0 <= star.x < 30
        assert 0 <= star.y < 12


def test_resize_rejects_bad_size():
    field = Starfield(width=40, height=20, seed=9)
    with pytest.raises(ValueError):
        field.resize(0, 12)
