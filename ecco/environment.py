import math
import random
import pygame
from .config import ENABLE_CAUSTICS, CAUSTICS_BRIGHTNESS

class Environment:
    OCEAN_FLOOR = "Ocean Floor"
    ROCKY_REEF = "Rocky Reef"
    CORAL_COVE = "Coral Cove"
    BEACH = "Beach Shallows"
    OIL_RIG = "Oil Rig"
######################################################################
# 90s-style Procedural Renderer
######################################################################

# Simple 4x4 Bayer dither matrix
_BAYER4 = (
    (0,  8,  2, 10),
    (12, 4, 14,  6),
    (3, 11,  1,  9),
    (15, 7, 13,  5),
)

_tile_cache = {}
_silhouette_cache = {}
_caustics_cache = {}


def _lerp(a, b, t):
    return a + (b - a) * t


def _dither_color(c1, c2, t, x, y):
    """
    Ordered dither between two RGB colors using a 4x4 Bayer pattern.
    t in [0,1]. Returns a tuple RGB.
    """
    threshold = _BAYER4[y % 4][x % 4] / 16.0
    use_b = t > threshold
    a = c2 if use_b else c1
    b = c1 if use_b else c2
    # Mix a little for smoother feel
    mix = 0.25
    return (
        int(_lerp(a[0], b[0], mix)),
        int(_lerp(a[1], b[1], mix)),
        int(_lerp(a[2], b[2], mix)),
    )


def _make_tile(env_type, size=24):
    key = (env_type, size)
    if key in _tile_cache:
        return _tile_cache[key]

    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pa = pygame.PixelArray(surf)

    if env_type == Environment.ROCKY_REEF:
        c_mid = (58, 72, 84)
        c_dark = (34, 42, 50)
        c_light = (116, 132, 148)
    elif env_type == Environment.CORAL_COVE:
        c_mid = (120, 70, 100)
        c_dark = (80, 40, 60)
        c_light = (200, 120, 160)
    elif env_type == Environment.BEACH:
        c_mid = (196, 174, 132)
        c_dark = (150, 126, 90)
        c_light = (220, 206, 170)
    elif env_type == Environment.OIL_RIG:
        c_mid = (70, 70, 75)
        c_dark = (40, 40, 45)
        c_light = (110, 110, 120)
    else:  # OCEAN_FLOOR
        c_mid = (30, 60, 70)
        c_dark = (18, 36, 42)
        c_light = (70, 120, 130)

    # Base with dithered gradient
    for y in range(size):
        t = y / (size - 1)
        for x in range(size):
            col = _dither_color(c_mid, c_dark, t*0.8 + 0.1, x, y)
            pa[x, y] = surf.map_rgb(col)

    del pa

    # Edge bevel for tile illusion
    pygame.draw.line(surf, c_light, (0, 0), (size-1, 0))
    pygame.draw.line(surf, c_dark, (0, size-1), (size-1, size-1))
    pygame.draw.line(surf, tuple(max(0, c-20) for c in c_dark), (0, 0), (0, size-1))
    pygame.draw.line(surf, tuple(min(255, c+20) for c in c_light), (size-1, 0), (size-1, size-1))

    # Embedded pebble/hex texture
    rng = random.Random(1337)
    for _ in range(8):
        rx, ry = rng.randrange(2, size-2), rng.randrange(2, size-2)
        r = rng.randrange(2, 4)
        pygame.draw.circle(surf, c_light, (rx, ry), r, 1)
        pygame.draw.circle(surf, c_dark, (rx+1, ry+1), r, 1)

    _tile_cache[key] = surf
    return surf


