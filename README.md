# driftstar

An animated starfield for your terminal. Stars drift slowly across the
screen in three depth layers, a soft aurora breathes across the top, and
every now and then a shooting star streaks past. Nothing to configure,
nothing to learn — just run it and watch for a bit.

```
        .              *                 +
                        .          +
   .         +                        .          *
              .      *             .
                         +
```

## Why I built it

I kept a terminal open on a second monitor while working, and the blank
black screen bugged me. I wanted something calm to sit there — not a
clock, not a dashboard, just a quiet sky. Existing starfield toys I found
were either a screensaver you couldn't tweak or a demo buried inside a
bigger project. So I wrote the small thing I actually wanted: a sky with
a speed knob, a density knob, and a calm mode for when it's just
background.

## Install

Requires Python 3.10 or newer. No dependencies at all.

```bash
pip install git+https://github.com/codewithkrrish/driftstar.git
```

Or clone it and run it straight from the folder — it works the same,
since there's nothing to install besides the package itself:

```bash
git clone https://github.com/codewithkrrish/driftstar.git
cd driftstar
python -m driftstar
```

## Usage

```bash
driftstar                  # default sky, runs until Ctrl+C
driftstar --calm           # slow, dim, no shooting stars — background mode
driftstar --speed 0.5      # half speed, even calmer
driftstar --density 1.8    # a crowded sky
driftstar --duration 60    # run for 60 seconds, then stop on its own
driftstar --seed 42        # same sky every time (good for screenshots)
driftstar --no-color       # plain characters, no ANSI colours
```

| Flag | What it does | Default |
| --- | --- | --- |
| `--speed` | Drift speed multiplier | `1.0` |
| `--density` | How crowded the sky is, 0.1 to 2.0 | `1.0` |
| `--calm` | Slow, dim, no shooting stars | off |
| `--duration` | Stop after N seconds (0 = run until Ctrl+C) | `0` |
| `--fps` | Target frame rate: 15, 30 or 60 | `30` |
| `--no-color` | Plain characters only | off |
| `--seed` | Fix the random layout | none |

Controls: `Ctrl+C` to quit. Resize the window any time — the sky adjusts
and keeps going. If the window gets too small to show anything sensible
it just waits until you make it bigger again.

## How it's put together

```
driftstar/
  starfield.py   # the sky itself: stars, layers, shooting stars, wrapping
  aurora.py      # the gradient band at the top, and how it shifts over time
  renderer.py    # turns a sky into a frame of ANSI escape codes
  cli.py         # argument parsing and the animation loop
tests/
  test_starfield.py
  test_aurora_renderer.py
  test_cli.py
```

The model and the rendering are separate on purpose: `starfield.py`
never touches the terminal, so the whole sky is testable without one.
The frame builder is pure too — give it a sky, get back a string.

## Limitations, honestly

- It's an ANSI toy, so it looks best in a modern terminal (Windows
  Terminal, iTerm2, GNOME Terminal, Kitty, and friends). Old-style
  Windows consoles that don't understand ANSI escapes will show garbage.
- Truecolour is used for the aurora. On a 256-colour-only terminal it
  falls back poorly — use `--no-color` there.
- There's no mouse support and no interaction at all. It's a sky, not a
  game; if you want controls, `--speed` and `--density` are the whole
  remote.
- At 60 fps on a very large terminal it can use a noticeable bit of CPU
  — it's redrawing the whole screen every frame. 30 fps is the sweet
  spot, and `--calm` is cheaper still.

## License

MIT — see [LICENSE](LICENSE).

## Author

[Krrish](https://github.com/codewithkrrish) — I build small tools I
actually use, and put them here.
