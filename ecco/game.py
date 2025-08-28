# Sea Turtle Echo – Side Scroller Edition with Environments & Creatures
# Save this file as: SeaTurtle_SideScroller.pyw
# Double-click to run (Python + Pygame required). First run generates music/SFX.
# ------------------------------------------------------------

import os, sys, math, random, time
import pygame
from pygame.locals import *

from .config import (TITLE, DEFAULT_W, DEFAULT_H, SCALE, FPS,
                     POWERUP_THRESHOLD, POWERUP_DURATION, SAVE_FILE)
from .environment import Environment, draw_environment
from .sound import load_or_generate_audio, play_sfx, _sfx


# Graceful message if pygame isn't installed
def _msgbox(title, text):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, title, 0x40)
    except Exception:
        print(f"{title}: {text}")

# ----------------------- Character Types ----------------------
class CharacterType:
    MALE_TURTLE = "Male Sea Turtle"
    FEMALE_TURTLE = "Female Sea Turtle"
    BISEXUAL_TURTLE = "Bi Sea Turtle"
    TORTOISE = "Land Tortoise"

# ----------------------- Game Objects ----------------------
class Turtle:
    def __init__(self, x, y, character_type=CharacterType.MALE_TURTLE):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.angle = 0.0
        self.base_speed = 3.0
        self.speed = self.base_speed
        self.drag = 0.92
        self.radius = 10
        self.cooldown = 0.0
        self.character_type = character_type
        
        # Tortoise special handling - spawns healthy
        self.health = 3
        self.max_health = 3
        self.is_tortoise = (character_type == CharacterType.TORTOISE)
        self.has_moved = False
        self.death_timer = 0.0
            
        self.iframes = 0.0
        self.mouth_timer = 0.0
        self.swim_animation = 0.0
        
        # Power-up state
        self.jellyfish_eaten = 0
        self.powered_up = False
        self.powerup_timer = 0.0
        
        # Character-specific colors
        if character_type == CharacterType.MALE_TURTLE:
            self.shell_color = (18, 102, 85)
            self.body_color = (32, 140, 110)
            self.accent_color = (190, 235, 210)
        elif character_type == CharacterType.FEMALE_TURTLE:
            self.shell_color = (102, 18, 85)
            self.body_color = (140, 32, 110)
            self.accent_color = (235, 190, 220)
        elif character_type == CharacterType.BISEXUAL_TURTLE:
            self.shell_color = (255, 255, 255)
            self.body_color = (255, 255, 255)
            self.accent_color = (255, 255, 255)
        else:  # Tortoise
            self.shell_color = (92, 64, 35)
            self.body_color = (115, 80, 44)
            self.accent_color = (140, 120, 80)

        self.rainbow = (character_type == CharacterType.BISEXUAL_TURTLE)
        self.rainbow_phase = 0.0

    def update(self, dt, keys, scroll_speed):
        dt_sec = dt / 1000.0
        
        # Check for tortoise death on movement
        if self.is_tortoise and not self.has_moved:
            if any(keys[k] for k in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
                                     pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_SPACE, pygame.K_LSHIFT]):
                self.has_moved = True
                self.death_timer = 0.5  # Brief delay before death
        
        # Handle tortoise drowning
        if self.is_tortoise and self.has_moved:
            self.death_timer -= dt_sec
            if self.death_timer <= 0 and self.health > 0:
                self.health = 0
                return
        
        if self.health <= 0:
            return
            
        # Movement input
        ax, ay = 0.0, 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: ax -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: ax += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: ay -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: ay += 1
        
        # Normalize diagonal movement
        mag = math.hypot(ax, ay)
        if mag > 0:
            ax /= mag
            ay /= mag
            self.swim_animation += dt_sec * 10
        
        # Apply speed boost when powered up
        current_speed = self.speed * (1.5 if self.powered_up else 1.0)
        
        # Dash mechanic
        if (keys[pygame.K_SPACE] or keys[pygame.K_LSHIFT]) and self.cooldown <= 0:
            self.vx += ax * 300
            self.vy += ay * 300
            self.cooldown = 1.0
            play_sfx("dash")
        else:
            # Normal movement with side-scrolling bias
            self.vx += ax * current_speed * dt_sec * 60
            self.vy += ay * current_speed * dt_sec * 60
        
        # Apply drag
        self.vx *= (1.0 - (1.0 - self.drag) * dt_sec * 60)
        self.vy *= (1.0 - (1.0 - self.drag) * dt_sec * 60)
        
        # Auto-scroll with the level but reduce current pushing right
        self.x += (self.vx + scroll_speed * 0.2) * dt_sec
        self.y += self.vy * dt_sec
        
        # Get current screen dimensions
        base_w = pygame.display.get_surface().get_width() // SCALE
        base_h = pygame.display.get_surface().get_height() // SCALE
        
        # Constrain to screen (no wrap in side-scroller)
        self.x = max(self.radius, min(base_w - self.radius, self.x))
        self.y = max(self.radius, min(base_h - self.radius, self.y))
        
        # Update angle based on movement
        if mag > 0:
            self.angle = math.degrees(math.atan2(ay, ax))
        
        # Update timers
        self.cooldown = max(0.0, self.cooldown - dt_sec)
        self.iframes = max(0.0, self.iframes - dt_sec)
        self.mouth_timer = max(0.0, self.mouth_timer - dt_sec)
        
        # Update powerup timer
        if self.powered_up:
            self.powerup_timer -= dt_sec
            if self.powerup_timer <= 0:
                self.powered_up = False

        if self.rainbow:
            self.rainbow_phase = (self.rainbow_phase + dt_sec * 60) % 360

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        
        # Power-up glow effect
        if self.powered_up:
            glow_r = r + 5 + int(math.sin(pygame.time.get_ticks() * 0.01) * 2)
            pygame.draw.circle(surf, (255, 200, 100), (cx, cy), glow_r, 2)

        flipper_color = self.shell_color
        head_color = self.accent_color

        if self.rainbow:
            for i in range(7):
                color = pygame.Color(0)
                hue = (self.rainbow_phase + i * (360 / 7)) % 360
                color.hsva = (hue, 80, 100, 100)
                radius = max(1, int(r - i * r / 7))
                pygame.draw.circle(surf, color, (cx, cy), radius)
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy), r, 2)
            flipper_color = pygame.Color(0)
            flipper_color.hsva = (self.rainbow_phase % 360, 80, 100, 100)
            head_color = pygame.Color(0)
            head_color.hsva = ((self.rainbow_phase + 180) % 360, 80, 100, 100)
        else:
            # Shell base
            pygame.draw.ellipse(surf, self.shell_color, (cx-r, cy-r, r*2, r*2))

            # Shell pattern (hexagonal segments)
            for angle in range(0, 360, 60):
                px = cx + int(math.cos(math.radians(angle)) * r * 0.6)
                py = cy + int(math.sin(math.radians(angle)) * r * 0.6)
                pygame.draw.circle(surf, self.body_color, (px, py), 3)

            # Shell highlight
            pygame.draw.ellipse(surf, self.body_color, (cx-r+2, cy-r+2, (r*2)-4, (r*2)-4), 2)
        
        # Head (bigger and more detailed)
        hx = cx + int(math.cos(math.radians(self.angle)) * r * 1.2)
        hy = cy + int(math.sin(math.radians(self.angle)) * r * 1.2)
        pygame.draw.circle(surf, head_color, (hx, hy), 4)
        
        # Eyes (two eyes for more detail)
        eye1x = hx + int(math.cos(math.radians(self.angle + 20)) * 3)
        eye1y = hy + int(math.sin(math.radians(self.angle + 20)) * 3)
        eye2x = hx + int(math.cos(math.radians(self.angle - 20)) * 3)
        eye2y = hy + int(math.sin(math.radians(self.angle - 20)) * 3)
        pygame.draw.circle(surf, (20, 40, 30), (eye1x, eye1y), 1)
        pygame.draw.circle(surf, (20, 40, 30), (eye2x, eye2y), 1)
        
        # Animated flippers
        swim_offset = math.sin(self.swim_animation) * 20
        
        # Front flippers
        f1x = int(math.cos(math.radians(self.angle + 60 + swim_offset)) * r * 1.0)
        f1y = int(math.sin(math.radians(self.angle + 60 + swim_offset)) * r * 1.0)
        f2x = int(math.cos(math.radians(self.angle - 60 - swim_offset)) * r * 1.0)
        f2y = int(math.sin(math.radians(self.angle - 60 - swim_offset)) * r * 1.0)
        pygame.draw.ellipse(surf, flipper_color, (cx+f1x-3, cy+f1y-2, 6, 4))
        pygame.draw.ellipse(surf, flipper_color, (cx+f2x-3, cy+f2y-2, 6, 4))
        
        # Back flippers
        b1x = int(math.cos(math.radians(self.angle + 150 - swim_offset)) * r * 0.8)
        b1y = int(math.sin(math.radians(self.angle + 150 - swim_offset)) * r * 0.8)
        b2x = int(math.cos(math.radians(self.angle - 150 + swim_offset)) * r * 0.8)
        b2y = int(math.sin(math.radians(self.angle - 150 + swim_offset)) * r * 0.8)
        pygame.draw.ellipse(surf, flipper_color, (cx+b1x-2, cy+b1y-2, 4, 3))
        pygame.draw.ellipse(surf, flipper_color, (cx+b2x-2, cy+b2y-2, 4, 3))
        
        # Tail
        tx = cx - int(math.cos(math.radians(self.angle)) * r * 1.0)
        ty = cy - int(math.sin(math.radians(self.angle)) * r * 1.0)
        pygame.draw.circle(surf, flipper_color, (tx, ty), 2)
        
        # Mouth animation when eating
        if self.mouth_timer > 0:
            mx = cx + int(math.cos(math.radians(self.angle)) * r * 1.5)
            my = cy + int(math.sin(math.radians(self.angle)) * r * 1.5)
            pygame.draw.circle(surf, (255, 255, 255), (mx, my), 2)

