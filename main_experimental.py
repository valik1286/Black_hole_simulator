import pygame
import math
import random
import numpy as np
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode((900, 900))
clock = pygame.time.Clock()

# --- ПАРАМЕТРИ СИМУЛЯЦІЇ ---
CENTER = np.array([450, 450])
BLACK_HOLE_RADIUS = 60
GRAVITY_RADIUS = 300
GRAVITY_CONSTANT = 15000
LIGHT_BEND_INTENSITY = 1.6
ACCRETION_COLOR = (255, 140, 0)
SPHERE_COLOR = (180, 200, 255)
BACKGROUND_COLOR = (0, 0, 0)
FPS = 300
EVAPORATION_RATE = 0.02

# --- НОВІ ПАРАМЕТРИ ---
ISCO_RADIUS_FACTOR = 1.6
ISCO_COLOR = (255, 69, 0)
BH_MASS_MULTIPLIER = 1000
DISK_ROTATION_SPEED = 0.3
MAX_CHARGE_FOR_BH = 2000
PARTICLE_COUNT_ON_MERGE = 40
BH_GRAVITY_FACTOR = 0.000001
DOPPLER_FACTOR = 0.5

# --- ПАРАМЕТРИ ЗІРОК ---
stars = []
STAR_SPAWN_RATE = 0.02
MAX_STARS = 200
STAR_LIFETIME = 150
STAR_COLOR = (255, 255, 255)

# --- СТАНИ ---
objects = []
black_holes = [{
    "center": CENTER.astype(float),
    "radius": BLACK_HOLE_RADIUS,
    "gravity": GRAVITY_CONSTANT,
    "vel": np.array([0.0, 0.0]),
    "mass": BLACK_HOLE_RADIUS * BH_MASS_MULTIPLIER
}]
charging = False
charge_time = 0
MAX_CHARGE = 1500
disk_angle = 0
INITIAL_BH_MASS = BLACK_HOLE_RADIUS * BH_MASS_MULTIPLIER

# --- РІДКІ ЗІРКИ ---
def draw_rare_noise_stars():
    global stars
    if random.random() < STAR_SPAWN_RATE and len(stars) < MAX_STARS:
        pos_x = random.randint(0, screen.get_width() - 1)
        pos_y = random.randint(0, screen.get_height() - 1)
        stars.append({"pos": (pos_x, pos_y), "life": STAR_LIFETIME})
    survivors = []
    for star in stars:
        star["life"] -= 1
        if star["life"] > 0:
            screen.set_at(star["pos"], STAR_COLOR)
            survivors.append(star)
    stars = survivors

# --- ЧОРНІ ДІРИ ---
def draw_black_hole():
    global disk_angle
    for i, bh in enumerate(black_holes):
        bh_center = bh["center"]
        bh_radius = bh["radius"]
        isco_radius = bh_radius * ISCO_RADIUS_FACTOR
        for k in range(int(isco_radius - bh_radius)):
            color_fade = k / (isco_radius - bh_radius)
            r = int(ISCO_COLOR[0] * (1 - color_fade))
            g = int(ISCO_COLOR[1] * (1 - color_fade))
            b = 0
            pygame.draw.circle(screen, (r, g, b), bh_center.astype(int), bh_radius + k, 1)
        pygame.draw.circle(screen, (0, 0, 0), bh_center.astype(int), bh_radius)
        for j in range(int(bh_radius * 1.2)):
            r = max(0, 255 - j * 3)
            g = max(0, 140 - j * 2)
            b = 0
            pygame.draw.circle(screen, (r, g, b), bh_center.astype(int), bh_radius + j, 1)
        if i == 0:
            current_disk_speed = DISK_ROTATION_SPEED * (1 + (bh["mass"] / INITIAL_BH_MASS) * 0.5)
            disk_angle += current_disk_speed
            if disk_angle > 360:
                disk_angle -= 360
            for j in range(360):
                angle = math.radians(j + disk_angle)
                r1 = bh_radius + 40
                r2 = bh_radius + 110
                z_factor = 0.3 + 0.7 * abs(math.sin(angle)) * 0.5
                x1 = bh_center[0] + math.cos(angle) * r1
                y1 = bh_center[1] + math.sin(angle) * r1 * z_factor
                x2 = bh_center[0] + math.cos(angle) * r2
                y2 = bh_center[1] + math.sin(angle) * r2 * z_factor
                color_boost = 1 + math.cos(angle) * DOPPLER_FACTOR
                color_intensity = 255 - int(255 * (j / 360))
                R = 255
                G = max(120, color_intensity)
                B = 0
                c = (min(255, int(R * color_boost)),
                     min(255, int(G * color_boost)),
                     min(255, int(B * color_boost)))
                pygame.draw.line(screen, c, (x1, y1), (x2, y2), 2)

