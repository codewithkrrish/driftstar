"""Core starfield model: pure, testable, no terminal I/O in here.

A starfield is a set of stars on a float grid. Stars drift diagonally
(down and to the left, like the sky slowly turning) and wrap around the
edges, so the field never runs out. Depth layers give parallax: far stars
are dim and slow, near stars are bright and fast.

Everything here is deterministic given a seed, which is what makes it
testable -- and also means two runs with the same seed look identical,
which is handy for screenshots.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

# Characters per layer, dimmest to brightest. Kept to plain ASCII so the
# toy works in any terminal font, not just ones with fancy glyphs.
LAYER_CHARS = (".", "+", "*")

# Speed (cells per second) and brightness weight per layer, far -> near.
LAYER_SPEEDS = (2.0, 5.0, 11.0)
LAYER_BRIGHTNESS = (0.35, 0.65, 1.0)

MIN_DENSITY = 0.1
MAX_DENSITY = 2.0
# Roughly one star per this many cells at density 1.0. Tuned by eye: dense
# enough to feel alive, sparse enough that the aurora still shows through.
CELLS_PER_STAR = 45


@dataclass
class Star:
    """One star: a float position, a depth layer, and a twinkle phase."""

    x: float
    y: float
    layer: int
    phase: float = 0.0

    @property
    def char(self) -> str:
        return LAYER_CHARS[self.layer]

    @property
    def speed(self) -> float:
        return LAYER_SPEEDS[self.layer]

    def brightness(self, time: float) -> float:
        """Twinkle: base brightness of the layer, gently oscillating."""
        base = LAYER_BRIGHTNESS[self.layer]
        return base * (0.75 + 0.25 * math.sin(time * 1.5 + self.phase))


@dataclass
class ShootingStar:
    """A brief streak: head position, velocity, and remaining life."""

    x: float
    y: float
    vx: float
    vy: float
    life: float  # seconds remaining
    max_life: float = 0.9
    # Tail is drawn behind the head along the velocity direction.
    TAIL_LENGTH: int = 6

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    @property
    def alive(self) -> bool:
        return self.life > 0


@dataclass
class Starfield:
    """The whole sky: stars, an optional shooting star, and the clock."""

    width: int
    height: int
    density: float = 1.0
    speed: float = 1.0
    calm: bool = False
    seed: int | None = None
    stars: list[Star] = field(default_factory=list)
    shooting: ShootingStar | None = None
    time: float = 0.0

    def __post_init__(self) -> None:
        if self.width < 1 or self.height < 1:
            raise ValueError("width and height must be positive")
        if not MIN_DENSITY <= self.density <= MAX_DENSITY:
            raise ValueError(f"density must be between {MIN_DENSITY} and {MAX_DENSITY}")
        if self.speed <= 0:
            raise ValueError("speed must be positive")
        rng = random.Random(self.seed)
        # Caller-supplied stars (tests, mostly) are kept as-is; otherwise
        # generate a fresh sky for this size and density.
        if not self.stars:
            self.stars = [self._random_star(rng) for _ in range(self._target_count())]
        # Calm mode: no shooting stars, ever. It's meant to sit quietly
        # in the background, not demand attention.
        self._shooting_chance = 0.0 if self.calm else 0.12

    def _target_count(self) -> int:
        """How many stars for this area and density (at least a handful)."""
        count = int(self.width * self.height * self.density / CELLS_PER_STAR)
        return max(count, 8)

    def _random_star(self, rng: random.Random) -> Star:
        # Weighted towards far stars: most of the sky is distant.
        layer = rng.choices((0, 1, 2), weights=(5, 3, 2))[0]
        return Star(
            x=rng.uniform(0, self.width),
            y=rng.uniform(0, self.height),
            layer=layer,
            phase=rng.uniform(0, 2 * math.pi),
        )

    def update(self, dt: float, rng: random.Random | None = None) -> None:
        """Advance the sky by dt seconds."""
        if dt < 0:
            raise ValueError("dt must not be negative")
        self.time += dt
        drift = self.speed * (0.45 if self.calm else 1.0)
        for star in self.stars:
            # Diagonal drift: mostly sideways, slightly down.
            star.x -= star.speed * drift * dt
            star.y += star.speed * drift * dt * 0.25
            # Wrap: a star that leaves one edge re-enters from the other.
            star.x %= self.width
            star.y %= self.height
        if self.shooting is not None:
            self.shooting.update(dt)
            if not self.shooting.alive:
                self.shooting = None
        elif rng is not None and rng.random() < self._shooting_chance * dt:
            self.shooting = self._spawn_shooting_star(rng)

    def _spawn_shooting_star(self, rng: random.Random) -> ShootingStar:
        # Start near the top, streak down-left fast.
        return ShootingStar(
            x=rng.uniform(self.width * 0.3, self.width),
            y=rng.uniform(0, self.height * 0.3),
            vx=-rng.uniform(40, 70),
            vy=rng.uniform(12, 22),
            life=0.9,
        )

    def resize(self, width: int, height: int) -> None:
        """Adjust to a new terminal size, keeping stars in bounds."""
        if width < 1 or height < 1:
            raise ValueError("width and height must be positive")
        self.width, self.height = width, height
        for star in self.stars:
            star.x %= width
            star.y %= height
        # Top up or trim so the density still feels right.
        target = self._target_count()
        rng = random.Random()
        while len(self.stars) < target:
            self.stars.append(self._random_star(rng))
        del self.stars[target:]
