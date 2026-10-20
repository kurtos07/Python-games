# -*- coding: utf-8 -*-
"""
==========================================================================
  CK 1  -  un jeu "inspire de GTA 1" en Python + Pygame (un seul fichier)
==========================================================================
  Installation :  pip install pygame        (pygame 2.x recommande)
  Lancement    :  dans Pyzo -> "Run file as script" (Ctrl+Shift+E)

  Contenu : grande ville generee (routes, trottoirs, parcs, immeubles en
  pseudo-3D), voitures conduisibles avec physique de derapage, circulation,
  pietons (PNJ), police avec niveau de recherche (etoiles), 6 armes,
  explosions, voitures qui brulent, pickups, radar + grande carte.
  PAS de magasins, PAS de missions.

  COMMANDES
    ZQSD / WASD / fleches : se deplacer / conduire (Maj = courir)
    Souris                : viser      |  Clic gauche ou CTRL : tirer
    E (ou F / Entree)     : monter / descendre d'une voiture
    Espace                : frein a main (derapages !)
    1-6 / molette / TAB   : changer d'arme
    M                     : grande carte   |  ESC : pause
==========================================================================
"""
import math
import random
from collections import deque

import pygame

# --------------------------------------------------------------------------
#  CONSTANTES
# --------------------------------------------------------------------------
W, H = 1100, 680
FPS = 60
TILE = 64
PERIOD = 10                 # 3 tuiles de route + 7 tuiles de bloc
NB = 6                      # blocs par cote
N = NB * PERIOD + 3         # taille de la carte en tuiles
WORLD = N * TILE
NN = NB + 1                 # carrefours par ligne
K3D = 0.0011                # force de l'effet 3D des immeubles
LANE = 42                   # decalage de la voie de circulation
PARK = 88                   # decalage des voitures garees

T_ROAD, T_SIDE, T_GRASS, T_BUILD, T_TREE = 0, 1, 2, 3, 4
DIRS = ((1, 0), (0, 1), (-1, 0), (0, -1))

CAR_TYPES = {
    'sedan': dict(L=84, W=40, hp=100, maxv=470, acc=380, brk=700, turn=2.3, mass=1.0),
    'sport': dict(L=80, W=38, hp=80, maxv=640, acc=560, brk=800, turn=2.7, mass=0.9),
    'van': dict(L=104, W=46, hp=160, maxv=360, acc=260, brk=500, turn=1.7, mass=1.8),
    'taxi': dict(L=84, W=40, hp=100, maxv=500, acc=400, brk=700, turn=2.3, mass=1.0),
    'police': dict(L=86, W=40, hp=140, maxv=580, acc=470, brk=800, turn=2.5, mass=1.2),
}
CAR_COLORS = [(200, 40, 40), (40, 90, 200), (225, 225, 225), (45, 45, 50),
              (230, 180, 30), (30, 140, 70), (150, 150, 160), (210, 100, 30),
              (120, 50, 160)]

WEAPONS = [
    dict(name='Poings', melee=True, dmg=18, rate=0.40, pack=0, ammo_max=0, letter='-'),
    dict(name='Pistolet', dmg=22, rate=0.28, speed=900, spread=0.025, pellets=1,
         auto=False, ammo_max=120, life=0.7, pack=30, letter='P'),
    dict(name='Mitraillette', dmg=11, rate=0.075, speed=950, spread=0.07, pellets=1,
         auto=True, ammo_max=400, life=0.7, pack=100, letter='M'),
    dict(name='Fusil a pompe', dmg=14, rate=0.85, speed=850, spread=0.18, pellets=7,
         auto=False, ammo_max=40, life=0.35, pack=12, letter='S'),
    dict(name='Lance-roquettes', rocket=True, dmg=0, rate=1.2, speed=620, spread=0.0,
         pellets=1, auto=False, ammo_max=15, life=2.0, pack=6, letter='R'),
    dict(name='Lance-flammes', flame=True, dmg=4, rate=0.04, speed=330, spread=0.14,
         pellets=1, auto=True, ammo_max=300, life=0.38, pack=100, letter='F'),
]

SHIRTS = [(200, 60, 60), (60, 90, 200), (230, 200, 60), (70, 160, 90), (240, 240, 240),
          (150, 70, 170), (240, 140, 50), (90, 90, 95), (60, 170, 180)]
PANTS = [(40, 40, 60), (70, 60, 40), (30, 30, 30), (60, 70, 110), (100, 100, 100)]
HAIRS = [(30, 20, 15), (90, 60, 30), (220, 190, 90), (150, 150, 150), (15, 15, 15)]
SKINS = [(240, 200, 160), (210, 160, 120), (150, 100, 70), (100, 65, 45)]


# --------------------------------------------------------------------------
#  OUTILS
# --------------------------------------------------------------------------
def clamp(v, a, b):
    return a if v < a else (b if v > b else v)