class Jelly:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r = 6 + random.randint(0, 2)
        self.phase = random.random() * math.tau
        self.speed = 0.5 + random.random() * 0.5
        self.value = 1  # Score value

    def update(self, dt, scroll_speed):
        dt_sec = dt / 1000.0
        self.y += math.sin(self.phase) * 30 * dt_sec
        # Drift left with the current so new jellies spawn on the right and
        # gently float across the screen
        self.x -= scroll_speed * dt_sec * 0.5
        self.phase += self.speed * dt_sec * 2
        
        base_h = pygame.display.get_surface().get_height() // SCALE
        
        # Wrap vertically
        if self.y < 0: self.y = base_h
        if self.y > base_h: self.y = 0

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        # Enhanced jellyfish with translucent dome and inner glow
        pygame.draw.circle(surf, (231, 192, 255), (cx, cy), self.r)
        pygame.draw.circle(surf, (250, 240, 255), (cx, cy-2), self.r-3)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy-4), 1)
        
        # Animated tentacles
        tentacle_wave = math.sin(self.phase * 2) * 2
        for i in range(-3, 4):
            tx = cx + i * 2
            ty_start = cy + self.r - 1
            ty_end = cy + self.r + 6 + abs(tentacle_wave)
            tx_end = tx + int(tentacle_wave * 0.5)
            pygame.draw.line(surf, (216, 172, 240), (tx, ty_start), (tx_end, ty_end), 1)

