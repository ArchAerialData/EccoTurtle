import math
import pygame

class Environment:
    OCEAN_FLOOR = "Ocean Floor"
    ROCKY_REEF = "Rocky Reef"
    CORAL_COVE = "Coral Cove"
    BEACH = "Beach Shallows"
    OIL_RIG = "Oil Rig"


def draw_environment(surf, env_type, offset, time_val):
    w, h = surf.get_width(), surf.get_height()
    # clear previous frame to avoid artifacts
    surf.fill((0, 0, 0))

    if env_type == Environment.OCEAN_FLOOR:
        for y in range(h):
            depth = y / h
            c = int(20 - depth * 15)
            b = int(60 - depth * 30)
            pygame.draw.line(surf, (5, c, b), (0, y), (w, y))
        for x in range(0, w + 40, 40):
            dx = x - (offset % 40)
            height = 10 + int(math.sin((x + offset) * 0.02) * 5)
            pygame.draw.ellipse(surf, (100, 90, 60),
                                (dx - 20, h - height, 40, height * 2))

    elif env_type == Environment.ROCKY_REEF:
        surf.fill((20, 50, 80))
        for x in range(0, w + 60, 60):
            dx = x - (offset % 60)
            pygame.draw.rect(surf, (60, 65, 70),
                             (dx - 15, h - 80, 30, 80))
            pygame.draw.polygon(surf, (50, 55, 60),
                                [(dx - 20, h), (dx + 20, h),
                                 (dx + 10, h - 90), (dx - 10, h - 90)])

    elif env_type == Environment.CORAL_COVE:
        for y in range(h):
            depth = y / h
            r = int(30 + depth * 20)
            g = int(140 - depth * 40)
            b = int(180 - depth * 30)
            pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
        for x in range(0, w + 50, 50):
            dx = x - (offset % 50)
            pygame.draw.circle(surf, (255, 120, 150), (dx, h - 20), 15)
            pygame.draw.circle(surf, (255, 140, 170), (dx, h - 20), 12)
            for branch in range(-2, 3):
                by = h - 40 - abs(branch) * 10
                bx = dx + branch * 8
                pygame.draw.line(surf, (255, 100, 50),
                                 (dx, h - 10), (bx, by), 3)

    elif env_type == Environment.BEACH:
        surf.fill((100, 180, 220))
        for x in range(0, w, 30):
            sx = x + int(math.sin(time_val * 0.001 + x) * 10)
            pygame.draw.line(surf, (150, 210, 240), (sx, 0), (sx - 20, h), 2)
        pygame.draw.rect(surf, (230, 210, 170), (0, h - 30, w, 30))
        for x in range(0, w + 40, 40):
            dx = x - (offset % 40)
            pygame.draw.circle(surf, (255, 230, 200), (dx, h - 15), 3)

    elif env_type == Environment.OIL_RIG:
        surf.fill((30, 40, 45))
        for x in range(0, w + 120, 120):
            dx = x - (offset % 120)
            pygame.draw.rect(surf, (80, 80, 80), (dx - 5, 0, 10, h))
            for y in range(40, h, 40):
                pygame.draw.line(surf, (70, 70, 70), (dx - 20, y), (dx + 20, y - 20), 3)
        for x in range(0, w + 80, 80):
            dx = x - (offset % 80) + int(math.sin(time_val * 0.0005 + x) * 20)
            pygame.draw.ellipse(surf, (20, 10, 30), (dx - 30, h - 60, 60, 20))
