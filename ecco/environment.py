import math
import pygame

class Environment:
    OCEAN_FLOOR = "Ocean Floor"
    ROCKY_REEF = "Rocky Reef"
    CORAL_COVE = "Coral Cove"
    BEACH = "Beach Shallows"
    OIL_RIG = "Oil Rig"
def _lerp(a, b, t):
    return a + (b - a) * t



def _lerp_color(c1, c2, t):
    return tuple(int(_lerp(c1[i], c2[i], t)) for i in range(3))


def draw_environment(surf, env_type, offset, time_val, time_of_day, ambient_density=1.0):

    w, h = surf.get_width(), surf.get_height()

    # Parallax offsets for mid/foreground layers (relative to world offset)
    mid_offset = int(offset * 0.6)
    fg_offset = int(offset * 0.85)

    # --- Time of day colour selection ---
    t = time_of_day % 24.0
    day_sky = (135, 206, 235)
    day_water = (0, 105, 148)
    dawn_sky = (255, 150, 80)
    dawn_water = (60, 110, 130)
    dusk_sky = (255, 100, 60)
    dusk_water = (0, 60, 90)
    night_sky = (10, 10, 40)
    night_water = (0, 20, 30)

    overlay_alpha = 0
    moon_alpha = 0
    if 6 <= t < 8:  # dawn
        r = (t - 6) / 2
        sky_color = _lerp_color(dawn_sky, day_sky, r)
        water_color = _lerp_color(dawn_water, day_water, r)
        overlay_alpha = int(120 * (1 - r))
        moon_alpha = int(255 * (1 - r))
    elif 8 <= t < 18:  # day
        sky_color = day_sky
        water_color = day_water
    elif 18 <= t < 20:  # dusk
        r = (t - 18) / 2
        sky_color = _lerp_color(day_sky, dusk_sky, r)
        water_color = _lerp_color(day_water, dusk_water, r)
        overlay_alpha = int(120 * r)
        moon_alpha = int(255 * r)
    else:  # night
        sky_color = night_sky
        water_color = night_water
        overlay_alpha = 120
        moon_alpha = 255
        if t < 6:  # fade out towards dawn
            r = t / 6
            sky_color = _lerp_color(night_sky, dawn_sky, r)
            water_color = _lerp_color(night_water, dawn_water, r)
            overlay_alpha = int(120 * (1 - r))
            moon_alpha = int(255 * (1 - r))

    # clear previous frame to avoid artifacts and apply base water colour
    surf.fill(water_color)

    # Create separate layers for parallax scrolling
    background = pygame.Surface((w, h), pygame.SRCALPHA)
    midground = pygame.Surface((w, h), pygame.SRCALPHA)
    foreground = pygame.Surface((w, h), pygame.SRCALPHA)

    if env_type == Environment.OCEAN_FLOOR:
        for y in range(h):
            depth = y / h

            line_col = _lerp_color(water_color,
                                   (max(0, water_color[0] - 30),
                                    max(0, water_color[1] - 50),
                                    max(0, water_color[2] - 70)), depth)
            pygame.draw.line(surf, line_col, (0, y), (w, y))

        step_mid = max(30, int(40 / max(0.5, min(2.0, ambient_density))))
        for x in range(0, w + step_mid, step_mid):
            dx = x - (mid_offset % 40)
            height = 10 + int(math.sin((x + mid_offset) * 0.02) * 5)
            pygame.draw.ellipse(midground, (100, 90, 60),
                                (dx - 20, h - height, 40, height * 2))
        step_fg = max(60, int(80 / max(0.5, min(2.0, ambient_density))))
        for x in range(0, w, step_fg):
            dx = x - (fg_offset % 80)
            pygame.draw.polygon(foreground, (180, 120, 50),
                                [(dx, h-25), (dx+5, h-15), (dx+15, h-12),
                                 (dx+7, h-5), (dx+10, h+5), (dx, h),
                                 (dx-10, h+5), (dx-7, h-5), (dx-15, h-12),
                                 (dx-5, h-15)])
        # Wreck silhouette in the deep
        ship_x = w - ((offset // 3) % (w + 200))
        pygame.draw.polygon(background, (20, 30, 40),
                            [(ship_x - 120, h - 60), (ship_x - 20, h - 80),
                             (ship_x + 40, h - 75), (ship_x + 60, h - 60),
                             (ship_x + 120, h - 55), (ship_x + 100, h - 40),
                             (ship_x - 130, h - 40)])
        # Passing whale silhouette for depth
        whale_x = (w + 400) - ((offset // 5) % (w + 800))
        whale_y = h//2 + int(math.sin(time_val*0.0015) * 20)
        pygame.draw.ellipse(background, (15, 22, 30), (whale_x - 80, whale_y - 16, 160, 32))
        # Tail fluke
        pygame.draw.polygon(background, (15, 22, 30),
                            [(whale_x - 90, whale_y), (whale_x - 110, whale_y - 10), (whale_x - 110, whale_y + 10)])
        # Dorsal fin
        pygame.draw.polygon(background, (12, 18, 25),
                            [(whale_x + 10, whale_y - 18), (whale_x + 20, whale_y - 4), (whale_x, whale_y - 6)])
        # Sparse seaweed
        weed_step = max(40, int(50 / max(0.5, min(2.0, ambient_density))))
        for x in range(0, w, weed_step):
            dx = x - (fg_offset % 50)
            sway = int(math.sin(time_val*0.002 + x) * 6)
            pygame.draw.line(foreground, (20, 80, 40), (dx, h-30), (dx+sway, h-8), 3)

    elif env_type == Environment.ROCKY_REEF:
        step_col = max(40, int(60 / max(0.5, min(2.0, ambient_density))))
        for x in range(0, w + 60, step_col):
            dx = x - (mid_offset % 60)
            pygame.draw.rect(midground, (60, 65, 70),
                             (dx - 15, h - 80, 30, 80))
            pygame.draw.polygon(midground, (50, 55, 60),
                                [(dx - 20, h), (dx + 20, h),
                                 (dx + 10, h - 90), (dx - 10, h - 90)])
        # Cavern openings and urchins
        for x in range(0, w, 120):
            cx = x - (mid_offset % 120) + 40
            pygame.draw.ellipse(background, (20, 20, 30), (cx, h-70, 50, 30))
        for x in range(0, w, max(70, int(90 / max(0.5, min(2.0, ambient_density))))):
            dx = x - (fg_offset % 90)
            pygame.draw.circle(foreground, (60, 60, 80), (dx, h-18), 6)
            for a in range(0, 360, 30):
                ex = dx + int(math.cos(math.radians(a)) * 9)
                ey = h-18 + int(math.sin(math.radians(a)) * 9)
                pygame.draw.line(foreground, (90, 90, 110), (dx, h-18), (ex, ey), 1)
        # Kelp sway
        for x in range(0, w, max(35, int(45 / max(0.5, min(2.0, ambient_density))))):
            dx = x - (fg_offset % 45)
            sway = int(math.sin(time_val*0.002 + x) * 5)
            pygame.draw.line(foreground, (30, 100, 60), (dx, h-60), (dx+sway, h-20), 3)

    elif env_type == Environment.CORAL_COVE:
        for y in range(h):
            depth = y / h

            line_col = _lerp_color(water_color,
                                   (water_color[0] + 30,
                                    max(0, water_color[1] - 40),
                                    max(0, water_color[2] - 30)), depth)
            pygame.draw.line(surf, line_col, (0, y), (w, y))
    
        for x in range(0, w + 50, max(35, int(50 / max(0.5, min(2.0, ambient_density))))):
            dx = x - (mid_offset % 50)
            pygame.draw.circle(midground, (255, 120, 150), (dx, h - 20), 15)
            pygame.draw.circle(midground, (255, 140, 170), (dx, h - 20), 12)
            for branch in range(-2, 3):
                by = h - 40 - abs(branch) * 10
                bx = dx + branch * 8
                pygame.draw.line(midground, (255, 100, 50),
                                 (dx, h - 10), (bx, by), 3)
        # Shoals of fish silhouettes in background
        for x in range(0, w, max(70, int(90 / max(0.5, min(2.0, ambient_density))))):
            dx = x - (mid_offset % 90)
            fy = h//2 + int(math.sin(time_val*0.003 + x) * 20)
            pygame.draw.ellipse(background, (10, 40, 50), (dx, fy, 12, 6))
            pygame.draw.polygon(background, (10, 40, 50),
                                [(dx+12, fy+3), (dx+16, fy), (dx+16, fy+6)])
        # Foreground anemones
        for x in range(0, w, max(90, int(110 / max(0.5, min(2.0, ambient_density))))):
            dx = x - (fg_offset % 110)
            base_y = h-18
            pygame.draw.circle(foreground, (255, 180, 200), (dx, base_y), 6)
            for a in range(-60, 61, 20):
                tipx = dx + int(math.cos(math.radians(a)) * 10)
                tipy = base_y - 6 - int(abs(math.sin(time_val*0.005 + a))*3)
                pygame.draw.line(foreground, (255, 120, 160), (dx, base_y-2), (tipx, tipy), 2)
        # Occasional giant ray silhouette gliding across
        if int((time_val // 4000) % max(1, int(3 / max(0.5, min(2.0, ambient_density))))) == 0:
            rx = (w + 200) - ((offset // 2) % (w + 400))
            ry = h//2 + int(math.sin(time_val*0.001) * 15)
            pygame.draw.polygon(background, (12, 35, 45),
                                [(rx, ry), (rx-50, ry-20), (rx-20, ry), (rx-50, ry+20)])
            pygame.draw.line(background, (12, 35, 45), (rx-20, ry), (rx+20, ry+10), 2)


    elif env_type == Environment.BEACH:
        pygame.draw.rect(surf, sky_color, (0, 0, w, h//3))
        pygame.draw.rect(surf, water_color, (0, h//3, w, h - h//3))
        for x in range(0, w, 30):
            sx = x + int(math.sin(time_val * 0.001 + x) * 10)
            pygame.draw.line(surf, _lerp_color(water_color, sky_color, 0.3),
                             (sx, h//3), (sx - 20, h), 2)
        pygame.draw.rect(surf, (230, 210, 170), (0, h - 30, w, 30))
        for x in range(0, w + 40, 40):
            dx = x - (offset % 40)
            pygame.draw.circle(surf, (255, 230, 200), (dx, h - 15), 3)
        # Sun and clouds (hidden at night)
        sun_alpha = 0 if overlay_alpha else 255
        if sun_alpha:
            sun = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(sun, (255, 255, 200), (20, 20), 20)
            sun.set_alpha(sun_alpha)
            surf.blit(sun, (w - 60, 10))
            for cx in range(0, w, 100):
                cloud = pygame.Surface((60, 20), pygame.SRCALPHA)
                pygame.draw.ellipse(cloud, (250, 250, 255), (0, 0, 60, 20))
                cloud.set_alpha(sun_alpha)
                surf.blit(cloud, (cx - 20, 10))
        # Kelp in shallows
        for x in range(0, w, max(50, int(70 / max(0.5, min(2.0, ambient_density))))):
            dx = x - (fg_offset % 70)
            sway = int(math.sin(time_val*0.003 + x) * 8)
            pygame.draw.line(foreground, (20, 120, 80), (dx, h-28), (dx+sway, h-8), 3)
        # Tiny boats on horizon
        for x in range(0, w, max(120, int(160 / max(0.5, min(2.0, ambient_density))))):
            bx = x - (mid_offset % 160)
            pygame.draw.rect(background, (80, 80, 90), (bx, h//3 - 6, 14, 4))
            pygame.draw.polygon(background, (80, 80, 90), [(bx+6, h//3 - 6), (bx+6, h//3 - 16), (bx+12, h//3 - 6)])
        # Occasional dolphin arc silhouettes
        for x in range(0, w, max(180, int(220 / max(0.5, min(2.0, ambient_density))))):
            dx = x - (mid_offset % 220)
            dy = h//3 - 12 + int(math.sin((time_val*0.002 + x)*0.5) * 6)
            pygame.draw.arc(background, (60, 70, 85), (dx, dy, 24, 10), 0.0, 3.14, 2)
            pygame.draw.polygon(background, (60, 70, 85), [(dx+18, dy+5), (dx+24, dy+2), (dx+24, dy+8)])

    elif env_type == Environment.OIL_RIG:

        for x in range(0, w + 120, 120):
            dx = x - (mid_offset % 120)
            pygame.draw.rect(midground, (80, 80, 80), (dx - 5, 0, 10, h))
            for y in range(40, h, 40):
                pygame.draw.line(midground, (70, 70, 70), (dx - 20, y), (dx + 20, y - 20), 3)
        for x in range(0, w + 80, 80):

            dx = x - (offset % 80) + int(math.sin(time_val * 0.0005 + x) * 20)
            pygame.draw.ellipse(surf, (20, 10, 30), (dx - 30, h - 60, 60, 20))
        # Suspended cables and oil droplets
        for x in range(0, w, 100):
            dx = x - (offset % 100)
            pygame.draw.line(surf, (90, 90, 90), (dx, 0), (dx+20, h//2), 2)
        if int(time_val*0.002) % 2 == 0:
            drop_x = (time_val//20 % w)
            pygame.draw.circle(surf, (10, 10, 20), (int(drop_x), h-40), 3)
        # Scuba diver patrolling near the rig with flashlight
        swim_x = w - ((offset // 2) % (w + 240)) + 120
        swim_y = h//2 + int(math.sin(time_val*0.003) * 20)
        diver = pygame.Surface((30, 16), pygame.SRCALPHA)
        # body
        pygame.draw.ellipse(diver, (50, 80, 110), (6, 5, 16, 6))
        # tank
        pygame.draw.rect(diver, (180, 180, 190), (0, 4, 8, 8))
        # fins
        pygame.draw.polygon(diver, (40, 60, 90), [(22, 8), (28, 5), (28, 11)])
        # head + mask
        pygame.draw.circle(diver, (220, 220, 220), (6, 8), 3)
        pygame.draw.rect(diver, (120, 180, 200), (4, 6, 6, 4))
        pos_x = (swim_x % (w + 240)) - 30
        pos_y = swim_y
        surf.blit(diver, (pos_x, pos_y))
        # flashlight cone (diver swims leftwards). Scale alpha with density
        head_x = int(pos_x + 6)
        head_y = int(pos_y + 8)
        cone = pygame.Surface((80, 60), pygame.SRCALPHA)
        pygame.draw.polygon(cone, (255, 250, 210, int(60 * max(0.5, min(2.0, ambient_density)))) , [(70, 30), (0, 0), (0, 60)])
        surf.blit(cone, (head_x - 70, head_y - 30))
        # bubbles
        for i in range(3 + (1 if ambient_density > 1.2 else 0)):
            bx = int(pos_x - i*4)
            by = int(pos_y + 2 - i*6 - (time_val*0.02 % 6))
            pygame.draw.circle(surf, (220, 240, 255), (bx, by), 2)
        # Distant submarine silhouette near seafloor
        sub_x = (w + 500) - ((offset // 3) % (w + 1000))
        sub_y = h - 80
        pygame.draw.rect(background, (20, 30, 40), (sub_x - 60, sub_y - 14, 120, 28))
        pygame.draw.circle(background, (20, 30, 40), (sub_x + 60, sub_y), 14)
        pygame.draw.rect(background, (20, 30, 40), (sub_x - 20, sub_y - 26, 40, 12))
        # small prop bubbles
        if int(time_val*0.01) % 2 == 0:
            for i in range(2):
                pygame.draw.circle(background, (35, 45, 60), (sub_x - 66 - i*6, sub_y - 4 + i*3), 2)

    # Composite layers onto the base surface
    surf.blit(background, (0, 0))
    surf.blit(midground, (0, 0))
    surf.blit(foreground, (0, 0))

    # --- Night overlay and moon ---
    if overlay_alpha > 0:
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 40, overlay_alpha))
        surf.blit(overlay, (0, 0))

    if moon_alpha > 0:
        moon = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(moon, (240, 240, 255), (15, 15), 12)
        moon.set_alpha(moon_alpha)
        surf.blit(moon, (w - 50, 20))