class PlasticBag:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r = 7
        self.swing = random.random() * math.tau
        self.speed = 0.3 + random.random() * 0.3

    def update(self, dt, scroll_speed):
        dt_sec = dt / 1000.0
        # Sway with currents while drifting left with the level
        self.x += math.cos(self.swing) * 20 * dt_sec
        self.x -= scroll_speed * dt_sec * 0.7
        self.y += math.sin(self.swing) * 10 * dt_sec
        self.swing += self.speed * dt_sec * 2
        
        base_h = pygame.display.get_surface().get_height() // SCALE
        
        if self.y < 0: self.y = base_h
        if self.y > base_h: self.y = 0

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        # More detailed plastic bag
        bag_color = (235, 245, 255)
        # Main body
        pygame.draw.rect(surf, bag_color, (cx-5, cy-7, 10, 12), 1)
        # Slight shading
        pygame.draw.line(surf, (215, 225, 235), (cx-5, cy-1), (cx+5, cy-1))
        # Handles
        pygame.draw.line(surf, bag_color, (cx-5, cy-7), (cx-7, cy-11), 1)
        pygame.draw.line(surf, bag_color, (cx+5, cy-7), (cx+7, cy-11), 1)
        # Crinkle lines for texture
        pygame.draw.line(surf, bag_color, (cx-3, cy-4), (cx-1, cy+2), 1)
        pygame.draw.line(surf, bag_color, (cx+1, cy-3), (cx+3, cy+3), 1)

# New creature classes
class MantisShrimp:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r = 8
        self.direction = 1 if random.random() > 0.5 else -1
        self.speed = 1.5
        self.punch_timer = 0.0
        self.edible = True
        self.value = 5  # Worth more points when eaten

    def update(self, dt, scroll_speed):
        dt_sec = dt / 1000.0
        self.x += self.direction * self.speed * 30 * dt_sec
        self.x -= scroll_speed * dt_sec * 0.8
        
        # Random punching animation
        if random.random() < 0.005:
            self.punch_timer = 0.3
        self.punch_timer = max(0.0, self.punch_timer - dt_sec)
        
        base_h = pygame.display.get_surface().get_height() // SCALE
        # Bounce off top and bottom
        if self.y < 20 or self.y > base_h - 20:
            self.direction *= -1

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        
        # Body segments
        body_colors = [(255, 100, 50), (255, 130, 70), (255, 150, 90)]
        for i, color in enumerate(body_colors):
            segment_x = cx - i * 3 * self.direction
            pygame.draw.ellipse(surf, color, (segment_x - 4, cy - 3, 8, 6))
        # Tail fan
        pygame.draw.polygon(surf, (255, 80, 40),
                            [(cx - 12*self.direction, cy - 2),
                             (cx - 16*self.direction, cy),
                             (cx - 12*self.direction, cy + 2)])
        
        # Raptorial claws
        if self.punch_timer > 0:
            # Extended punch
            pygame.draw.circle(surf, (255, 255, 100), 
                             (cx + self.direction * 12, cy), 3)
        else:
            # Normal position
            pygame.draw.circle(surf, (255, 80, 40), 
                             (cx + self.direction * 6, cy - 2), 2)
            pygame.draw.circle(surf, (255, 80, 40), 
                             (cx + self.direction * 6, cy + 2), 2)
        
        # Eyes on stalks
        pygame.draw.circle(surf, (0, 200, 100), (cx + 2, cy - 4), 2)
        pygame.draw.circle(surf, (0, 200, 100), (cx - 2, cy - 4), 2)