# --- ВИГИН СВІТЛА ---
def draw_light_distortion(surface):
    arr = pygame.surfarray.pixels3d(surface)
    height, width = surface.get_height(), surface.get_width()
    for bh in black_holes:
        bh_center = bh["center"]
        for y in range(0, height, 8):
            for x in range(0, width, 8):
                dx, dy = x - bh_center[0], y - bh_center[1]
                dist = math.sqrt(dx**2 + dy**2)
                if dist < GRAVITY_RADIUS:
                    factor = LIGHT_BEND_INTENSITY * (1 - dist / GRAVITY_RADIUS)
                    offset_x = int(dx * factor * 0.05)
                    offset_y = int(dy * factor * 0.05)
                    src_x = max(0, min(width-1, x + offset_x))
                    src_y = max(0, min(height-1, y + offset_y))
                    arr[x, y] = arr[src_x, src_y]
    del arr

# --- СПАВН ОБ'ЄКТІВ ---
def spawn_object(pos, radius):
    mass = float(radius * 2)
    radius_float = float(radius)
    angle = random.uniform(0, 2 * math.pi)
    speed = np.array([math.cos(angle), math.sin(angle)]) * random.uniform(1.5, 3.0)
    if radius_float < 15:
        color = (100, 150, 255)
    else:
        color = SPHERE_COLOR
    objects.append({
        "pos": np.array(pos, dtype=float),
        "vel": speed,
        "mass": mass,
        "radius": radius_float,
        "color": color
    })

def spawn_black_hole(pos):
    mass_new = BLACK_HOLE_RADIUS * 0.7 * BH_MASS_MULTIPLIER
    vel_x = random.uniform(-0.5, 0.5)
    vel_y = random.uniform(-0.5, 0.5)
    black_holes.append({
        "center": np.array(pos, dtype=float),
        "radius": BLACK_HOLE_RADIUS * 0.7,
        "gravity": GRAVITY_CONSTANT * 0.8,
        "vel": np.array([vel_x, vel_y]),
        "mass": mass_new
    })
    print(f"Нова чорна діра на {pos}. Кількість: {len(black_holes)}.")