def wrap_angle(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


# --------------------------------------------------------------------------
#  LA VILLE (generation procedurale)
# --------------------------------------------------------------------------
rng = random.Random(1997)
tiles = [[T_SIDE] * N for _ in range(N)]
buildings = []
tree_list = []
ROOF_COLORS = [(150, 70, 60), (110, 110, 122), (90, 100, 135), (150, 125, 90),
               (80, 115, 95), (165, 155, 145), (125, 80, 105), (70, 95, 115),
               (180, 110, 70), (95, 95, 100)]


class Building:
    def __init__(self, tx, ty, tw, th):
        self.x = tx * TILE
        self.y = ty * TILE
        self.w = tw * TILE
        self.h = th * TILE
        self.ht = rng.choice([60, 80, 100, 130, 170, 230, 300])
        base = rng.choice(ROOF_COLORS)
        self.roof = base
        self.wall = tuple(int(c * 0.78 + 30) for c in base)
        self.id = len(buildings)
        self.ac = (rng.random(), rng.random())
        for yy in range(ty, ty + th):
            for xx in range(tx, tx + tw):
                tiles[yy][xx] = T_BUILD


def split_block(x, y, w, h, depth):
    if depth >= 2 or (depth > 0 and rng.random() < 0.3) or (w < 4 and h < 4):
        buildings.append(Building(x, y, w, h))
        return
    if w >= h and w >= 4:
        c = rng.randint(2, w - 2)
        split_block(x, y, c, h, depth + 1)
        split_block(x + c, y, w - c, h, depth + 1)
    elif h >= 4:
        c = rng.randint(2, h - 2)
        split_block(x, y, w, c, depth + 1)
        split_block(x, y + c, w, h - c, depth + 1)
    else:
        buildings.append(Building(x, y, w, h))


def build_city():
    del buildings[:]
    del tree_list[:]
    for ty in range(N):
        for tx in range(N):
            tiles[ty][tx] = T_ROAD if (tx % PERIOD < 3 or ty % PERIOD < 3) else T_SIDE
    for bj in range(NB):
        for bi in range(NB):
            x0 = bi * PERIOD + 4
            y0 = bj * PERIOD + 4
            if rng.random() < 0.15:           # parc
                for ty in range(y0, y0 + 5):
                    for tx in range(x0, x0 + 5):
                        if rng.random() < 0.3:
                            tiles[ty][tx] = T_TREE
                            tree_list.append((tx * TILE + TILE / 2, ty * TILE + TILE / 2))
                        else:
                            tiles[ty][tx] = T_GRASS
            else:
                split_block(x0, y0, 5, 5, 0)


def tile_at(tx, ty):
    if 0 <= tx < N and 0 <= ty < N:
        return tiles[ty][tx]
    return T_BUILD


def is_zebra(tx, ty):
    rx = tx % PERIOD < 3
    ry = ty % PERIOD < 3
    if rx and ry:
        return False
    if ry:
        return tx % PERIOD in (3, PERIOD - 1)
    if rx:
        return ty % PERIOD in (3, PERIOD - 1)
    return False


def road_blocked(x, y):
    tx = int(x // TILE)
    ty = int(y // TILE)
    return tile_at(tx, ty) == T_ROAD and not is_zebra(tx, ty)


def push_from_tiles(x, y, r):
    """Pousse un cercle hors des tuiles solides. Renvoie [(nx, ny, penetration)]."""
    out = []
    tx0 = int((x - r) // TILE)
    tx1 = int((x + r) // TILE)
    ty0 = int((y - r) // TILE)
    ty1 = int((y + r) // TILE)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            t = tile_at(tx, ty)
            if t == T_BUILD:
                rx = tx * TILE
                ry = ty * TILE
                cx = min(max(x, rx), rx + TILE)
                cy = min(max(y, ry), ry + TILE)
                dx = x - cx
                dy = y - cy
                d2 = dx * dx + dy * dy
                if d2 < r * r:
                    if d2 > 1e-6:
                        d = math.sqrt(d2)
                        out.append((dx / d, dy / d, r - d))
                    else:
                        l = x - rx
                        rr = rx + TILE - x
                        tp = y - ry
                        bt = ry + TILE - y
                        m = min(l, rr, tp, bt)
                        if m == l:
                            out.append((-1.0, 0.0, l + r))
                        elif m == rr:
                            out.append((1.0, 0.0, rr + r))
                        elif m == tp:
                            out.append((0.0, -1.0, tp + r))
                        else:
                            out.append((0.0, 1.0, bt + r))
            elif t == T_TREE:
                cx = tx * TILE + TILE / 2
                cy = ty * TILE + TILE / 2
                dx = x - cx
                dy = y - cy
                rr = r + 11
                d2 = dx * dx + dy * dy
                if d2 < rr * rr:
                    if d2 > 1e-6:
                        d = math.sqrt(d2)
                    else:
                        d, dx, dy = 1.0, 1.0, 0.0
                    out.append((dx / d, dy / d, rr - d))
    return out


def move_entity(o, vx, vy, dt, allow_road=True):
    nx = o.x + vx * dt
    ny = o.y + vy * dt
    if not allow_road and road_blocked(nx, ny) and not road_blocked(o.x, o.y):
        return False
    o.x = nx
    o.y = ny
    blocked = False
    for _ in range(2):
        ps = push_from_tiles(o.x, o.y, o.r)
        if not ps:
            break
        blocked = True
        for ax, ay, pen in ps:
            o.x += ax * pen
            o.y += ay * pen
    return not blocked


# --- graphe routier (pour la circulation et la police) ---------------------
def node_pos(i, j):
    return ((i * PERIOD + 1.5) * TILE, (j * PERIOD + 1.5) * TILE)


def nearest_node(x, y):
    i = int(clamp(round((x / TILE - 1.5) / PERIOD), 0, NB))
    j = int(clamp(round((y / TILE - 1.5) / PERIOD), 0, NB))
    return i, j


def lane_pt(i, j, d, ahead):
    nx, ny = node_pos(i, j)
    dx, dy = d
    rx, ry = -dy, dx
    return (nx + dx * ahead + rx * LANE, ny + dy * ahead + ry * LANE)


def valid_node(i, j):
    return 0 <= i < NN and 0 <= j < NN


# --------------------------------------------------------------------------
#  RESSOURCES GRAPHIQUES
# --------------------------------------------------------------------------
SIDE_TILES = []
GRASS_TILES = []
ROAD_CACHE = {}
CAR_SPR = {}
FONTS = {}
ACACHE = {}
GROUND_TILE = None
MINIMAP = None
BIGMAP = None


def rrect(surf, col, rect, rad, width=0):
    try:
        pygame.draw.rect(surf, col, rect, width, border_radius=rad)
    except TypeError:
        pygame.draw.rect(surf, col, rect, width)


def alpha_circle(surf, color, alpha, r, pos):
    r = max(1, int(r))
    a = max(0, min(255, int(alpha))) // 16 * 16
    if a <= 0:
        return
    key = (color, a, r)
    s = ACACHE.get(key)
    if s is None:
        if len(ACACHE) > 700:
            ACACHE.clear()
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (color[0], color[1], color[2], a), (r, r), r)
        ACACHE[key] = s
    surf.blit(s, (int(pos[0]) - r, int(pos[1]) - r))


def draw_text(surf, txt, fkey, col, pos, center=False, shadow=True):
    f = FONTS[fkey]
    img = f.render(txt, True, col)
    r = img.get_rect()
    if center:
        r.center = pos
    else:
        r.topleft = pos
    if shadow:
        sh = f.render(txt, True, (0, 0, 0))
        surf.blit(sh, (r.x + 2, r.y + 2))
    surf.blit(img, r)


def star_pts(cx, cy, r):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return pts


def make_asphalt(seed):
    s = pygame.Surface((TILE, TILE))
    s.fill((62, 62, 66))
    r = random.Random(seed)
    for _ in range(50):
        c = r.randint(50, 74)
        s.set_at((r.randrange(TILE), r.randrange(TILE)), (c, c, c + 4))
    return s


def road_key(tx, ty):
    rx = tx % PERIOD < 3
    ry = ty % PERIOD < 3
    if rx and ry:
        return ('x', 0, False)
    if ry:
        return ('h', ty % PERIOD, tx % PERIOD in (3, PERIOD - 1))
    return ('v', tx % PERIOD, ty % PERIOD in (3, PERIOD - 1))


def road_tile(tx, ty):
    key = road_key(tx, ty)
    var = (tx * 5 + ty * 3) % 3
    full = (key, var)
    s = ROAD_CACHE.get(full)
    if s is not None:
        return s
    o, part, zeb = key
    s = make_asphalt(var).copy()
    yel = (225, 190, 40)
    curb = (150, 150, 148)
    white = (215, 215, 212)
    if o == 'h':
        if part == 1:
            pygame.draw.rect(s, yel, (0, 28, TILE, 3))
            pygame.draw.rect(s, yel, (0, 34, TILE, 3))
        if part == 0:
            pygame.draw.rect(s, curb, (0, 0, TILE, 4))
        if part == 2:
            pygame.draw.rect(s, curb, (0, TILE - 4, TILE, 4))
        if zeb:
            for yy in range(4, TILE, 16):
                pygame.draw.rect(s, white, (6, yy, TILE - 12, 8))
    elif o == 'v':
        if part == 1:
            pygame.draw.rect(s, yel, (28, 0, 3, TILE))
            pygame.draw.rect(s, yel, (34, 0, 3, TILE))
        if part == 0:
            pygame.draw.rect(s, curb, (0, 0, 4, TILE))
        if part == 2:
            pygame.draw.rect(s, curb, (TILE - 4, 0, 4, TILE))
        if zeb:
            for xx in range(4, TILE, 16):
                pygame.draw.rect(s, white, (xx, 6, 8, TILE - 12))
    ROAD_CACHE[full] = s
    return s


def make_car_sprites(kind, color, variant):
    sp = CAR_TYPES[kind]
    L = sp['L']
    Wd = sp['W']
    burnt = (variant == 'burnt')
    if burnt:
        color = (40, 38, 36)
    body = pygame.Surface((L, Wd), pygame.SRCALPHA)
    roof = pygame.Surface((L, Wd), pygame.SRCALPHA)
    dark = tuple(int(c * 0.55) for c in color)
    light = tuple(min(255, int(c * 1.2) + 12) for c in color)
    glass = (25, 25, 28) if burnt else (70, 100, 130)
    for wx in (int(L * 0.14), int(L * 0.66)):
        pygame.draw.rect(body, (15, 15, 15), (wx, 0, 15, Wd))
    rrect(body, color, (1, 3, L - 2, Wd - 6), 7)
    rrect(body, dark, (1, 3, L - 2, Wd - 6), 7, 2)
    pygame.draw.rect(body, dark, (int(L * 0.80), 6, 2, Wd - 12))
    pygame.draw.rect(body, dark, (int(L * 0.10), 6, 2, Wd - 12))
    if not burnt:
        for yy in (5, Wd - 11):
            pygame.draw.rect(body, (255, 245, 190), (L - 5, yy, 4, 6))
            pygame.draw.rect(body, (200, 30, 30), (1, yy, 4, 6))
    if kind == 'police' and not burnt:
        pygame.draw.rect(body, (30, 60, 170), (int(L * 0.2), 3, int(L * 0.5), 3))
        pygame.draw.rect(body, (30, 60, 170), (int(L * 0.2), Wd - 6, int(L * 0.5), 3))
    if kind == 'van':
        cx0, cw = int(L * 0.10), int(L * 0.68)
    else:
        cx0, cw = int(L * 0.28), int(L * 0.42)
    rrect(roof, light, (cx0, 5, cw, Wd - 10), 4)
    pygame.draw.rect(roof, glass, (cx0 + cw - 7, 7, 6, Wd - 14))
    if kind != 'van':
        pygame.draw.rect(roof, glass, (cx0 + 1, 7, 5, Wd - 14))
    if kind == 'police' and not burnt:
        c1, c2 = ((255, 30, 30), (40, 80, 255)) if variant == 0 else ((40, 80, 255), (255, 30, 30))
        half = (Wd - 12) // 2
        pygame.draw.rect(roof, c1, (cx0 + cw // 2 - 2, 6, 5, half))
        pygame.draw.rect(roof, c2, (cx0 + cw // 2 - 2, 6 + half, 5, half))
    if kind == 'taxi' and not burnt:
        pygame.draw.rect(roof, (255, 255, 200), (cx0 + cw // 2 - 3, Wd // 2 - 5, 6, 10))
    return body.convert_alpha(), roof.convert_alpha()


def car_sprites(kind, color, variant):
    key = (kind, color, variant)
    s = CAR_SPR.get(key)
    if s is None:
        s = make_car_sprites(kind, color, variant)
        CAR_SPR[key] = s
    return s


def init_assets():
    global GROUND_TILE
    del SIDE_TILES[:]
    del GRASS_TILES[:]
    for v in range(2):
        s = pygame.Surface((TILE, TILE))
        s.fill((178, 176, 170) if v == 0 else (170, 168, 162))
        pygame.draw.rect(s, (140, 138, 133), (0, 0, TILE, TILE), 1)
        pygame.draw.line(s, (152, 150, 145), (TILE // 2, 0), (TILE // 2, TILE))
        pygame.draw.line(s, (152, 150, 145), (0, TILE // 2), (TILE, TILE // 2))
        SIDE_TILES.append(s)
    for v in range(4):
        s = pygame.Surface((TILE, TILE))
        s.fill((74, 134, 64))
        r = random.Random(v)
        for _ in range(60):
            c = (r.randint(58, 92), r.randint(112, 150), r.randint(48, 76))
            pygame.draw.rect(s, c, (r.randrange(TILE), r.randrange(TILE), r.randint(2, 4), r.randint(2, 4)))
        GRASS_TILES.append(s)
    GROUND_TILE = pygame.Surface((TILE, TILE))
    GROUND_TILE.fill((52, 50, 52))
    FONTS['s'] = pygame.font.Font(None, 24)
    FONTS['m'] = pygame.font.Font(None, 34)
    FONTS['l'] = pygame.font.Font(None, 70)
    FONTS['xl'] = pygame.font.Font(None, 220)


def make_minimaps():
    global MINIMAP, BIGMAP
    cols = {T_ROAD: (70, 70, 78), T_SIDE: (150, 150, 145), T_GRASS: (60, 120, 55),
            T_TREE: (40, 100, 45), T_BUILD: (120, 90, 80)}
    s = pygame.Surface((N * 4, N * 4))
    for ty in range(N):
        for tx in range(N):
            pygame.draw.rect(s, cols[tiles[ty][tx]], (tx * 4, ty * 4, 4, 4))
    for b in buildings:
        pygame.draw.rect(s, b.roof, (int(b.x / 16), int(b.y / 16), int(b.w / 16), int(b.h / 16)))
    MINIMAP = s
    BIGMAP = pygame.transform.scale(s, (N * 10, N * 10))


# --------------------------------------------------------------------------
#  ENTITES
# --------------------------------------------------------------------------
class Grid:
    def __init__(self, cs=128):
        self.cs = cs
        self.d = {}

    def clear(self):
        self.d.clear()

    def add(self, o):
        self.d.setdefault((int(o.x // self.cs), int(o.y // self.cs)), []).append(o)

    def near(self, x, y, r):
        cs = self.cs
        res = []
        for cy in range(int((y - r) // cs), int((y + r) // cs) + 1):
            for cx in range(int((x - r) // cs), int((x + r) // cs) + 1):
                lst = self.d.get((cx, cy))
                if lst:
                    res.extend(lst)
        return res


class Bullet:
    __slots__ = ('x', 'y', 'vx', 'vy', 'dmg', 'owner', 'life', 'kind', 'max')

    def __init__(self, x, y, vx, vy, dmg, owner, life, kind):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.dmg, self.owner, self.life, self.kind = dmg, owner, life, kind
        self.max = life


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max', 'size', 'grow', 'color', 'kind')

    def __init__(self, x, y, vx, vy, life, size, color, kind, grow=0.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max = life
        self.size, self.color, self.kind, self.grow = size, color, kind, grow


class Explosion:
    def __init__(self, x, y, r):
        self.x, self.y, self.r = x, y, r
        self.t = 0.0
        self.dur = 0.7


class Pickup:
    def __init__(self, x, y, kind, val):
        self.x, self.y, self.kind, self.val = x, y, kind, val
        self.active = True
        self.t = 0.0


class Player:
    def __init__(self):
        self.x = self.y = 0.0
        self.r = 9
        self.hp = 100.0
        self.armor = 0.0
        self.angle = 0.0
        self.weapon = 1
        self.ammo = {1: 40}
        self.cd = 0.0
        self.car = None
        self.dead = False
        self.dead_t = 0.0
        self.anim = 0.0
        self.punch = 0.0
        self.flash = 0.0
        self.hurt = 0.0
        self.fire_prev = False
        self.moving = False
        self.shirt = (215, 55, 40)
        self.pants = (40, 45, 90)
        self.hair = (235, 200, 70)
        self.skin = (240, 200, 160)


class Ped:
    def __init__(self, x, y, kind='civ'):
        self.x, self.y = x, y
        self.r = 9
        self.kind = kind
        self.hp = 40.0 if kind == 'civ' else 70.0
        self.heading = random.choice([0, math.pi / 2, math.pi, -math.pi / 2])
        self.angle = self.heading
        self.timer = random.uniform(0.5, 4.0)
        self.idle = False
        self.state = 'walk'
        self.flee_t = 0.0
        self.anim = random.random() * 6
        self.cd = random.uniform(0.3, 1.2)
        self.alive = True
        self.moving = False
        if kind == 'cop':
            self.shirt, self.pants, self.hair = (30, 60, 170), (20, 30, 80), (20, 20, 40)
        else:
            self.shirt = random.choice(SHIRTS)
            self.pants = random.choice(PANTS)
            self.hair = random.choice(HAIRS)
        self.skin = random.choice(SKINS)

    def flee(self, fx, fy, t):
        if self.kind != 'civ':
            return
        self.state = 'flee'
        self.flee_t = t
        self.heading = math.atan2(self.y - fy, self.x - fx) + random.uniform(-0.5, 0.5)

    def wander(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.heading = random.choice([0, math.pi / 2, math.pi, -math.pi / 2])
            self.timer = random.uniform(2.0, 6.0)
            self.idle = random.random() < 0.18
        self.moving = False
        if not self.idle:
            sp = 58.0
            ok = move_entity(self, math.cos(self.heading) * sp, math.sin(self.heading) * sp,
                             dt, allow_road=False)
            self.angle = self.heading
            if ok:
                self.moving = True
                self.anim += dt * 9
            else:
                self.heading = random.choice([0, math.pi / 2, math.pi, -math.pi / 2])
                self.timer = random.uniform(0.5, 2.0)

    def update(self, dt, G):
        for (nx, ny, nr) in G.noises:
            if self.kind == 'civ' and self.state != 'flee' and \
                    (self.x - nx) ** 2 + (self.y - ny) ** 2 < nr * nr:
                self.flee(nx, ny, random.uniform(3.0, 6.0))
        if self.kind == 'cop' and G.stars > 0 and not G.player.dead:
            tx, ty = G.player_pos()
            dx = tx - self.x
            dy = ty - self.y
            d = math.hypot(dx, dy) + 1e-6
            self.angle = math.atan2(dy, dx)
            self.moving = False
            if d > 230:
                if move_entity(self, dx / d * 140, dy / d * 140, dt):
                    self.moving = True
                    self.anim += dt * 11
            self.cd -= dt
            if d < 430 and self.cd <= 0:
                self.cd = random.uniform(0.8, 1.5)
                a = self.angle + random.uniform(-0.1, 0.1)
                G.bullets.append(Bullet(self.x + math.cos(a) * 12, self.y + math.sin(a) * 12,
                                        math.cos(a) * 700, math.sin(a) * 700, 7, 'cop', 0.9, 'bullet'))
                G.noise(self.x, self.y, 450)
        elif self.state == 'flee':
            self.flee_t -= dt
            sp = 215.0
            ok = move_entity(self, math.cos(self.heading) * sp, math.sin(self.heading) * sp, dt)
            self.angle = self.heading
            self.moving = True
            self.anim += dt * 16
            if not ok:
                self.heading += random.choice([-1.4, 1.4])
            if self.flee_t <= 0:
                self.state = 'walk'
                self.timer = 0.5
        else:
            self.wander(dt)


class Car:
    _id = 0

    def __init__(self, kind, color, x, y, a):
        self.kind = kind
        self.sp = CAR_TYPES[kind]
        self.color = color
        self.x, self.y, self.a = x, y, a
        self.vx = self.vy = 0.0
        self.hp = float(self.sp['hp'])
        self.state = 'ok'          # ok / burning / wreck
        self.ai = None             # None / traffic / police / player
        self.cr = self.sp['W'] / 2 + 1
        self.coff = self.sp['L'] / 2 - self.cr
        self.burn = 0.0
        self.wps = []
        self.node = (0, 0)
        self.dirv = (1, 0)
        self.stuck = 0.0
        self.rev = 0.0
        self.rev_steer = 1.0
        self.blocked = False
        self.btime = 0.0
        self.noblock = 0.0
        self.tspeed = random.uniform(190, 260)
        self.throttle = 0.0
        self.steer = 0.0
        self.hb = False
        self.by = None
        self.smoke_t = 0.0
        self.skid_prev = None
        self.id = Car._id
        Car._id += 1

    def speed(self):
        return math.hypot(self.vx, self.vy)

    def circles(self):
        fx, fy = math.cos(self.a), math.sin(self.a)
        return [(self.x + fx * o, self.y + fy * o) for o in (-self.coff, 0.0, self.coff)]


# --------------------------------------------------------------------------
#  LE JEU
# --------------------------------------------------------------------------
def kd(keys, *codes):
    for c in codes:
        if keys[c]:
            return True
    return False


class Game:
    def __init__(self):
        self.player = Player()
        self.cars = []
        self.peds = []
        self.bullets = []
        self.particles = []
        self.explosions = []
        self.pickups = []
        self.decals = deque(maxlen=300)
        self.skids = deque(maxlen=900)
        self.ped_grid = Grid()
        self.car_grid = Grid()
        self.noises = []
        self.msgs = []
        self.score = 0
        self.kills = 0
        self.deaths = 0
        self.heat = 0.0
        self.stars = 0
        self.shake = 0.0
        self.t = 0.0
        self.frame = 0
        self.zoom = 1.0
        self.camx = self.camy = 0.0
        self.ox = self.oy = 0
        self.vw, self.vh = W, H
        self.bfs = None
        self.bfs_node = None
        self.spawn_t = 0.0
        self.show_map = False
        self.populate()

    # ------------------------------------------------------------ monde
    def populate(self):
        p = self.player
        p.x, p.y = 33.5 * TILE, 33.5 * TILE
        self.camx, self.camy = p.x, p.y
        # voiture garee juste a cote du joueur
        c = Car('sport', (200, 40, 40), 2104, 2260, -math.pi / 2)
        self.cars.append(c)
        # armes pres du depart
        self.pickups.append(Pickup(p.x + 110, p.y, 'weapon', 2))
        self.pickups.append(Pickup(p.x + 150, p.y, 'weapon', 3))
        self.pickups.append(Pickup(p.x + 110, p.y + 40, 'health', 50))
        # voitures garees
        tries = 0
        while len(self.cars) < 46 and tries < 400:
            tries += 1
            self.spawn_parked()
        # pickups un peu partout
        sidewalks = []
        for ty in range(N):
            for tx in range(N):
                if tiles[ty][tx] == T_SIDE:
                    sidewalks.append((tx, ty))
        for i in range(24):
            tx, ty = random.choice(sidewalks)
            r = random.random()
            if r < 0.55:
                w = random.choice([1, 2, 2, 3, 3, 4, 5])
                self.pickups.append(Pickup((tx + .5) * TILE, (ty + .5) * TILE, 'weapon', w))
            elif r < 0.8:
                self.pickups.append(Pickup((tx + .5) * TILE, (ty + .5) * TILE, 'health', 50))
            else:
                self.pickups.append(Pickup((tx + .5) * TILE, (ty + .5) * TILE, 'armor', 50))
        for i in range(30):
            self.spawn_ped_random(far=False)
        for i in range(14):
            self.spawn_traffic(far=False)

    def car_free(self, x, y, margin=110):
        for c in self.cars:
            if abs(c.x - x) < margin and abs(c.y - y) < margin:
                return False
        return True

    def spawn_parked(self):
        i, j = random.randrange(NN), random.randrange(NN)
        d = random.choice(DIRS)
        if not valid_node(i + d[0], j + d[1]):
            return
        t = random.uniform(200, 440)
        nx, ny = node_pos(i, j)
        rx, ry = -d[1], d[0]
        x = nx + d[0] * t + rx * PARK
        y = ny + d[1] * t + ry * PARK
        if not self.car_free(x, y) or math.hypot(x - self.player.x, y - self.player.y) < 150:
            return
        kind = random.choice(['sedan', 'sedan', 'sedan', 'sport', 'van', 'taxi'])
        col = (235, 200, 30) if kind == 'taxi' else random.choice(CAR_COLORS)
        c = Car(kind, col, x, y, math.atan2(d[1], d[0]))
        self.cars.append(c)

    def offscreen(self, x, y, margin=900):
        return math.hypot(x - self.camx, y - self.camy) > margin

    def spawn_traffic(self, far=True, police=False):
        for _ in range(12):
            i, j = random.randrange(NN), random.randrange(NN)
            d = random.choice(DIRS)
            if not valid_node(i + d[0], j + d[1]):
                continue
            t = random.uniform(150, 490)
            nx, ny = node_pos(i, j)
            rx, ry = -d[1], d[0]
            x = nx + d[0] * t + rx * LANE
            y = ny + d[1] * t + ry * LANE
            if far and not self.offscreen(x, y, 950):
                continue
            if not self.car_free(x, y, 120):
                continue
            if math.hypot(x - self.player.x, y - self.player.y) < 200:
                continue
            if police:
                c = Car('police', (235, 235, 240), x, y, math.atan2(d[1], d[0]))
                c.ai = 'police'
            else:
                kind = random.choice(['sedan', 'sedan', 'sedan', 'sport', 'van', 'taxi'])
                col = (235, 200, 30) if kind == 'taxi' else random.choice(CAR_COLORS)
                c = Car(kind, col, x, y, math.atan2(d[1], d[0]))
                c.ai = 'traffic'
            c.node = (i + d[0], j + d[1])
            c.dirv = d
            c.wps = [lane_pt(c.node[0], c.node[1], d, -110)]
            spd = 120.0
            c.vx, c.vy = d[0] * spd, d[1] * spd
            self.cars.append(c)
            return True
        return False

    def spawn_ped_random(self, far=True, kind='civ'):
        for _ in range(15):
            tx = random.randrange(N)
            ty = random.randrange(N)
            if tiles[ty][tx] not in (T_SIDE, T_GRASS):
                continue
            x = (tx + random.random()) * TILE
            y = (ty + random.random()) * TILE
            if far and not self.offscreen(x, y, 900):
                continue
            if not far and math.hypot(x - self.player.x, y - self.player.y) < 120:
                continue
            self.peds.append(Ped(x, y, kind))
            return True
        return False

    # ------------------------------------------------------------ utilitaires
    def player_pos(self):
        p = self.player
        if p.car:
            return p.car.x, p.car.y
        return p.x, p.y

    def add_msg(self, txt):
        self.msgs.append([txt, 3.0])
        if len(self.msgs) > 4:
            self.msgs.pop(0)

    def noise(self, x, y, r):
        self.noises.append((x, y, r))

    def mouse_world(self):
        mx, my = pygame.mouse.get_pos()
        return self.ox + mx * self.vw / float(W), self.oy + my * self.vh / float(H)

    def spawn_particle(self, kind, x, y, **kw):
        a = random.uniform(0, math.tau if hasattr(math, 'tau') else 6.2832)
        if kind == 'smoke':
            sp = random.uniform(5, 25)
            g = random.choice([(70, 70, 70), (95, 95, 95), (50, 50, 50)])
            self.particles.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp - 8,
                                           random.uniform(0.8, 1.6), random.uniform(5, 9), g, 'smoke', 14))
        elif kind == 'fire':
            sp = random.uniform(10, 50)
            col = random.choice([(255, 220, 60), (255, 150, 30), (255, 90, 20)])
            self.particles.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp,
                                           random.uniform(0.25, 0.6), random.uniform(5, 10), col, 'fire'))
        elif kind == 'spark':
            sp = random.uniform(80, 240)
            self.particles.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp,
                                           random.uniform(0.1, 0.3), 2, (255, 230, 120), 'spark'))
        elif kind == 'blood':
            sp = random.uniform(30, 140)
            self.particles.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp,
                                           random.uniform(0.2, 0.5), 2, (170, 10, 10), 'blood'))
        elif kind == 'debris':
            sp = random.uniform(100, 380)
            self.particles.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp,
                                           random.uniform(0.5, 1.1), 3, (60, 60, 60), 'debris'))

    # ------------------------------------------------------------ degats
    def hurt_ped(self, p, dmg, by, dirx=0.0, diry=0.0):
        if not p.alive:
            return
        p.hp -= dmg
        for _ in range(3):
            self.spawn_particle('blood', p.x, p.y)
        if p.hp > 0:
            if p.kind == 'civ':
                p.flee(p.x - dirx * 50, p.y - diry * 50, random.uniform(4, 7))
            elif by == 'player':
                self.heat += 0.2
            return
        p.alive = False
        self.decals.append(('blood', p.x, p.y, random.randint(10, 17)))
        self.decals.append(('corpse', p.x, p.y, p.angle, p.shirt, p.pants))
        if by == 'player':
            self.kills += 1
            if p.kind == 'civ':
                self.score += 100
                self.heat += 1.0
            else:
                self.score += 500
                self.heat += 3.0
                self.add_msg('Policier abattu ! +500')

    def hurt_player(self, dmg):
        p = self.player
        if p.dead or dmg <= 0:
            return
        if p.armor > 0:
            ab = min(p.armor, dmg * 0.7)
            p.armor -= ab
            dmg -= ab
        p.hp -= dmg
        p.hurt = 0.25
        if p.hp <= 0:
            self.kill_player()

    def kill_player(self):
        p = self.player
        p.hp = 0
        p.dead = True
        p.dead_t = 0.0
        if p.car:
            p.car.ai = None
            p.car.throttle = 0
            p.car.steer = 0
            p.car = None
        else:
            self.decals.append(('blood', p.x, p.y, 16))
            self.decals.append(('corpse', p.x, p.y, p.angle, p.shirt, p.pants))
        self.deaths += 1
        self.shake = 0

    def respawn(self):
        p = self.player
        for _ in range(200):
            tx, ty = random.randrange(N), random.randrange(N)
            if tiles[ty][tx] == T_SIDE:
                p.x, p.y = (tx + .5) * TILE, (ty + .5) * TILE
                break
        p.dead = False
        p.hp = 100.0
        p.armor = 0.0
        p.weapon = 1
        p.ammo = {1: 30}
        p.car = None
        self.heat = 0.0
        self.camx, self.camy = p.x, p.y
        self.add_msg("Tu reviens a la vie... (la police t'a oublie)")

    def damage_car(self, c, dmg, by=None):
        if c.state != 'ok' or dmg <= 0:
            return
        c.hp -= dmg
        if by:
            c.by = by
        if c.hp <= 0:
            self.ignite(c)

    def ignite(self, c):
        c.state = 'burning'
        c.burn = random.uniform(2.5, 4.0)
        if c.by == 'player' and c.ai == 'police':
            self.heat += 2.0
            self.score += 200
            self.add_msg('Voiture de police detruite ! +200')
        if c.ai in ('traffic', 'police'):
            c.ai = None

    def car_explode(self, c):
        p = self.player
        if p.car is c:
            p.car = None
            p.x, p.y = c.x, c.y
        c.state = 'wreck'
        c.hp = 0
        c.ai = None
        self.explode(c.x, c.y, 125, 140, c.by)

    def explode(self, x, y, radius, dmg, by):
        self.explosions.append(Explosion(x, y, radius))
        d_cam = math.hypot(x - self.camx, y - self.camy)
        self.shake = max(self.shake, 16 * clamp(1 - d_cam / 1000.0, 0.0, 1.0))
        self.noise(x, y, 900)
        for _ in range(14):
            self.spawn_particle('fire', x + random.uniform(-20, 20), y + random.uniform(-20, 20))
        for _ in range(10):
            self.spawn_particle('smoke', x, y)
        for _ in range(10):
            self.spawn_particle('debris', x, y)
        for p in self.peds:
            if p.alive:
                d = math.hypot(p.x - x, p.y - y)
                if d < radius:
                    self.hurt_ped(p, dmg * (1 - d / radius) * 1.3 + 5, by,
                                  (p.x - x) / (d + 1), (p.y - y) / (d + 1))
        pl = self.player
        if not pl.car and not pl.dead:
            d = math.hypot(pl.x - x, pl.y - y)
            if d < radius:
                self.hurt_player(dmg * (1 - d / radius) * 0.8)
        for c in self.cars:
            if c.state == 'wreck':
                continue
            d = math.hypot(c.x - x, c.y - y)
            rr = radius + 40
            if d < rr:
                k = 1 - d / rr
                c.vx += (c.x - x) / (d + 1) * 320 * k
                c.vy += (c.y - y) / (d + 1) * 320 * k
                self.damage_car(c, dmg * k * 1.5, by)

    # ------------------------------------------------------------ armes
    def select_weapon(self, i):
        p = self.player
        if i == 0 or p.ammo.get(i, 0) > 0:
            p.weapon = i
        else:
            self.add_msg("Tu n'as pas cette arme")

    def cycle_weapon(self, step):
        p = self.player
        avail = [i for i in range(len(WEAPONS)) if i == 0 or p.ammo.get(i, 0) > 0]
        if p.weapon in avail:
            k = (avail.index(p.weapon) + (1 if step > 0 else -1)) % len(avail)
        else:
            k = 0
        p.weapon = avail[k]

    def player_fire(self):
        p = self.player
        if p.cd > 0 or p.car or p.dead:
            return
        w = WEAPONS[p.weapon]
        a = p.angle
        ca, sa = math.cos(a), math.sin(a)
        if w.get('melee'):
            p.cd = w['rate']
            p.punch = 0.18
            hx, hy = p.x + ca * 26, p.y + sa * 26
            for ped in self.ped_grid.near(hx, hy, 30):
                if ped.alive and math.hypot(ped.x - hx, ped.y - hy) < ped.r + 16:
                    self.hurt_ped(ped, w['dmg'], 'player', ca, sa)
                    ped.x += ca * 10
                    ped.y += sa * 10
                    break
            return
        if p.ammo.get(p.weapon, 0) <= 0:
            self.add_msg('Plus de munitions !')
            p.cd = 0.4
            p.weapon = 0
            return
        p.ammo[p.weapon] -= 1
        p.cd = w['rate']
        p.flash = 0.06
        mx, my = p.x + ca * 20, p.y + sa * 20
        if w.get('rocket'):
            self.bullets.append(Bullet(mx, my, ca * w['speed'], sa * w['speed'], 0, 'player', w['life'], 'rocket'))
            self.noise(p.x, p.y, 800)
            self.heat += 0.1
        elif w.get('flame'):
            aa = a + random.uniform(-w['spread'], w['spread'])
            sp = w['speed'] * random.uniform(0.8, 1.1)
            self.bullets.append(Bullet(mx, my, math.cos(aa) * sp, math.sin(aa) * sp, w['dmg'], 'player', w['life'], 'flame'))
            self.noise(p.x, p.y, 250)
            self.heat += 0.01
        else:
            for _ in range(w['pellets']):
                aa = a + random.uniform(-w['spread'], w['spread'])
                self.bullets.append(Bullet(mx, my, math.cos(aa) * w['speed'], math.sin(aa) * w['speed'],
                                           w['dmg'], 'player', w['life'], 'bullet'))
            self.noise(p.x, p.y, 650)
            self.heat += 0.03

    # ------------------------------------------------------------ voiture
    def toggle_car(self):
        p = self.player
        if p.dead:
            return
        if p.car:
            c = p.car
            fx, fy = math.cos(c.a), math.sin(c.a)
            rx, ry = -fy, fx
            hw = c.sp['W'] / 2 + 16
            hl = c.sp['L'] / 2 + 16
            cands = [(c.x + rx * hw, c.y + ry * hw), (c.x - rx * hw, c.y - ry * hw),
                     (c.x - fx * hl, c.y - fy * hl), (c.x + fx * hl, c.y + fy * hl)]
            pos = cands[0]
            for (x, y) in cands:
                if not push_from_tiles(x, y, p.r):
                    pos = (x, y)
                    break
            p.x, p.y = pos
            c.ai = None
            c.throttle = 0
            c.steer = 0
            c.hb = True
            p.car = None
        else:
            best, bd = None, 1e9
            for c in self.cars:
                if c.state != 'ok':
                    continue
                d = math.hypot(c.x - p.x, c.y - p.y)
                if d < c.sp['L'] / 2 + 34 and d < bd:
                    best, bd = c, d
            if best is None:
                return
            c = best
            if c.ai in ('traffic', 'police'):
                fx, fy = math.cos(c.a), math.sin(c.a)
                ped = Ped(c.x - fy * 40, c.y + fx * 40, 'civ')
                ped.flee(p.x, p.y, 6)
                self.peds.append(ped)
                self.heat += 1.5 if c.ai == 'police' else 0.5
                self.add_msg('Voiture volee !')
            c.ai = 'player'
            c.wps = []
            p.car = c

    # ------------------------------------------------------------ IA voitures
    def probe(self, c):
        fx, fy = math.cos(c.a), math.sin(c.a)
        rx, ry = -fy, fx
        vf = c.vx * fx + c.vy * fy
        look = 70 + max(0.0, vf) * 0.45
        for o in self.car_grid.near(c.x, c.y, 260):
            if o is c:
                continue
            dx, dy = o.x - c.x, o.y - c.y
            f = dx * fx + dy * fy
            if 0 < f < look + o.sp['L'] / 2:
                lat = dx * rx + dy * ry
                if abs(lat) < (c.sp['W'] + o.sp['W']) / 2 + 2:
                    return True
        for p in self.ped_grid.near(c.x + fx * look * 0.6, c.y + fy * look * 0.6, look):
            if not p.alive:
                continue
            dx, dy = p.x - c.x, p.y - c.y
            f = dx * fx + dy * fy
            if 0 < f < look:
                if abs(dx * rx + dy * ry) < 28:
                    return True
        pl = self.player
        if not pl.car and not pl.dead:
            dx, dy = pl.x - c.x, pl.y - c.y
            f = dx * fx + dy * fy
            if 0 < f < look and abs(dx * rx + dy * ry) < 28:
                return True
        return False

    def plan_traffic(self, c):
        i, j = c.node
        d = c.dirv
        opts = [dd for dd in DIRS if dd != (-d[0], -d[1]) and valid_node(i + dd[0], j + dd[1])]
        if not opts:
            opts = [(-d[0], -d[1])]
        weights = [3.0 if dd == d else 1.0 for dd in opts]
        d2 = random.choices(opts, weights)[0]
        c.dirv = d2
        c.node = (i + d2[0], j + d2[1])
        c.wps = [lane_pt(i, j, d2, 110), lane_pt(c.node[0], c.node[1], d2, -110)]

    def become_traffic(self, c):
        i, j = nearest_node(c.x, c.y)
        opts = [dd for dd in DIRS if valid_node(i + dd[0], j + dd[1])]
        c.node = (i, j)
        c.dirv = random.choice(opts)
        c.wps = []
        c.ai = 'traffic'
        c.tspeed = random.uniform(190, 260)

    def update_bfs(self):
        px, py = self.player_pos()
        ni, nj = nearest_node(px, py)
        if self.bfs is not None and self.bfs_node == (ni, nj):
            return
        dist = [[999] * NN for _ in range(NN)]
        dist[nj][ni] = 0
        q = deque([(ni, nj)])
        while q:
            i, j = q.popleft()
            for dx, dy in DIRS:
                a, b = i + dx, j + dy
                if valid_node(a, b) and dist[b][a] == 999:
                    dist[b][a] = dist[j][i] + 1
                    q.append((a, b))
        self.bfs = dist
        self.bfs_node = (ni, nj)

    def police_target(self, c):
        px, py = self.player_pos()
        if math.hypot(px - c.x, py - c.y) < 450 or self.bfs is None:
            return px, py
        i, j = nearest_node(c.x, c.y)
        best, bd = None, self.bfs[j][i]
        for dx, dy in DIRS:
            a, b = i + dx, j + dy
            if valid_node(a, b) and self.bfs[b][a] < bd:
                bd = self.bfs[b][a]
                best = (a, b)
        if best is None:
            return px, py
        return node_pos(best[0], best[1])

    def ai_control(self, c, dt):
        fx, fy = math.cos(c.a), math.sin(c.a)
        vf = c.vx * fx + c.vy * fy
        if c.rev > 0:
            c.rev -= dt
            return -1.0, c.rev_steer, False
        if c.noblock > 0:
            c.noblock -= dt
        if c.ai == 'police':
            tx, ty = self.police_target(c)
            c.tspeed = 520.0 if math.hypot(tx - c.x, ty - c.y) > 220 else 260.0
        else:
            if not c.wps:
                self.plan_traffic(c)
            tx, ty = c.wps[0]
            if math.hypot(tx - c.x, ty - c.y) < 60:
                c.wps.pop(0)
                if not c.wps:
                    self.plan_traffic(c)
                tx, ty = c.wps[0]
        diff = wrap_angle(math.atan2(ty - c.y, tx - c.x) - c.a)
        steer = clamp(diff * 2.5, -1.0, 1.0)
        tgt = c.tspeed
        blocked = c.blocked and c.noblock <= 0
        if blocked:
            tgt = 0.0
        elif abs(diff) > 0.7:
            tgt = min(tgt, 100.0)
        elif abs(diff) > 0.3:
            tgt = min(tgt, 170.0)
        if vf < tgt - 8:
            th = 1.0 if tgt - vf > 40 else 0.5
        elif vf > tgt + 12:
            th = -0.6
        else:
            th = 0.15
        hb = (tgt == 0.0 and abs(vf) < 10)
        if tgt > 0 and abs(vf) < 10:
            c.stuck += dt
        else:
            c.stuck = 0.0
        if c.stuck > 1.6:
            c.stuck = 0.0
            c.rev = 1.1
            c.rev_steer = random.choice((-1.0, 1.0))
        if blocked:
            c.btime += dt
            if c.btime > 4.5:
                c.btime = 0.0
                c.rev = 1.0
                c.rev_steer = random.choice((-1.0, 1.0))
                c.noblock = 2.5
        else:
            c.btime = 0.0
        return th, steer, hb

    def car_physics(self, c, dt):
        sp = c.sp
        fx, fy = math.cos(c.a), math.sin(c.a)
        rx, ry = -fy, fx
        vf = c.vx * fx + c.vy * fy
        vl = c.vx * rx + c.vy * ry
        th = c.throttle if c.state == 'ok' else 0.0
        if th > 0:
            if vf < -5:
                vf += sp['brk'] * dt
            else:
                vf += sp['acc'] * th * dt * max(0.0, 1.0 - vf / sp['maxv'])
        elif th < 0:
            if vf > 5:
                vf -= sp['brk'] * abs(th) * dt
            else:
                vf -= sp['acc'] * 0.6 * abs(th) * dt * max(0.0, 1.0 + vf / (sp['maxv'] * 0.4))
        vf -= vf * 0.30 * dt
        if th == 0:
            s = math.copysign(min(abs(vf), 90 * dt), vf)
            vf -= s
        if c.ai is None or c.state != 'ok':
            vf -= vf * 3.0 * dt
        elif c.hb:
            vf -= vf * 2.2 * dt
        grip = 7.0 - 3.0 * min(abs(vf) / sp['maxv'], 1.0)
        if c.hb:
            grip = 1.2
        if c.ai is None or c.state != 'ok':
            grip = 6.0
        vl *= math.exp(-grip * dt)
        sf = clamp(vf / 140.0, -1.0, 1.0)
        turn = c.steer * sp['turn'] * sf * (1.0 - 0.35 * min(abs(vf) / sp['maxv'], 1.0))
        if c.hb:
            turn *= 1.5
        c.a += turn * dt
        c.vx = fx * vf + rx * vl
        c.vy = fy * vf + ry * vl
        c.x += c.vx * dt
        c.y += c.vy * dt
        return vf, vl

    def car_tiles(self, c):
        hit = 0.0
        for _ in range(2):
            pushed = False
            fx, fy = math.cos(c.a), math.sin(c.a)
            for o in (-c.coff, 0.0, c.coff):
                for nx, ny, pen in push_from_tiles(c.x + fx * o, c.y + fy * o, c.cr):
                    c.x += nx * pen
                    c.y += ny * pen
                    pushed = True
                    vn = c.vx * nx + c.vy * ny
                    if vn < 0:
                        c.vx -= 1.25 * vn * nx
                        c.vy -= 1.25 * vn * ny
                        hit = max(hit, -vn)
            if not pushed:
                break
        return hit

    def update_cars(self, dt):
        self.car_grid.clear()
        for c in self.cars:
            self.car_grid.add(c)
        px, py = self.player_pos()
        for c in self.cars:
            if c.state == 'ok' and c.ai is None and abs(c.vx) + abs(c.vy) < 1.0:
                continue
            if abs(c.x - px) > 2600 or abs(c.y - py) > 2600:
                continue
            if c.ai == 'player':
                pass
            elif c.ai in ('traffic', 'police') and c.state == 'ok':
                if (self.frame + c.id) % 3 == 0:
                    c.blocked = self.probe(c)
                c.throttle, c.steer, c.hb = self.ai_control(c, dt)
            else:
                c.throttle, c.steer, c.hb = 0.0, 0.0, False
            vf, vl = self.car_physics(c, dt)
            hit = self.car_tiles(c)
            if hit > 150:
                self.damage_car(c, (hit - 150) * 0.12, None)
                for _ in range(3):
                    self.spawn_particle('spark', c.x, c.y)
                if c.ai == 'player':
                    self.shake = max(self.shake, min(10.0, hit / 40.0))
                    self.noise(c.x, c.y, 350)
            # derapages
            if (abs(vl) > 100 or (c.hb and abs(vf) > 120)) and c.state == 'ok':
                fx, fy = math.cos(c.a), math.sin(c.a)
                rx, ry = -fy, fx
                back = -c.sp['L'] * 0.32
                pts = [(c.x + fx * back + rx * c.sp['W'] * 0.38, c.y + fy * back + ry * c.sp['W'] * 0.38),
                       (c.x + fx * back - rx * c.sp['W'] * 0.38, c.y + fy * back - ry * c.sp['W'] * 0.38)]
                if c.skid_prev:
                    for a, b in zip(c.skid_prev, pts):
                        self.skids.append((a[0], a[1], b[0], b[1]))
                c.skid_prev = pts
                if random.random() < dt * 10:
                    self.spawn_particle('smoke', pts[0][0], pts[0][1])
            else:
                c.skid_prev = None
            # etats
            fx, fy = math.cos(c.a), math.sin(c.a)
            if c.state == 'ok':
                if c.hp < 45:
                    c.smoke_t -= dt
                    if c.smoke_t <= 0:
                        c.smoke_t = 0.07
                        self.spawn_particle('smoke', c.x + fx * c.sp['L'] * 0.35, c.y + fy * c.sp['L'] * 0.35)
            elif c.state == 'burning':
                c.burn -= dt
                if random.random() < dt * 30:
                    self.spawn_particle('fire', c.x + random.uniform(-14, 14), c.y + random.uniform(-14, 14))
                if random.random() < dt * 12:
                    self.spawn_particle('smoke', c.x, c.y)
                if c.ai == 'player':
                    self.hurt_player(9 * dt)
                if c.burn <= 0:
                    self.car_explode(c)

    def car_collisions(self, dt):
        for a in self.cars:
            sa = a.speed()
            a_idle = (a.ai is None and a.state == 'ok' and sa < 1.0)
            for b in self.car_grid.near(a.x, a.y, 120):
                if b.id <= a.id:
                    continue
                if a_idle and b.ai is None and b.state == 'ok' and b.speed() < 1.0:
                    continue
                if math.hypot(a.x - b.x, a.y - b.y) > (a.sp['L'] + b.sp['L']) / 2 + 8:
                    continue
                done = False
                for (ax, ay) in a.circles():
                    for (bx, by) in b.circles():
                        dx, dy = ax - bx, ay - by
                        d = math.hypot(dx, dy)
                        rr = a.cr + b.cr
                        if d < rr:
                            if d < 1e-6:
                                dx, dy, d = 1.0, 0.0, 1.0
                            nx, ny = dx / d, dy / d
                            pen = rr - d
                            ma, mb = a.sp['mass'], b.sp['mass']
                            a.x += nx * pen * mb / (ma + mb)
                            a.y += ny * pen * mb / (ma + mb)
                            b.x -= nx * pen * ma / (ma + mb)
                            b.y -= ny * pen * ma / (ma + mb)
                            rel = (a.vx - b.vx) * nx + (a.vy - b.vy) * ny
                            if rel < 0:
                                j = -1.3 * rel / (1.0 / ma + 1.0 / mb)
                                a.vx += nx * j / ma
                                a.vy += ny * j / ma
                                b.vx -= nx * j / mb
                                b.vy -= ny * j / mb
                                imp = -rel
                                if imp > 120:
                                    byp = 'player' if (a.ai == 'player' or b.ai == 'player') else None
                                    self.damage_car(a, (imp - 120) * 0.10 * mb / ma, 'player' if b.ai == 'player' else None)
                                    self.damage_car(b, (imp - 120) * 0.10 * ma / mb, 'player' if a.ai == 'player' else None)
                                    for _ in range(3):
                                        self.spawn_particle('spark', (ax + bx) / 2, (ay + by) / 2)
                                    if byp:
                                        self.shake = max(self.shake, min(9.0, imp / 45.0))
                                        if a.ai == 'police' or b.ai == 'police':
                                            self.heat += 0.4
                                        self.noise(a.x, a.y, 400)
                            done = True
                            break
                    if done:
                        break

    def cars_vs_people(self, dt):
        pl = self.player
        for c in self.cars:
            sp = c.speed()
            if c.state == 'wreck' and sp < 5:
                pass
            cx0, cy0 = c.x, c.y
            reach = c.sp['L'] / 2 + 30
            if sp > 120 and c.state == 'ok':
                for p in self.ped_grid.near(cx0, cy0, reach + 40):
                    if p.kind == 'civ' and p.state != 'flee' and p.alive:
                        if (p.x - cx0) ** 2 + (p.y - cy0) ** 2 < 110 ** 2:
                            p.flee(cx0, cy0, random.uniform(3, 5))
            for p in self.ped_grid.near(cx0, cy0, reach):
                if not p.alive:
                    continue
                for (x, y) in c.circles():
                    dx, dy = p.x - x, p.y - y
                    d = math.hypot(dx, dy)
                    if d < c.cr + p.r:
                        if sp > 40:
                            by = 'player' if c.ai == 'player' else None
                            self.hurt_ped(p, sp * 0.35, by, c.vx / (sp + 1), c.vy / (sp + 1))
                            if not p.alive:
                                c.vx *= 0.97
                                c.vy *= 0.97
                        else:
                            if d < 1e-6:
                                dx, dy, d = 1.0, 0.0, 1.0
                            p.x += dx / d * (c.cr + p.r - d)
                            p.y += dy / d * (c.cr + p.r - d)
                        break
            if not pl.car and not pl.dead:
                for (x, y) in c.circles():
                    dx, dy = pl.x - x, pl.y - y
                    d = math.hypot(dx, dy)
                    if d < c.cr + pl.r:
                        if sp > 60 and c.ai != 'player':
                            self.hurt_player(sp * 0.10 * dt * 6)
                        if d < 1e-6:
                            dx, dy, d = 1.0, 0.0, 1.0
                        pl.x += dx / d * (c.cr + pl.r - d)
                        pl.y += dy / d * (c.cr + pl.r - d)
                        break

    # ------------------------------------------------------------ balles
    def update_bullets(self, dt):
        alive = []
        pl = self.player
        for b in self.bullets:
            dead = False
            for _ in range(2):
                b.x += b.vx * dt / 2
                b.y += b.vy * dt / 2
                t = tile_at(int(b.x // TILE), int(b.y // TILE))
                if t == T_BUILD:
                    dead = True
                    if b.kind == 'rocket':
                        self.explode(b.x, b.y, 130, 170, b.owner)
                    elif b.kind == 'bullet':
                        for _k in range(2):
                            self.spawn_particle('spark', b.x, b.y)
                    break
                if self.bullet_hit(b, pl):
                    dead = True
                    break
            b.life -= dt
            if b.kind == 'rocket':
                if random.random() < 0.8:
                    self.spawn_particle('smoke', b.x, b.y)
                if random.random() < 0.6:
                    self.spawn_particle('fire', b.x, b.y)
            if b.life <= 0 and not dead:
                dead = True
                if b.kind == 'rocket':
                    self.explode(b.x, b.y, 130, 170, b.owner)
            if not dead:
                alive.append(b)
        self.bullets = alive

    def bullet_hit(self, b, pl):
        if b.owner == 'player':
            for p in self.ped_grid.near(b.x, b.y, 20):
                if p.alive and (p.x - b.x) ** 2 + (p.y - b.y) ** 2 < (p.r + 3) ** 2:
                    if b.kind == 'rocket':
                        self.explode(b.x, b.y, 130, 170, b.owner)
                    else:
                        n = math.hypot(b.vx, b.vy) + 1e-6
                        self.hurt_ped(p, b.dmg, 'player', b.vx / n, b.vy / n)
                    return True
        else:
            if not pl.car and not pl.dead and (pl.x - b.x) ** 2 + (pl.y - b.y) ** 2 < (pl.r + 3) ** 2:
                self.hurt_player(b.dmg)
                for _ in range(2):
                    self.spawn_particle('blood', b.x, b.y)
                return True
        for c in self.car_grid.near(b.x, b.y, 70):
            if c.state == 'wreck':
                continue
            for (x, y) in c.circles():
                if (x - b.x) ** 2 + (y - b.y) ** 2 < c.cr * c.cr:
                    if b.kind == 'rocket':
                        self.explode(b.x, b.y, 130, 170, b.owner)
                    else:
                        mul = 1.5 if b.kind == 'flame' else 0.6
                        self.damage_car(c, b.dmg * mul, b.owner)
                        self.spawn_particle('spark', b.x, b.y)
                    return True
        return False

    def update_particles(self, dt):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                if p.kind == 'blood' and random.random() < 0.4:
                    self.decals.append(('blood', p.x, p.y, random.randint(2, 4)))
                continue
            p.x += p.vx * dt
            p.y += p.vy * dt
            if p.kind in ('smoke', 'fire'):
                p.vx *= 0.97
                p.vy *= 0.97
            else:
                p.vx *= 0.93
                p.vy *= 0.93
            alive.append(p)
        if len(alive) > 700:
            alive = alive[-700:]
        self.particles = alive
        ex = []
        for e in self.explosions:
            e.t += dt
            if e.t < e.dur:
                ex.append(e)
        self.explosions = ex

    # ------------------------------------------------------------ pickups
    def update_pickups(self, dt):
        p = self.player
        for pk in self.pickups:
            if not pk.active:
                pk.t -= dt
                if pk.t <= 0:
                    pk.active = True
                continue
            if p.car or p.dead:
                continue
            if (p.x - pk.x) ** 2 + (p.y - pk.y) ** 2 < 26 * 26:
                if pk.kind == 'weapon':
                    w = WEAPONS[pk.val]
                    had = p.ammo.get(pk.val, 0) > 0
                    p.ammo[pk.val] = min(w['ammo_max'], p.ammo.get(pk.val, 0) + w['pack'])
                    if not had:
                        p.weapon = pk.val
                        self.add_msg('Nouvelle arme : ' + w['name'])
                    else:
                        self.add_msg('Munitions : ' + w['name'])
                elif pk.kind == 'health':
                    if p.hp >= 100:
                        continue
                    p.hp = min(100.0, p.hp + pk.val)
                    self.add_msg('Soin +' + str(pk.val))
                else:
                    if p.armor >= 100:
                        continue
                    p.armor = min(100.0, p.armor + pk.val)
                    self.add_msg('Gilet pare-balles')
                pk.active = False
                pk.t = 45.0

    # ------------------------------------------------------------ population / police
    def manage_population(self, dt):
        self.heat = max(0.0, self.heat - 0.07 * dt)
        th = [1.0, 3.0, 6.0, 10.0, 15.0]
        new_stars = sum(1 for v in th if self.heat >= v)
        if new_stars > self.stars:
            self.add_msg('Recherche : ' + '*' * new_stars)
        if new_stars == 0 and self.stars > 0:
            self.add_msg('La police a perdu ta trace')
            for c in self.cars:
                if c.ai == 'police' and c.state == 'ok':
                    self.become_traffic(c)
        self.stars = new_stars
        self.spawn_t -= dt
        if self.spawn_t > 0:
            return
        self.spawn_t = 0.3
        cx, cy = self.camx, self.camy
        self.peds = [p for p in self.peds if p.alive and
                     (math.hypot(p.x - cx, p.y - cy) < 2300 or (p.kind == 'cop' and self.stars > 0 and
                                                                 math.hypot(p.x - cx, p.y - cy) < 3000))]
        keep = []
        for c in self.cars:
            far = math.hypot(c.x - cx, c.y - cy) > 2300
            if far and c.ai in ('traffic', 'police'):
                continue
            keep.append(c)
        self.cars = keep
        wrecks = [c for c in self.cars if c.state == 'wreck']
        if len(wrecks) > 10:
            for c in wrecks[:len(wrecks) - 10]:
                if self.offscreen(c.x, c.y, 1000):
                    self.cars.remove(c)
        civs = sum(1 for p in self.peds if p.kind == 'civ')
        if civs < 55:
            self.spawn_ped_random(far=True)
        traffic = sum(1 for c in self.cars if c.ai == 'traffic')
        if traffic < 20:
            self.spawn_traffic(far=True)
        want_cars = [0, 1, 2, 2, 3, 4][self.stars]
        want_cops = [0, 0, 1, 2, 3, 4][self.stars]
        pc = sum(1 for c in self.cars if c.ai == 'police')
        if pc < want_cars:
            self.spawn_traffic(far=True, police=True)
        cc = sum(1 for p in self.peds if p.kind == 'cop')
        if cc < want_cops and not self.player.dead:
            for _ in range(10):
                a = random.uniform(0, 6.283)
                dist = random.uniform(750, 1100)
                x = cx + math.cos(a) * dist
                y = cy + math.sin(a) * dist
                tx, ty = int(x // TILE), int(y // TILE)
                if tile_at(tx, ty) in (T_SIDE, T_GRASS):
                    self.peds.append(Ped(x, y, 'cop'))
                    break

    # ------------------------------------------------------------ boucle
    def update_player(self, dt, controls):
        p = self.player
        p.cd = max(0.0, p.cd - dt)
        p.flash = max(0.0, p.flash - dt)
        p.hurt = max(0.0, p.hurt - dt)
        p.punch = max(0.0, p.punch - dt)
        if p.dead:
            p.dead_t += dt
            if p.dead_t > 3.2 and controls:
                self.respawn()
            return
        if not controls:
            return
        keys = pygame.key.get_pressed()
        up = kd(keys, pygame.K_UP, pygame.K_z, pygame.K_w)
        dn = kd(keys, pygame.K_DOWN, pygame.K_s)
        lf = kd(keys, pygame.K_LEFT, pygame.K_q, pygame.K_a)
        rt = kd(keys, pygame.K_RIGHT, pygame.K_d)
        if p.car:
            c = p.car
            c.throttle = (1.0 if up else 0.0) - (1.0 if dn else 0.0)
            c.steer = (1.0 if rt else 0.0) - (1.0 if lf else 0.0)
            c.hb = kd(keys, pygame.K_SPACE)
            p.x, p.y = c.x, c.y
            p.angle = c.a
            return
        mxw, myw = self.mouse_world()
        p.angle = math.atan2(myw - p.y, mxw - p.x)
        mx = (1 if rt else 0) - (1 if lf else 0)
        my = (1 if dn else 0) - (1 if up else 0)
        p.moving = False
        if mx or my:
            l = math.hypot(mx, my)
            sp = 235.0 if kd(keys, pygame.K_LSHIFT, pygame.K_RSHIFT) else 150.0
            move_entity(p, mx / l * sp, my / l * sp, dt)
            p.anim += sp * dt * 0.07
            p.moving = True
        fire = bool(pygame.mouse.get_pressed()[0]) or kd(keys, pygame.K_LCTRL, pygame.K_RCTRL)
        w = WEAPONS[p.weapon]
        if fire and (w.get('auto') or not p.fire_prev):
            self.player_fire()
        p.fire_prev = fire

    def update(self, dt, controls=True):
        self.frame += 1
        self.t += dt
        self.ped_grid.clear()
        for p in self.peds:
            if p.alive:
                self.ped_grid.add(p)
        self.update_player(dt, controls)
        self.update_bfs()
        self.update_cars(dt)
        self.car_collisions(dt)
        for p in self.peds:
            if p.alive:
                p.update(dt, self)
        self.cars_vs_people(dt)
        self.update_bullets(dt)
        self.update_particles(dt)
        self.update_pickups(dt)
        self.manage_population(dt)
        self.noises = []
        for m in self.msgs:
            m[1] -= dt
        self.msgs = [m for m in self.msgs if m[1] > 0]
        self.shake = max(0.0, self.shake - dt * 30)
        # camera + zoom
        p = self.player
        if p.car:
            c = p.car
            tx = c.x + c.vx * 0.35
            ty = c.y + c.vy * 0.35
            tz = 1.0 - clamp(c.speed() / 650.0, 0.0, 1.0) * 0.32
        else:
            tx, ty = p.x, p.y
            tz = 1.0
        if controls:
            k = min(1.0, 6.0 * dt)
            self.camx += (tx - self.camx) * k
            self.camy += (ty - self.camy) * k
            self.zoom += (tz - self.zoom) * min(1.0, 2.5 * dt)

    # ------------------------------------------------------------ dessin
    def draw_world(self, surf, ox, oy, vw, vh):
        vcx, vcy = vw / 2.0, vh / 2.0
        surf.fill((14, 14, 18))
        # sol
        tx0 = max(0, ox // TILE)
        ty0 = max(0, oy // TILE)
        tx1 = min(N - 1, (ox + vw) // TILE)
        ty1 = min(N - 1, (oy + vh) // TILE)
        for ty in range(ty0, ty1 + 1):
            row = tiles[ty]
            for tx in range(tx0, tx1 + 1):
                t = row[tx]
                if t == T_ROAD:
                    img = road_tile(tx, ty)
                elif t == T_SIDE:
                    img = SIDE_TILES[(tx + ty) & 1]
                elif t == T_GRASS or t == T_TREE:
                    img = GRASS_TILES[(tx * 7 + ty * 3) % 4]
                else:
                    img = GROUND_TILE
                surf.blit(img, (tx * TILE - ox, ty * TILE - oy))

        def vis(x, y, m):
            return -m < x - ox < vw + m and -m < y - oy < vh + m

        # traces de pneus
        for (x1, y1, x2, y2) in self.skids:
            if vis(x1, y1, 20):
                pygame.draw.line(surf, (38, 38, 42), (x1 - ox, y1 - oy), (x2 - ox, y2 - oy), 3)
        # decals (sang, cadavres)
        for d in self.decals:
            if not vis(d[1], d[2], 40):
                continue
            x, y = d[1] - ox, d[2] - oy
            if d[0] == 'blood':
                pygame.draw.circle(surf, (120, 14, 14), (int(x), int(y)), d[3])
                pygame.draw.circle(surf, (160, 20, 20), (int(x), int(y)), max(1, d[3] // 2))
            else:
                a = d[3]
                fx, fy = math.cos(a), math.sin(a)
                pygame.draw.line(surf, d[5], (x - fx * 7, y - fy * 7), (x + fx * 4, y + fy * 4), 5)
                pygame.draw.line(surf, d[4], (x - fy * 6, y + fx * 6), (x + fy * 6, y - fx * 6), 6)
                pygame.draw.circle(surf, (200, 160, 130), (int(x + fx * 8), int(y + fy * 8)), 4)
        # pickups
        for i, pk in enumerate(self.pickups):
            if not pk.active or not vis(pk.x, pk.y, 30):
                continue
            x = pk.x - ox
            y = pk.y - oy + math.sin(self.t * 4 + i) * 3
            if pk.kind == 'weapon':
                col, ch = (240, 200, 40), WEAPONS[pk.val]['letter']
            elif pk.kind == 'health':
                col, ch = (220, 40, 50), '+'
            else:
                col, ch = (60, 120, 230), 'A'
            alpha_circle(surf, (0, 0, 0), 80, 13, (x + 2, y + 5))
            pygame.draw.circle(surf, (255, 255, 255), (int(x), int(y)), 12)
            pygame.draw.circle(surf, col, (int(x), int(y)), 10)
            img = FONTS['s'].render(ch, True, (20, 20, 20))
            surf.blit(img, img.get_rect(center=(int(x), int(y))))
        # voitures
        vcars = [c for c in self.cars if vis(c.x, c.y, 90)]
        for c in vcars:
            for (x, y) in c.circles():
                alpha_circle(surf, (0, 0, 0), 70, c.cr + 2, (x - ox + 4, y - oy + 5))
        for c in vcars:
            if c.state == 'wreck':
                self.draw_car(surf, c, ox, oy, vcx, vcy)
        for c in vcars:
            if c.state != 'wreck':
                self.draw_car(surf, c, ox, oy, vcx, vcy)
        # pietons
        for p in self.peds:
            if p.alive and vis(p.x, p.y, 30):
                self.draw_person(surf, p, ox, oy, p.kind == 'cop' and self.stars > 0, False)
        pl = self.player
        if not pl.car and not pl.dead:
            self.draw_person(surf, pl, ox, oy, pl.weapon != 0, pl.flash > 0)
        # immeubles et arbres (tries du plus loin au plus proche)
        items = []
        for b in buildings:
            k = b.ht * K3D
            l, t = b.x - ox, b.y - oy
            r, bt = l + b.w, t + b.h
            xs = (l, r, l + (l - vcx) * k, r + (r - vcx) * k)
            ys = (t, bt, t + (t - vcy) * k, bt + (bt - vcy) * k)
            if max(xs) < 0 or min(xs) > vw or max(ys) < 0 or min(ys) > vh:
                continue
            cx, cy = l + b.w / 2 - vcx, t + b.h / 2 - vcy
            items.append((cx * cx + cy * cy, 0, b))
        for (tx, ty) in tree_list:
            if vis(tx, ty, 40):
                cx, cy = tx - ox - vcx, ty - oy - vcy
                items.append((cx * cx + cy * cy, 1, (tx, ty)))
        items.sort(key=lambda it: -it[0])
        for _, kind, o in items:
            if kind == 0:
                self.draw_building(surf, o, ox, oy, vcx, vcy)
            else:
                self.draw_tree(surf, o, ox, oy, vcx, vcy)
        # balles
        for b in self.bullets:
            if not vis(b.x, b.y, 30):
                continue
            x, y = b.x - ox, b.y - oy
            if b.kind == 'bullet':
                n = math.hypot(b.vx, b.vy) + 1e-6
                pygame.draw.line(surf, (255, 240, 150), (x, y), (x - b.vx / n * 14, y - b.vy / n * 14), 2)
            elif b.kind == 'rocket':
                pygame.draw.circle(surf, (200, 200, 200), (int(x), int(y)), 4)
                pygame.draw.circle(surf, (255, 150, 30), (int(x), int(y)), 2)
            else:
                f = b.life / b.max
                col = (255, int(80 + 150 * f), 20)
                pygame.draw.circle(surf, col, (int(x), int(y)), int(4 + 8 * (1 - f)))
        # particules
        for p in self.particles:
            if not vis(p.x, p.y, 30):
                continue
            x, y = p.x - ox, p.y - oy
            f = p.life / p.max
            if p.kind == 'smoke':
                alpha_circle(surf, p.color, 150 * f, p.size + p.grow * (1 - f), (x, y))
            elif p.kind == 'fire':
                pygame.draw.circle(surf, p.color, (int(x), int(y)), max(1, int(p.size * f)))
            elif p.kind == 'spark':
                pygame.draw.line(surf, p.color, (x, y), (x - p.vx * 0.03, y - p.vy * 0.03), 2)
            elif p.kind == 'blood':
                pygame.draw.circle(surf, p.color, (int(x), int(y)), 2)
            else:
                pygame.draw.rect(surf, p.color, (int(x), int(y), 3, 3))
        for e in self.explosions:
            if not vis(e.x, e.y, e.r * 2):
                continue
            k = e.t / e.dur
            rad = e.r * (0.35 + 0.8 * k)
            x, y = e.x - ox, e.y - oy
            alpha_circle(surf, (255, 120, 20), 230 * (1 - k), rad, (x, y))
            alpha_circle(surf, (255, 220, 100), 240 * (1 - k), rad * 0.62, (x, y))
            alpha_circle(surf, (255, 255, 230), 240 * (1 - k) * (1 - k), rad * 0.3, (x, y))

    def draw_car(self, surf, c, ox, oy, vcx, vcy):
        if c.state != 'ok':
            variant, col = 'burnt', (0, 0, 0)
        elif c.kind == 'police':
            variant, col = int(self.t * 6) % 2, c.color
        else:
            variant, col = 0, c.color
        body, roof = car_sprites(c.kind, col, variant)
        ang = -math.degrees(c.a)
        b = pygame.transform.rotate(body, ang)
        r = pygame.transform.rotate(roof, ang)
        sx, sy = c.x - ox, c.y - oy
        surf.blit(b, b.get_rect(center=(int(sx), int(sy))))
        rx = sx + (sx - vcx) * 0.03
        ry = sy + (sy - vcy) * 0.03 - 2
        surf.blit(r, r.get_rect(center=(int(rx), int(ry))))

    def draw_person(self, surf, p, ox, oy, armed, flash):
        x, y = p.x - ox, p.y - oy
        a = p.angle
        fx, fy = math.cos(a), math.sin(a)
        rx, ry = -fy, fx
        sw = math.sin(p.anim) * 5 if p.moving else 0.0
        alpha_circle(surf, (0, 0, 0), 70, 9, (x + 3, y + 4))
        pygame.draw.circle(surf, p.pants, (int(x + fx * sw - rx * 3), int(y + fy * sw - ry * 3)), 3)
        pygame.draw.circle(surf, p.pants, (int(x - fx * sw + rx * 3), int(y - fy * sw + ry * 3)), 3)
        pygame.draw.line(surf, p.shirt, (int(x - rx * 6), int(y - ry * 6)), (int(x + rx * 6), int(y + ry * 6)), 7)
        if armed:
            gl = 14
            if hasattr(p, 'weapon') and p.weapon in (3, 4):
                gl = 20
            ex, ey = x + fx * gl, y + fy * gl
            pygame.draw.line(surf, (30, 30, 30), (x + rx * 4, y + ry * 4), (ex + rx * 4, ey + ry * 4), 3)
            if flash:
                pygame.draw.circle(surf, (255, 230, 100), (int(ex + rx * 4 + fx * 3), int(ey + ry * 4 + fy * 3)), 6)
        elif hasattr(p, 'punch') and p.punch > 0:
            pygame.draw.circle(surf, p.skin, (int(x + fx * 14), int(y + fy * 14)), 4)
        pygame.draw.circle(surf, p.skin, (int(x), int(y)), 5)
        pygame.draw.circle(surf, p.hair, (int(x - fx * 1.5), int(y - fy * 1.5)), 4)

    def draw_tree(self, surf, o, ox, oy, vcx, vcy):
        x, y = o[0] - ox, o[1] - oy
        alpha_circle(surf, (0, 0, 0), 80, 22, (x + 5, y + 7))
        pygame.draw.circle(surf, (90, 60, 30), (int(x), int(y)), 4)
        k = 0.05
        tx, ty = x + (x - vcx) * k, y + (y - vcy) * k
        pygame.draw.circle(surf, (28, 85, 38), (int(tx), int(ty)), 24)
        pygame.draw.circle(surf, (40, 115, 50), (int(tx - 4), int(ty - 4)), 17)
        pygame.draw.circle(surf, (60, 140, 65), (int(tx - 7), int(ty - 7)), 8)

    def draw_building(self, surf, b, ox, oy, vcx, vcy):
        k = b.ht * K3D
        l, t = b.x - ox, b.y - oy
        r, bt = l + b.w, t + b.h

        def pr(px, py):
            return (px + (px - vcx) * k, py + (py - vcy) * k)

        A, B, C, D = (l, t), (r, t), (r, bt), (l, bt)
        A2, B2, C2, D2 = pr(*A), pr(*B), pr(*C), pr(*D)
        faces = []
        if vcy < t:
            faces.append((A, B, A2, B2, 0, b.w, 0.88))
        if vcy > bt:
            faces.append((D, C, D2, C2, 1, b.w, 0.62))
        if vcx < l:
            faces.append((A, D, A2, D2, 2, b.h, 0.74))
        if vcx > r:
            faces.append((B, C, B2, C2, 3, b.h, 0.98))
        for (p, q, p2, q2, fid, length, sh) in faces:
            col = tuple(int(c * sh) for c in b.wall)
            pygame.draw.polygon(surf, col, [p, q, q2, p2])
            nu = max(1, int(length // 34))
            nv = max(1, int(b.ht // 38))
            for j in range(nv):
                v0 = (j + 0.28) / nv
                v1 = (j + 0.72) / nv
                for i in range(nu):
                    u0 = (i + 0.2) / nu
                    u1 = (i + 0.8) / nu
                    hs = (b.id * 7919 + fid * 104729 + i * 31 + j * 17) % 7
                    wc = (250, 225, 120) if hs == 0 else ((38, 52, 72) if hs < 5 else (58, 78, 98))
                    wc = tuple(int(c * (0.6 + 0.4 * sh)) for c in wc)
                    pts = []
                    for (u, v) in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
                        bx = p[0] + (q[0] - p[0]) * u
                        by = p[1] + (q[1] - p[1]) * u
                        rx_ = p2[0] + (q2[0] - p2[0]) * u
                        ry_ = p2[1] + (q2[1] - p2[1]) * u
                        pts.append((bx + (rx_ - bx) * v, by + (ry_ - by) * v))
                    pygame.draw.polygon(surf, wc, pts)
            pygame.draw.line(surf, tuple(int(c * 0.5) for c in b.wall), p2, q2, 2)
        rl, rt = int(A2[0]), int(A2[1])
        rw, rh = int(B2[0] - A2[0]), int(D2[1] - A2[1])
        pygame.draw.rect(surf, b.roof, (rl, rt, rw, rh))
        pygame.draw.rect(surf, tuple(int(c * 0.6) for c in b.roof), (rl, rt, rw, rh), 3)
        if rw > 24 and rh > 24:
            pygame.draw.rect(surf, tuple(min(255, int(c * 1.12) + 6) for c in b.roof),
                             (rl + 8, rt + 8, rw - 16, rh - 16))
            ax = rl + 14 + int((rw - 50) * b.ac[0])
            ay = rt + 14 + int((rh - 50) * b.ac[1])
            pygame.draw.rect(surf, (120, 122, 128), (ax, ay, 22, 18))
            pygame.draw.rect(surf, (80, 82, 88), (ax, ay, 22, 18), 2)

    # ------------------------------------------------------------ HUD
    def draw_hud(self, surf):
        p = self.player
        # radar
        RS = 170
        x0, y0 = 12, H - RS - 12
        rad = pygame.Surface((RS, RS))
        rad.fill((10, 10, 14))
        px, py = self.player_pos()
        sc = 4.0 / TILE
        rad.blit(MINIMAP, (RS // 2 - int(px * sc), RS // 2 - int(py * sc)))
        blink = int(self.t * 4) % 2
        for c in self.cars:
            if c.ai == 'police':
                dx, dy = (c.x - px) * sc + RS / 2, (c.y - py) * sc + RS / 2
                if 0 < dx < RS and 0 < dy < RS:
                    pygame.draw.circle(rad, (60, 100, 255) if blink else (255, 50, 50), (int(dx), int(dy)), 4)
        for pk in self.pickups:
            if pk.active:
                dx, dy = (pk.x - px) * sc + RS / 2, (pk.y - py) * sc + RS / 2
                if 0 < dx < RS and 0 < dy < RS:
                    pygame.draw.circle(rad, (255, 230, 60), (int(dx), int(dy)), 2)
        a = p.car.a if p.car else p.angle
        pts = []
        for (ux, uy) in ((7, 0), (-5, -5), (-5, 5)):
            pts.append((RS / 2 + ux * math.cos(a) - uy * math.sin(a), RS / 2 + ux * math.sin(a) + uy * math.cos(a)))
        pygame.draw.polygon(rad, (255, 255, 255), pts)
        surf.blit(rad, (x0, y0))
        pygame.draw.rect(surf, (230, 230, 230), (x0, y0, RS, RS), 2)
        # barres
        bx = x0 + RS + 14
        by = H - 44
        pygame.draw.rect(surf, (0, 0, 0), (bx - 2, by - 2, 204, 20))
        pygame.draw.rect(surf, (200, 30, 30), (bx, by, int(200 * clamp(p.hp, 0, 100) / 100), 16))
        draw_text(surf, 'SANTE', 's', (255, 255, 255), (bx + 6, by), shadow=False)
        if p.armor > 0:
            pygame.draw.rect(surf, (0, 0, 0), (bx - 2, by - 26, 204, 20))
            pygame.draw.rect(surf, (60, 120, 230), (bx, by - 24, int(200 * p.armor / 100), 16))
            draw_text(surf, 'GILET', 's', (255, 255, 255), (bx + 6, by - 24), shadow=False)
        if p.car:
            c = p.car
            ratio = clamp(c.hp / float(c.sp['hp']), 0, 1)
            pygame.draw.rect(surf, (0, 0, 0), (bx - 2, by - 54, 204, 20))
            pygame.draw.rect(surf, (230, 150, 30), (bx, by - 52, int(200 * ratio), 16))
            draw_text(surf, 'VOITURE', 's', (255, 255, 255), (bx + 6, by - 52), shadow=False)
            draw_text(surf, '%d km/h' % int(c.speed() * 0.3), 'm', (255, 255, 255), (W // 2, H - 40), center=True)
        # arme
        w = WEAPONS[p.weapon]
        if not p.car:
            txt = w['name'] if p.weapon == 0 else '%s  %d' % (w['name'], p.ammo.get(p.weapon, 0))
            img = FONTS['m'].render(txt, True, (255, 230, 120))
            sh = FONTS['m'].render(txt, True, (0, 0, 0))
            surf.blit(sh, (W - 18 - img.get_width(), H - 38))
            surf.blit(img, (W - 20 - img.get_width(), H - 40))
        # score
        draw_text(surf, 'SCORE %d' % self.score, 'm', (255, 255, 255), (16, 12))
        draw_text(surf, 'Victimes : %d' % self.kills, 's', (230, 230, 230), (16, 44))
        # etoiles
        for i in range(5):
            cx = W - 30 - i * 34
            if i < self.stars:
                col = (255, 210, 40) if (self.t * 4) % 2 < 1.4 else (255, 120, 20)
                pygame.draw.polygon(surf, col, star_pts(cx, 30, 14))
            else:
                pygame.draw.polygon(surf, (70, 70, 70), star_pts(cx, 30, 14), 2)
        # messages
        for i, m in enumerate(self.msgs):
            draw_text(surf, m[0], 'm', (255, 255, 255), (W // 2, 80 + i * 30), center=True)
        # degats
        if p.hurt > 0:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 0, 0, int(110 * p.hurt / 0.25)))
            surf.blit(ov, (0, 0))
        if p.dead:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 130))
            surf.blit(ov, (0, 0))
            draw_text(surf, 'MORT', 'xl', (200, 20, 20), (W // 2, H // 2 - 20), center=True)
            draw_text(surf, 'Retour a la vie...', 'm', (255, 255, 255), (W // 2, H // 2 + 90), center=True)
        if self.show_map:
            self.draw_bigmap(surf)

    def draw_bigmap(self, surf):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 190))
        surf.blit(ov, (0, 0))
        S = BIGMAP.get_width()
        x0, y0 = (W - S) // 2, (H - S) // 2
        surf.blit(BIGMAP, (x0, y0))
        pygame.draw.rect(surf, (255, 255, 255), (x0, y0, S, S), 3)
        k = S / float(WORLD)
        for pk in self.pickups:
            if pk.active:
                pygame.draw.circle(surf, (255, 230, 60), (int(x0 + pk.x * k), int(y0 + pk.y * k)), 3)
        blink = int(self.t * 4) % 2
        for c in self.cars:
            if c.ai == 'police':
                pygame.draw.circle(surf, (60, 100, 255) if blink else (255, 50, 50),
                                   (int(x0 + c.x * k), int(y0 + c.y * k)), 5)
        px, py = self.player_pos()
        pygame.draw.circle(surf, (255, 255, 255), (int(x0 + px * k), int(y0 + py * k)), 7)
        pygame.draw.circle(surf, (230, 30, 30), (int(x0 + px * k), int(y0 + py * k)), 4)
        draw_text(surf, 'CARTE DE LA VILLE  (M pour fermer)   Rouge = toi   Jaune = objets   Bleu/rouge = police',
                  's', (255, 255, 255), (W // 2, 14), center=True)

    def draw(self, screen):
        z = self.zoom
        shx = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0.0
        shy = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0.0
        if abs(z - 1.0) < 0.003:
            vw, vh = W, H
            view = screen
        else:
            vw, vh = int(W / z), int(H / z)
            view = pygame.Surface((vw, vh))
        ox = int(self.camx - vw / 2.0 + shx)
        oy = int(self.camy - vh / 2.0 + shy)
        self.ox, self.oy, self.vw, self.vh = ox, oy, vw, vh
        self.draw_world(view, ox, oy, vw, vh)
        if view is not screen:
            pygame.transform.scale(view, (W, H), screen)
        self.draw_hud(screen)


# --------------------------------------------------------------------------
#  ECRAN TITRE
# --------------------------------------------------------------------------
def draw_title(screen, game, t):
    game.draw_world(screen, int(game.camx - W / 2), int(game.camy - H / 2), W, H)
    game.ox, game.oy, game.vw, game.vh = int(game.camx - W / 2), int(game.camy - H / 2), W, H
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 150))
    screen.blit(ov, (0, 0))
    wob = math.sin(t * 2) * 4
    draw_text(screen, 'CK 1', 'xl', (255, 205, 30), (W // 2 + 4, 140 + wob + 4), center=True, shadow=False)
    draw_text(screen, 'CK 1', 'xl', (220, 40, 40), (W // 2, 140 + wob), center=True)
    draw_text(screen, "Ville ouverte  -  Voitures  -  Armes  -  Police  -  Aucune mission", 'm',
              (255, 255, 255), (W // 2, 250), center=True)
    lines = [
        "ZQSD / WASD / Fleches : se deplacer / conduire   (Maj = courir)",
        "Souris : viser      Clic gauche ou CTRL : tirer",
        "E : monter / descendre d'une voiture      Espace : frein a main",
        "1-6 / molette / TAB : changer d'arme      M : carte      ESC : pause",
    ]
    for i, l in enumerate(lines):
        draw_text(screen, l, 's', (230, 230, 230), (W // 2, 330 + i * 30), center=True)
    if int(t * 2) % 2 == 0:
        draw_text(screen, 'Appuie sur ENTREE pour jouer', 'l', (255, 255, 255), (W // 2, 530), center=True)


# --------------------------------------------------------------------------
#  PROGRAMME PRINCIPAL
# --------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption('CK 1')
    clock = pygame.time.Clock()
    build_city()
    init_assets()
    make_minimaps()
    game = Game()
    state = 'title'
    title_t = 0.0
    digit_map = {'&': 0, 'é': 1, '"': 2, "'": 3, '(': 4, '-': 5,
                 '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5}
    wheel = getattr(pygame, 'MOUSEWHEEL', None)
    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if state == 'title':
                    if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        state = 'play'
                        game.camx, game.camy = game.player.x, game.player.y
                        game.zoom = 1.0
                    elif e.key == pygame.K_ESCAPE:
                        running = False
                elif state == 'play':
                    if e.key == pygame.K_ESCAPE or e.key == pygame.K_p:
                        state = 'pause'
                    elif e.key in (pygame.K_e, pygame.K_f, pygame.K_RETURN):
                        game.toggle_car()
                    elif e.key == pygame.K_m:
                        game.show_map = not game.show_map
                    elif e.key == pygame.K_TAB:
                        game.cycle_weapon(1)
                    else:
                        ch = getattr(e, 'unicode', '')
                        if ch in digit_map:
                            game.select_weapon(digit_map[ch])
                elif state == 'pause':
                    if e.key in (pygame.K_ESCAPE, pygame.K_p):
                        state = 'play'
                    elif e.key == pygame.K_q:
                        running = False
            elif wheel is not None and e.type == wheel and state == 'play':
                game.cycle_weapon(-1 if e.y > 0 else 1)

        if state == 'title':
            title_t += dt
            game.update(dt, controls=False)
            game.camx = 2144 + math.sin(title_t * 0.15) * 600
            game.camy = 2144 + title_t * 25 % 1200 - 600
            draw_title(screen, game, title_t)
        elif state == 'play':
            game.update(dt, controls=True)
            game.draw(screen)
        else:
            game.draw(screen)
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 150))
            screen.blit(ov, (0, 0))
            draw_text(screen, 'PAUSE', 'l', (255, 255, 255), (W // 2, H // 2 - 30), center=True)
            draw_text(screen, 'ESC : reprendre      Q : quitter', 'm', (230, 230, 230), (W // 2, H // 2 + 30), center=True)
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
