import math
import pygame

class Environment:
    OCEAN_FLOOR = "Ocean Floor"
    ROCKY_REEF = "Rocky Reef"
    CORAL_COVE = "Coral Cove"
    BEACH = "Beach Shallows"
    OIL_RIG = "Oil Rig"


def draw_environment(surf, env_type, bg_offset, mid_offset, fg_offset, time_val):
    w, h = surf.get_width(), surf.get_height()
    # clear previous frame to avoid artifacts
    surf.fill((0, 0, 0))

    # Create separate layers for parallax scrolling
    background = pygame.Surface((w, h), pygame.SRCALPHA)
    midground = pygame.Surface((w, h), pygame.SRCALPHA)
    foreground = pygame.Surface((w, h), pygame.SRCALPHA)

    if env_type == Environment.OCEAN_FLOOR:
        for y in range(h):
            depth = y / h
            c = int(20 - depth * 15)
            b = int(60 - depth * 30)
            pygame.draw.line(background, (5, c, b), (0, y), (w, y))
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
        background.fill((20, 50, 80))
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
            r = int(30 + depth * 20)
            g = int(140 - depth * 40)
            b = int(180 - depth * 30)
            pygame.draw.line(background, (r, g, b), (0, y), (w, y))
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
        background.fill((100, 180, 220))
        for x in range(0, w, 30):
            sx = x + int(math.sin(time_val * 0.001 + x) * 10)
            pygame.draw.line(background, (150, 210, 240), (sx, 0), (sx - 20, h), 2)
        pygame.draw.circle(background, (255, 255, 200), (w-40, 40), 20)
        for cx in range(0, w, 100):

            pygame.draw.ellipse(background, (250, 250, 255), (cx-20, 10, 60, 20))
        pygame.draw.rect(midground, (230, 210, 170), (0, h - 30, w, 30))

        def _details():
            for x in range(0, w + 40, 40):
                dx = x - (fg_offset % 40)

    elif env_type == Environment.OIL_RIG:
        background.fill((30, 40, 45))
        for x in range(0, w + 120, 120):
            dx = x - (mid_offset % 120)
            pygame.draw.rect(midground, (80, 80, 80), (dx - 5, 0, 10, h))
            for y in range(40, h, 40):
                pygame.draw.line(midground, (70, 70, 70), (dx - 20, y), (dx + 20, y - 20), 3)
        for x in range(0, w + 80, 80):

            dx = x - (mid_offset % 80) + int(math.sin(time_val * 0.0005 + x) * 20)
            pygame.draw.ellipse(midground, (20, 10, 30), (dx - 30, h - 60, 60, 20))

        def _details():
            for x in range(0, w, 100):
                dx = x - (fg_offset % 100)
                pygame.draw.line(surf, (90, 90, 90), (dx, 0), (dx+20, h//2), 2)
            if int(time_val*0.002) % 2 == 0:
                drop_x = (time_val//20 % w)
                pygame.draw.circle(surf, (10, 10, 20), (int(drop_x), h-40), 3)

    # Default no-op for environments without details
    if "_details" not in locals():
        def _details():
            pass

    # Blit layers to the main surface then draw details
    surf.blit(background, (0, 0))
    surf.blit(midground, (0, 0))
    surf.blit(foreground, (0, 0))
    _details()