# --- ОНОВЛЕННЯ ОБ'ЄКТІВ ---
def update_objects():
    global objects, black_holes
    survivors = []
    # --- ЧД ВЗАЄМОДІЯ ---
    new_bh_velocities = [np.array([0.0, 0.0]) for _ in black_holes]
    i = 0
    while i < len(black_holes):
        bh1 = black_holes[i]
        j = i + 1
        while j < len(black_holes):
            bh2 = black_holes[j]
            diff = bh2["center"] - bh1["center"]
            dist = np.linalg.norm(diff)
            if dist < (bh1["radius"] + bh2["radius"]) * 0.8:
                total_mass = bh1["mass"] + bh2["mass"]
                bh1["center"] = (bh1["center"] * bh1["mass"] + bh2["center"] * bh2["mass"]) / total_mass
                bh1["vel"] = (bh1["vel"] * bh1["mass"] + bh2["vel"] * bh2["mass"]) / total_mass
                bh1["mass"] = total_mass
                bh1["radius"] = (bh1["radius"]**3 + bh2["radius"]**3)**(1/3)
                bh1["gravity"] = bh1["mass"] / BH_MASS_MULTIPLIER * GRAVITY_CONSTANT / BLACK_HOLE_RADIUS
                for _ in range(PARTICLE_COUNT_ON_MERGE):
                    angle = random.uniform(0, 2 * math.pi)
                    speed_boost = random.uniform(3, 7)
                    objects.append({
                        "pos": bh1["center"].copy(),
                        "vel": np.array([math.cos(angle), math.sin(angle)]) * speed_boost,
                        "mass": 2.0,
                        "radius": 3.0,
                        "color": (255, 255, 255)
                    })
                black_holes.pop(j)
                new_bh_velocities.pop(j)
                continue
            force_magnitude = (GRAVITY_CONSTANT * bh1["mass"] * bh2["mass"] / (dist**2)) * BH_GRAVITY_FACTOR
            new_bh_velocities[i] += diff / dist * force_magnitude / bh1["mass"]
            new_bh_velocities[j] -= diff / dist * force_magnitude / bh2["mass"]
            j += 1
        i += 1
    for bh, accel in zip(black_holes, new_bh_velocities):
        bh["vel"] += accel
        bh["center"] += bh["vel"]
    # --- ЗВИЧАЙНІ ОБ'ЄКТИ ---
    for obj in objects:
        total_force = np.array([0.0, 0.0])
        is_eaten = False
        for bh in black_holes:
            bh_center = bh["center"]
            bh_radius = bh["radius"]
            bh_gravity = bh["gravity"]
            diff = bh_center - obj["pos"]
            dist = np.linalg.norm(diff)
            if dist <= bh_radius * 1.5 and dist > bh_radius:
                if float(obj.get("radius", 0)) > 5:
                    is_eaten = True
                    break
                fade_factor = 1.0 - (dist - bh_radius) / (bh_radius * 0.5)
                r = int(255 * fade_factor)
                g = int(obj["color"][1] * (1.0 - fade_factor * 0.3))
                b = int(obj["color"][2] * (1.0 - fade_factor * 0.3))
                obj["color"] = (max(r, 80), g, b)
            elif dist <= bh_radius:
                is_eaten = True
                if 'eaten_timer' not in obj:
                    obj['eaten_timer'] = 0
                    obj['initial_color'] = obj["color"]
                obj['eaten_timer'] += 1
                mass_ratio = bh["mass"] / INITIAL_BH_MASS
                MAX_FADE_FRAMES = 30 / max(0.1, mass_ratio)
                if obj['eaten_timer'] >= MAX_FADE_FRAMES:
                    break
                fade = 1.0 - (obj['eaten_timer'] / MAX_FADE_FRAMES)
                r = int(obj['initial_color'][0] * fade + 255 * (1-fade))
                g = int(obj['initial_color'][1] * fade * 0.5)
                b = int(obj['initial_color'][2] * fade * 0.5)
                obj["color"] = (max(r, 0), max(g, 0), max(b, 0))
                survivors.append(obj)
                pygame.draw.circle(screen, obj["color"], obj["pos"].astype(int), int(obj["radius"]))
                continue
            force_magnitude = (bh_gravity / (dist**2)) * 0.1
            total_force += diff / dist * force_magnitude
        if float(obj.get("radius", 0)) < 1:
            continue
        if not is_eaten:
            obj["vel"] += total_force
            obj["pos"] += obj["vel"]
            obj["radius"] = float(obj["radius"]) - EVAPORATION_RATE
            survivors.append(obj)
            pygame.draw.circle(screen, obj["color"], obj["pos"].astype(int), int(obj["radius"]))
        else:
            current_radius = float(obj.get("radius", 0))
            if current_radius > 5:
                for _ in range(4):
                    new_r = float(current_radius * 0.4) - EVAPORATION_RATE
                    escape_chance = np.random.randn(2) * 2
                    if random.random() < 0.25:
                        escape_chance *= 3
                    survivors.append({
                        "pos": obj["pos"].copy(),
                        "vel": escape_chance,
                        "mass": float(obj.get("mass", 2) / 2),
                        "radius": new_r,
                        "color": (120, 120, 255)
                    })
    objects = survivors

# --- ГОЛОВНИЙ ЦИКЛ ---
running = True
while running:
    dt = clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            charging = True
            charge_time = 0
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            if charging:
                if charge_time >= MAX_CHARGE + MAX_CHARGE_FOR_BH:
                    spawn_black_hole(pygame.mouse.get_pos())
                elif charge_time > 0:
                    radius = 10 + 40 * min(charge_time / MAX_CHARGE, 1)
                    spawn_object(pygame.mouse.get_pos(), radius)
            charging = False
    if charging:
        charge_time += dt
    screen.fill(BACKGROUND_COLOR)
    draw_black_hole()
    update_objects()
    draw_rare_noise_stars()
    draw_light_distortion(screen)
    if charging:
        radius = 10 + 40 * min(charge_time / MAX_CHARGE, 1)
        color = (0, 255, 0) if charge_time >= MAX_CHARGE + MAX_CHARGE_FOR_BH else (80, 120, 255)
        pygame.draw.circle(screen, color, pygame.mouse.get_pos(), int(radius), 2)
        if charge_time > MAX_CHARGE:
            extra_time = charge_time - MAX_CHARGE
            bh_radius_indicator = 5 + 15 * min(extra_time / MAX_CHARGE_FOR_BH, 1)
            pygame.draw.circle(screen, (255, 0, 0), pygame.mouse.get_pos(), int(radius + bh_radius_indicator), 3)
    pygame.display.flip()

pygame.quit()