class SeaHorse:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r = 6
        self.bob = random.random() * math.tau
        self.edible = True
        self.value = 3

    def update(self, dt, scroll_speed):
        dt_sec = dt / 1000.0
        self.x -= scroll_speed * dt_sec * 0.6
        self.y += math.sin(self.bob) * 20 * dt_sec
        self.bob += dt_sec * 3

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        
        # Curled body
        pygame.draw.arc(surf, (255, 200, 100), 
                       (cx - 6, cy - 8, 12, 16), 
                       math.pi * 0.5, math.pi * 1.5, 2)
        
        # Head
        pygame.draw.circle(surf, (255, 210, 120), (cx, cy - 6), 3)
        
        # Snout
        pygame.draw.line(surf, (255, 200, 100), (cx + 3, cy - 6), (cx + 6, cy - 5), 2)
        
        # Eye
        pygame.draw.circle(surf, (0, 0, 0), (cx + 1, cy - 7), 1)
        
        # Fin
        fin_wave = int(math.sin(self.bob * 2) * 2)
        pygame.draw.ellipse(surf, (255, 220, 140),
                            (cx - 8 + fin_wave, cy - 3, 4, 6))

class Clownfish:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r = 5
        self.swim_cycle = random.random() * math.tau
        self.edible = True
        self.value = 2

    def update(self, dt, scroll_speed):
        dt_sec = dt / 1000.0
        self.x += math.cos(self.swim_cycle) * 40 * dt_sec
        self.x -= scroll_speed * dt_sec * 0.9
        self.y += math.sin(self.swim_cycle * 2) * 20 * dt_sec
        self.swim_cycle += dt_sec * 4

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        
        # Body
        pygame.draw.ellipse(surf, (255, 140, 0), (cx - 5, cy - 3, 10, 6))
        
        # White stripes
        pygame.draw.line(surf, (255, 255, 255), (cx - 2, cy - 3), (cx - 2, cy + 3), 2)
        pygame.draw.line(surf, (255, 255, 255), (cx + 2, cy - 3), (cx + 2, cy + 3), 2)
        
        # Eye
        pygame.draw.circle(surf, (0, 0, 0), (cx + 3, cy - 1), 1)
        
        # Fins
        pygame.draw.circle(surf, (255, 160, 20), (cx - 5, cy), 2)
        pygame.draw.circle(surf, (255, 160, 20), (cx + 5, cy), 2)

class Pufferfish:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r = 7
        self.puffed = False
        self.puff_timer = 0.0
        self.edible = True
        self.value = 4

    def update(self, dt, scroll_speed):
        dt_sec = dt / 1000.0
        self.x -= scroll_speed * dt_sec * 0.5
        
        # Random puffing
        if not self.puffed and random.random() < 0.003:
            self.puffed = True
            self.puff_timer = 2.0
        
        if self.puffed:
            self.puff_timer -= dt_sec
            if self.puff_timer <= 0:
                self.puffed = False

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        
        if self.puffed:
            # Puffed state
            r = self.r + 3
            pygame.draw.circle(surf, (200, 200, 100), (cx, cy), r)
            # Spikes
            for angle in range(0, 360, 30):
                sx = cx + int(math.cos(math.radians(angle)) * r)
                sy = cy + int(math.sin(math.radians(angle)) * r)
                ex = cx + int(math.cos(math.radians(angle)) * (r + 3))
                ey = cy + int(math.sin(math.radians(angle)) * (r + 3))
                pygame.draw.line(surf, (150, 150, 50), (sx, sy), (ex, ey), 1)
        else:
            # Normal state
            pygame.draw.ellipse(surf, (180, 180, 80),
                                (cx - self.r, cy - self.r + 2,
                                 self.r * 2, self.r * 2 - 4))
            # Subtle spots for texture
            pygame.draw.circle(surf, (170, 170, 70), (cx - 2, cy - 2), 1)
            pygame.draw.circle(surf, (170, 170, 70), (cx + 2, cy + 1), 1)
        
        # Eye
        pygame.draw.circle(surf, (0, 0, 0), (cx + 3, cy - 2), 1)