def _get_silhouette_layer(w, h, env_type, seed, color=(0, 40, 50), alpha=90):
    key = (env_type, w, h, seed, color, alpha)
    if key in _silhouette_cache:
        return _silhouette_cache[key]

    s = pygame.Surface((w, h), pygame.SRCALPHA)
    rng = random.Random(seed)
    plank = int(h*0.5)

    # Silhouette plants/rocks
    for i in range(18):
        x = rng.randrange(0, w)
        base = h - rng.randrange(10, 40)
        tall = rng.randrange(20, 90)
        thickness = rng.randrange(2, 4)
        sway = rng.choice([-1, 1]) * rng.randrange(8, 22)
        pygame.draw.polygon(
            s,
            color,
            [(x, base), (x + sway//2, base - tall//2), (x + sway, base - tall), (x + sway + 4, base - tall + 8), (x+2, base-6)],
        )
    for i in range(8):
        x = rng.randrange(0, w)
        y = h - rng.randrange(30, 80)
        pygame.draw.ellipse(s, color, (x-40, y-20, 80, 40))

    s.set_alpha(alpha)
    _silhouette_cache[key] = s
    return s


def _get_caustics(size=128):
    if size in _caustics_cache:
        return _caustics_cache[size]
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    px = pygame.PixelArray(s)
    for y in range(size):
        for x in range(size):
            v = (
                math.sin((x*0.17) + (y*0.11)) +
                math.sin((x*0.07) - (y*0.19)) +
                math.sin((x*0.13) + (y*0.05))
            )
            # Normalize to 0..1
            v = (v + 3) / 6.0
            # Low-intensity bluish highlight pattern (prevents overbright washout)
            intensity = int(40 + v*40)  # 40..80
            px[x, y] = s.map_rgb((int(intensity*0.3), int(intensity*0.5), intensity))
    del px
    s.set_alpha(max(0, min(255, CAUSTICS_BRIGHTNESS)))
    _caustics_cache[size] = s
    return s


def _fill_vertical_gradient(surf, top, bottom):
    w, h = surf.get_width(), surf.get_height()
    for y in range(h):
        t = y / max(1, h-1)
        col = (
            int(_lerp(top[0], bottom[0], t)),
            int(_lerp(top[1], bottom[1], t)),
            int(_lerp(top[2], bottom[2], t)),
        )
        pygame.draw.line(surf, col, (0, y), (w, y))


def draw_environment(surf, env_type, offset, time_val):
    w, h = surf.get_width(), surf.get_height()
    surf.fill((0, 0, 0))

    # Background gradient per environment (deep water look)
    if env_type == Environment.OCEAN_FLOOR:
        _fill_vertical_gradient(surf, (6, 30, 40), (2, 14, 18))
        sil_color = (10, 40, 48)
    elif env_type == Environment.ROCKY_REEF:
        _fill_vertical_gradient(surf, (12, 36, 50), (4, 16, 24))
        sil_color = (14, 60, 70)
    elif env_type == Environment.CORAL_COVE:
        _fill_vertical_gradient(surf, (30, 40, 70), (20, 20, 40))
        sil_color = (60, 40, 70)
    elif env_type == Environment.BEACH:
        _fill_vertical_gradient(surf, (40, 110, 150), (20, 60, 100))
        sil_color = (30, 90, 120)
    else:  # OIL_RIG
        _fill_vertical_gradient(surf, (12, 16, 22), (6, 10, 14))
        sil_color = (20, 26, 34)

    # Parallax silhouettes (two layers)
    back = _get_silhouette_layer(w, h, env_type, seed=1, color=sil_color, alpha=60)
    mid = _get_silhouette_layer(w, h, env_type, seed=2, color=sil_color, alpha=90)
    # Parallax scroll slower than world
    bx = int(-offset * 0.2) % w
    mx = int(-offset * 0.4) % w
    surf.blit(back, (bx - w, 0))
    surf.blit(back, (bx, 0))
    surf.blit(mid, (mx - w, 0))
    surf.blit(mid, (mx, 0))

    # Midground tiled texture for 16-bit look
    tile = _make_tile(env_type, 24)
    tw, th = tile.get_width(), tile.get_height()

    # Draw a belt of tiles across bottom third
    rows = 4
    y_start = h - rows * th
    ox = int(-offset) % tw
    for r in range(rows):
        y = y_start + r * th
        for x in range(-tw, w + tw, tw):
            surf.blit(tile, (x + ox, y))
        # Bevel shadow between rows for depth
        pygame.draw.line(surf, (0, 0, 0), (0, y), (w, y), 1)

    # Environment-specific overlays
    if env_type in (Environment.OCEAN_FLOOR, Environment.ROCKY_REEF, Environment.CORAL_COVE):
        # Kelp foreground vines
        rng = random.Random(999)
        for x in range(0, w, 60):
            dx = x - int(offset * 0.8) % 60
            sway = int(math.sin(time_val * 0.002 + x) * 8)
            pygame.draw.line(surf, (40, 120, 70), (dx, y_start - 20), (dx + sway, y_start - 60), 3)
            pygame.draw.circle(surf, (30, 90, 60), (dx + sway, y_start - 60), 3)

    if env_type == Environment.OIL_RIG:
        # Struts and cables
        for x in range(0, w + 120, 120):
            dx = x - (int(offset * 0.8) % 120)
            pygame.draw.rect(surf, (80, 80, 90), (dx - 5, 0, 10, h))
            for y in range(40, h, 48):
                pygame.draw.line(surf, (70, 70, 80), (dx - 24, y), (dx + 24, y - 24), 2)

    # Water caustics overlay (moving) — guarded and alpha blended
    if ENABLE_CAUSTICS:
        ca = _get_caustics(128)
        cx = int(time_val * 0.06) % ca.get_width()
        cy = int(time_val * 0.04) % ca.get_height()
        for y in range(-cy, h, ca.get_height()):
            for x in range(-cx, w, ca.get_width()):
                surf.blit(ca, (x, y))
