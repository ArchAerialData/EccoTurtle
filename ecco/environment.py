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


def draw_environment(surf, env_type, offset, time_val, time_of_day):

    w, h = surf.get_width(), surf.get_height()

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

        for x in range(0, w + 40, 40):
            dx = x - (mid_offset % 40)
            height = 10 + int(math.sin((x + mid_offset) * 0.02) * 5)
            pygame.draw.ellipse(midground, (100, 90, 60),
                                (dx - 20, h - height, 40, height * 2))
        for x in range(0, w, 80):
            dx = x - (fg_offset % 80)
            pygame.draw.polygon(foreground, (180, 120, 50),
                                [(dx, h-25), (dx+5, h-15), (dx+15, h-12),
                                 (dx+7, h-5), (dx+10, h+5), (dx, h),
                                 (dx-10, h+5), (dx-7, h-5), (dx-15, h-12),
                                 (dx-5, h-15)])


        def _details():
            for x in range(0, w, 50):
                dx = x - (fg_offset % 50)
                pygame.draw.line(surf, (20, 80, 40), (dx, h-30), (dx, h-10), 2)

    elif env_type == Environment.ROCKY_REEF:
        for x in range(0, w + 60, 60):
            dx = x - (mid_offset % 60)
            pygame.draw.rect(midground, (60, 65, 70),
                             (dx - 15, h - 80, 30, 80))
            pygame.draw.polygon(midground, (50, 55, 60),
                                [(dx - 20, h), (dx + 20, h),
                                 (dx + 10, h - 90), (dx - 10, h - 90)])


        def _details():
            for x in range(0, w, 45):
                dx = x - (fg_offset % 45)
                sway = int(math.sin(time_val*0.002 + x) * 5)
                pygame.draw.line(surf, (30, 100, 60), (dx, h-60), (dx+sway, h-20), 3)

    elif env_type == Environment.CORAL_COVE:
        for y in range(h):
            depth = y / h

            line_col = _lerp_color(water_color,
                                   (water_color[0] + 30,
                                    max(0, water_color[1] - 40),
                                    max(0, water_color[2] - 30)), depth)
            pygame.draw.line(surf, line_col, (0, y), (w, y))
    
        for x in range(0, w + 50, 50):
            dx = x - (mid_offset % 50)
            pygame.draw.circle(midground, (255, 120, 150), (dx, h - 20), 15)
            pygame.draw.circle(midground, (255, 140, 170), (dx, h - 20), 12)
            for branch in range(-2, 3):
                by = h - 40 - abs(branch) * 10
                bx = dx + branch * 8
                pygame.draw.line(midground, (255, 100, 50),
                                 (dx, h - 10), (bx, by), 3)


        def _details():
            for x in range(0, w, 90):
                dx = x - (fg_offset % 90)
                fy = h//2 + int(math.sin(time_val*0.003 + x) * 20)
                pygame.draw.ellipse(surf, (200, 80, 80), (dx, fy, 12, 6))
                pygame.draw.polygon(surf, (220, 100, 100),
                                    [(dx+12, fy+3), (dx+16, fy), (dx+16, fy+6)])


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