class Bubble:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = (random.random() * 2 - 1) * 10
        self.vy = -10 - random.random() * 10
        self.life = 1.0
        self.r = 1 + random.randint(0, 2)

    def update(self, dt):
        dt_sec = dt / 1000.0
        self.x += self.vx * dt_sec
        self.y += self.vy * dt_sec
        self.life -= dt_sec * 0.8

    def draw(self, surf):
        if self.life > 0:
            alpha = int(self.life * 255)
            color = (200 + int(55 * self.life), 230 + int(25 * self.life), 255)
            pygame.draw.circle(surf, color, (int(self.x), int(self.y)), self.r, 1)
            # Highlight for 3D effect
            if self.r > 1:
                pygame.draw.circle(surf, (255, 255, 255), 
                                 (int(self.x - self.r//2), int(self.y - self.r//2)), 1)

# --------------------- Helper Functions --------------------
def dist2(a, b, x, y):
    return (a - x) * (a - x) + (b - y) * (b - y)

def circle_collide(ax, ay, ar, bx, by, br):
    return dist2(ax, ay, bx, by) <= (ar + br) * (ar + br)

def load_highscore(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return max(0, int(f.read().strip()))
    except Exception:
        return 0

def save_highscore(path, score):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(str(int(score)))
    except Exception:
        pass

# ----------------------- Character Selection -----------------------
def character_selection_screen(screen, clock, base_font, title_font):
    """Character selection menu"""
    characters = [
        (CharacterType.MALE_TURTLE, "Classic hero of the seas", (18, 102, 85)),
        (CharacterType.FEMALE_TURTLE, "Swift and graceful", (102, 18, 85)),
        (CharacterType.BISEXUAL_TURTLE, "Loves all ocean creatures", (85, 18, 102)),
        (CharacterType.TORTOISE, "Adventurous land dweller", (92, 64, 35))  # No death hint
    ]
    
    selected = 0
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return None
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return None
                elif event.key == K_UP or event.key == K_w:
                    selected = (selected - 1) % len(characters)
                elif event.key == K_DOWN or event.key == K_s:
                    selected = (selected + 1) % len(characters)
                elif event.key == K_RETURN or event.key == K_SPACE:
                    return characters[selected][0]
        
        # Draw selection screen
        screen.fill((8, 22, 44))
        
        # Title
        title = title_font.render("SELECT YOUR CHARACTER", True, (220, 255, 255))
        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 50))
        
        # Character options
        y_start = 150
        for i, (char_type, desc, color) in enumerate(characters):
            y = y_start + i * 100
            
            # Highlight selected
            if i == selected:
                pygame.draw.rect(screen, (50, 100, 150), 
                               (screen.get_width()//2 - 300, y - 10, 600, 80), 3)
            
            # Character preview (turtle icon)
            cx, cy = screen.get_width()//2 - 200, y + 30
            pygame.draw.ellipse(screen, color, (cx-20, cy-20, 40, 40))
            pygame.draw.ellipse(screen, tuple(c+30 if c+30<255 else 255 for c in color), 
                              (cx-15, cy-15, 30, 30), 3)
            
            # Character name
            name_text = base_font.render(char_type, True, (220, 255, 255))
            screen.blit(name_text, (screen.get_width()//2 - 100, y))
            
            # Description
            desc_text = base_font.render(desc, True, (180, 220, 240))
            screen.blit(desc_text, (screen.get_width()//2 - 100, y + 30))
        
        # Instructions
        inst = base_font.render("↑↓ or W/S to select, ENTER to confirm, ESC to quit", 
                              True, (150, 200, 220))
        screen.blit(inst, (screen.get_width()//2 - inst.get_width()//2, 
                         screen.get_height() - 50))
        
        pygame.display.flip()
        clock.tick(FPS)

# ----------------------- Main Menu with Volume Control -----------------------
def main_menu_screen(screen, clock, base_font, title_font, volume):
    """Main menu with volume control"""
    selected = 0
    menu_items = ["Start Game", f"Music Volume: {int(volume * 100)}%", "Quit"]
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return None, volume
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return None, volume
                elif event.key == K_UP or event.key == K_w:
                    selected = (selected - 1) % len(menu_items)
                elif event.key == K_DOWN or event.key == K_s:
                    selected = (selected + 1) % len(menu_items)
                elif event.key == K_LEFT or event.key == K_a:
                    if selected == 1:  # Volume control
                        volume = max(0.0, volume - 0.1)
                        pygame.mixer.music.set_volume(volume)
                        menu_items[1] = f"Music Volume: {int(volume * 100)}%"
                elif event.key == K_RIGHT or event.key == K_d:
                    if selected == 1:  # Volume control
                        volume = min(1.0, volume + 0.1)
                        pygame.mixer.music.set_volume(volume)
                        menu_items[1] = f"Music Volume: {int(volume * 100)}%"
                elif event.key == K_RETURN or event.key == K_SPACE:
                    if selected == 0:  # Start
                        return "start", volume
                    elif selected == 2:  # Quit
                        return None, volume
        
        # Draw menu
        screen.fill((8, 22, 44))
        
        # Title with wave effect
        wave_offset = int(math.sin(pygame.time.get_ticks() * 0.001) * 10)
        title = title_font.render("SEA TURTLE ECHO", True, (220, 255, 255))
        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 
                           100 + wave_offset))
        
        subtitle = base_font.render("~ Deep Dive Edition ~", True, (180, 220, 240))
        screen.blit(subtitle, (screen.get_width()//2 - subtitle.get_width()//2, 
                              140 + wave_offset))
        
        # Menu items
        y_start = 250
        for i, item in enumerate(menu_items):
            y = y_start + i * 60
            
            # Highlight selected
            if i == selected:
                pygame.draw.rect(screen, (50, 100, 150), 
                               (screen.get_width()//2 - 200, y - 10, 400, 40), 3)
            
            color = (255, 255, 255) if i == selected else (180, 220, 240)
            item_text = base_font.render(item, True, color)
            screen.blit(item_text, (screen.get_width()//2 - item_text.get_width()//2, y))
            
            # Volume bar
            if i == 1:
                bar_x = screen.get_width()//2 - 100
                bar_y = y + 25
                pygame.draw.rect(screen, (100, 100, 100), 
                               (bar_x, bar_y, 200, 10), 1)
                pygame.draw.rect(screen, (100, 200, 255), 
                               (bar_x, bar_y, int(200 * volume), 10))
        
        # Instructions
        inst = base_font.render("↑↓ to navigate, ←→ to adjust volume, ENTER to select", 
                              True, (150, 200, 220))
        screen.blit(inst, (screen.get_width()//2 - inst.get_width()//2, 
                         screen.get_height() - 50))
        
        pygame.display.flip()
        clock.tick(FPS)

# ------------------------- Main Game -----------------------
def run():
    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    
    # Start with default size but allow resizing
    screen = pygame.display.set_mode((DEFAULT_W, DEFAULT_H), RESIZABLE)
    pygame.display.set_caption(TITLE)
    
    # Icon
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(icon, (32, 140, 110), (16, 16), 14)
    pygame.draw.circle(icon, (18, 102, 85), (16, 16), 14, 2)
    pygame.display.set_icon(icon)
    
    clock = pygame.time.Clock()
    
    # Fonts
    pygame.font.init()
    base_font = pygame.font.SysFont("consolas", 14)
    title_font = pygame.font.SysFont("consolas", 22, bold=True)
    
    # Audio
    music_map, eat, hurt, dash, powerup = load_or_generate_audio()
    pygame.mixer.music.load(music_map[Environment.BEACH])
    
    _sfx["eat"] = pygame.mixer.Sound(eat)
    _sfx["hurt"] = pygame.mixer.Sound(hurt)
    _sfx["dash"] = pygame.mixer.Sound(dash)
    _sfx["powerup"] = pygame.mixer.Sound(powerup)
    
    # Main menu
    volume = 0.35
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1)
    
    menu_result, volume = main_menu_screen(screen, clock, base_font, title_font, volume)
    if menu_result is None:
        pygame.quit()
        return
    
    # Character selection
    selected_character = character_selection_screen(screen, clock, base_font, title_font)
    if selected_character is None:
        pygame.quit()
        return
    
    # Create base surface for the game
    current_w, current_h = screen.get_size()
    base_w, base_h = current_w // SCALE, current_h // SCALE
    base = pygame.Surface((base_w, base_h))
    
    # Game state
    rng = random.Random()
    turtle = Turtle(50, base_h//2, selected_character)
    
    # Check if tortoise (but don't kill immediately)
    game_over = False
    death_message = ""
    
    # Initialize creatures
    jellies = []
    bags = []
    creatures = []  # New interactive creatures
    bubbles = []
    
    # Environment management
    environments = [Environment.BEACH, Environment.CORAL_COVE, Environment.ROCKY_REEF, 
                   Environment.OCEAN_FLOOR, Environment.OIL_RIG]
    current_env_index = 0
    current_env = environments[current_env_index]
    env_transition = 0
    distance_traveled = 0
    
    # Side-scrolling variables
    scroll_speed = 30  # pixels per second
    world_offset = 0
    
    score = 0
    streak = 0
    paused = False
    start_menu = False  
    fullscreen = False
    
    highscore_path = SAVE_FILE
    highscore = load_highscore(highscore_path)
    
    t = 0.0
    
    # Spawn initial entities
    for _ in range(5):
        jellies.append(Jelly(rng.randrange(base_w//2, base_w), 
                           rng.randrange(20, base_h-20)))
    for _ in range(3):
        bags.append(PlasticBag(rng.randrange(base_w//2, base_w), 
                              rng.randrange(20, base_h-20)))
    
    # Add initial creatures
    creatures.append(MantisShrimp(base_w - 50, base_h//2))
    creatures.append(SeaHorse(base_w - 100, base_h//3))
    creatures.append(Clownfish(base_w - 150, base_h*2//3))
    
    while True:
        dt = clock.tick(FPS)
        t += dt
        
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit()
                return
            elif e.type == VIDEORESIZE:
                current_w, current_h = e.w, e.h
                screen = pygame.display.set_mode((current_w, current_h), RESIZABLE)
                base_w, base_h = current_w // SCALE, current_h // SCALE
                base = pygame.Surface((base_w, base_h))
            elif e.type == KEYDOWN:
                if e.key == K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), FULLSCREEN)
                        current_w, current_h = screen.get_size()
                    else:
                        screen = pygame.display.set_mode((DEFAULT_W, DEFAULT_H), RESIZABLE)
                        current_w, current_h = DEFAULT_W, DEFAULT_H
                    base_w, base_h = current_w // SCALE, current_h // SCALE
                    base = pygame.Surface((base_w, base_h))
                elif e.key == K_ESCAPE:
                    if start_menu or game_over:
                        pygame.quit()
                        return
                    paused = not paused
                elif e.key == K_RETURN and start_menu:
                    start_menu = False
                elif e.key == K_r and game_over:
                    # Restart
                    selected_character = character_selection_screen(screen, clock, base_font, title_font)
                    if selected_character is None:
                        pygame.quit()
                        return
                    turtle = Turtle(50, base_h//2, selected_character)
                    game_over = False
                    death_message = ""
                    jellies = []
                    bags = []
                    creatures = []
                    bubbles = []
                    score = 0
                    streak = 0
                    distance_traveled = 0
                    world_offset = 0
                    current_env_index = 0
                    current_env = environments[current_env_index]
                    pygame.mixer.music.load(music_map[current_env])
                    pygame.mixer.music.play(-1)
                    
                    # Respawn entities
                    for _ in range(5):
                        jellies.append(Jelly(rng.randrange(base_w//2, base_w), 
                                           rng.randrange(20, base_h-20)))
                    for _ in range(3):
                        bags.append(PlasticBag(rng.randrange(base_w//2, base_w), 
                                              rng.randrange(20, base_h-20)))
                    creatures.append(MantisShrimp(base_w - 50, base_h//2))
                    creatures.append(SeaHorse(base_w - 100, base_h//3))
                    creatures.append(Clownfish(base_w - 150, base_h*2//3))
                    start_menu = False
        
        keys = pygame.key.get_pressed()
        
        # Update game state
        if not (paused or game_over or start_menu):
            # Update scrolling
            world_offset += scroll_speed * (dt / 1000.0)
            distance_traveled += scroll_speed * (dt / 1000.0)
            
            # Environment transitions every 500 pixels
            if distance_traveled > 500:
                distance_traveled = 0
                current_env_index = (current_env_index + 1) % len(environments)
                current_env = environments[current_env_index]
                pygame.mixer.music.load(music_map[current_env])
                pygame.mixer.music.play(-1)
                # spawn fresh food in new environment
                for _ in range(3):
                    jellies.append(
                        Jelly(base_w + rng.randrange(20, 100),
                              rng.randrange(20, base_h - 20))
                    )
            
            # Update turtle
            turtle.update(dt, keys, scroll_speed)
            
            # Check for tortoise death
            if turtle.is_tortoise and turtle.has_moved and turtle.health <= 0:
                game_over = True
                death_message = "The tortoise immediately drowned! Wrong habitat!"
            elif turtle.health <= 0:
                game_over = True
            
            # Update entities
            for j in jellies[:]:
                j.update(dt, scroll_speed)
                if j.x < -20:  # Remove off-screen
                    jellies.remove(j)
            
            for b in bags[:]:
                b.update(dt, scroll_speed)
                if b.x < -20:
                    bags.remove(b)
            
            for c in creatures[:]:
                c.update(dt, scroll_speed)
                if c.x < -20:
                    creatures.remove(c)
            
            for bub in list(bubbles):
                bub.update(dt)
                if bub.life <= 0:
                    bubbles.remove(bub)
            
            # Spawn new entities
            if rng.random() < (0.003 + min(0.01, score * 0.00005)):
                jellies.append(Jelly(base_w + rng.randrange(20, 100), 
                                   rng.randrange(20, base_h-20)))
            if rng.random() < (0.002 + min(0.008, score * 0.00003)):
                bags.append(PlasticBag(base_w + rng.randrange(20, 100), 
                                      rng.randrange(20, base_h-20)))
            
            # Spawn creatures
            if rng.random() < 0.004:
                creature_types = [MantisShrimp, SeaHorse, Clownfish, Pufferfish]
                CreatureClass = rng.choice(creature_types)
                creatures.append(CreatureClass(base_w + rng.randrange(20, 100), 
                                              rng.randrange(40, base_h-40)))
            
            # Limit entities
            jellies = jellies[-30:]
            bags = bags[-20:]
            creatures = creatures[-15:]
            
            # Collisions with jellies
            for j in list(jellies):
                if circle_collide(turtle.x, turtle.y, turtle.radius, j.x, j.y, j.r):
                    jellies.remove(j)
                    score += j.value + min(9, streak // 5)
                    streak += 1
                    turtle.mouth_timer = 0.4
                    turtle.jellyfish_eaten += 1
                    play_sfx("eat")
                    
                    # Check for power-up
                    if not turtle.powered_up and turtle.jellyfish_eaten >= POWERUP_THRESHOLD:
                        turtle.powered_up = True
                        turtle.powerup_timer = POWERUP_DURATION
                        turtle.jellyfish_eaten = 0
                        play_sfx("powerup")
                        # Visual effect
                        for _ in range(8):
                            bubbles.append(Bubble(turtle.x, turtle.y))
                    else:
                        for _ in range(4):
                            bubbles.append(Bubble(turtle.x, turtle.y))
            
            # Collisions with plastic bags
            for pb in list(bags):
                if circle_collide(turtle.x, turtle.y, turtle.radius, pb.x, pb.y, pb.r):
                    if turtle.iframes <= 0.0:
                        turtle.health -= 1
                        turtle.iframes = 1.5
                        streak = 0
                        play_sfx("hurt")
                        dx = turtle.x - pb.x
                        dy = turtle.y - pb.y
                        d = math.hypot(dx, dy) or 1.0
                        turtle.vx += (dx / d) * 180
                        turtle.vy += (dy / d) * 180
                        bags.remove(pb)
                        for _ in range(8):
                            bubbles.append(Bubble(turtle.x, turtle.y))
            
            # Collisions with creatures (only if powered up)
            if turtle.powered_up:
                for creature in list(creatures):
                    if hasattr(creature, 'edible') and creature.edible:
                        if circle_collide(turtle.x, turtle.y, turtle.radius, 
                                        creature.x, creature.y, creature.r):
                            creatures.remove(creature)
                            score += creature.value * 2  # Double points when powered up
                            turtle.mouth_timer = 0.4
                            play_sfx("eat")
                            for _ in range(6):
                                bubbles.append(Bubble(turtle.x, turtle.y))
            
            if game_over and score > highscore:
                highscore = score
                save_highscore(highscore_path, highscore)
        
        # Draw everything
        draw_environment(base, current_env, int(world_offset), int(t))
        
        # Draw entities
        for j in jellies:
            j.draw(base)
        for b in bags:
            b.draw(base)
        for c in creatures:
            c.draw(base)
        for bub in bubbles:
            bub.draw(base)
        
        if turtle.health > 0:
            turtle.draw(base)
        
        # UI
        if paused:
            p = base_font.render("PAUSED - Press ESC to resume", True, (210, 240, 250))
            base.blit(p, (base_w//2 - p.get_width()//2, base_h//2))
            
        elif game_over:
            if death_message:
                msg = base_font.render(death_message, True, (255, 100, 100))
                base.blit(msg, (base_w//2 - msg.get_width()//2, base_h//2 - 20))
            go = base_font.render(f"Game Over - Score: {score} (Best: {highscore})", True, (255, 220, 220))
            base.blit(go, (base_w//2 - go.get_width()//2, base_h//2))
            ri = base_font.render("Press R to select new character, ESC to quit", True, (230, 230, 240))
            base.blit(ri, (base_w//2 - ri.get_width()//2, base_h//2 + 20))
        
        # HUD
        s = base_font.render(f"Score: {score}", True, (220, 255, 255))
        base.blit(s, (6, 4))
        h = base_font.render(f"Best: {highscore}", True, (180, 230, 255))
        base.blit(h, (6, 18))
        
        # Environment indicator
        env_text = base_font.render(f"Zone: {current_env}", True, (180, 220, 240))
        base.blit(env_text, (6, 32))
        
        # Power-up indicator
        if turtle.powered_up:
            power_text = base_font.render(f"POWER-UP: {int(turtle.powerup_timer)}s", 
                                        True, (255, 200, 100))
            base.blit(power_text, (base_w//2 - power_text.get_width()//2, 10))
        else:
            # Jellyfish counter
            jelly_text = base_font.render(f"Jellies: {turtle.jellyfish_eaten}/{POWERUP_THRESHOLD}", 
                                         True, (200, 180, 255))
            base.blit(jelly_text, (base_w//2 - jelly_text.get_width()//2, 10))
        
        # Hearts
        for i in range(turtle.health):
            heart_x = base_w - 12 - i * 12
            pygame.draw.circle(base, (240, 90, 100), (heart_x - 4, 12), 3)
            pygame.draw.circle(base, (240, 90, 100), (heart_x, 12), 3)
            pygame.draw.polygon(base, (240, 90, 100), 
                              [(heart_x - 8, 14), (heart_x + 4, 14), (heart_x - 2, 20)])
        
        # Invulnerability flash
        if turtle.iframes > 0 and (int(t * 0.01) % 2 == 0):
            pygame.draw.rect(base, (255, 255, 255), (0, 0, base_w, base_h), 2)
        
        # Scale to window
        pygame.transform.scale(base, (current_w, current_h), screen)
        pygame.display.flip()

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        _msgbox("Error", f"{e}\n\nTry:\n- pip install --upgrade pygame\n- Python 3.10-3.12")