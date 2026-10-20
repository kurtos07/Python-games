#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3D SHOOTER - jeu de tir à la première personne en Python + pygame
(moteur 3D logiciel : projection perspective, polygones triés, pas d'OpenGL)

Lancer :   pip install pygame      puis      python shooter3d.py
"""
import math
import random
import sys
from itertools import chain
from operator import itemgetter

import pygame

# ----------------------------------------------------------------------------
# CONSTANTES
# ----------------------------------------------------------------------------
W, H = 1000, 620
FOV = 75.0
NEAR = 0.1
STEP_H = 0.6          # hauteur max qu'on peut "enjamber"
GRAV = 20.0
JUMP_V = 7.2
RADIUS = 0.35
GOAL = 15             # nombre de kills pour gagner
NUM_BOTS = 4
BOT_DMG = 0.6         # les bots font moins de dégâts
CELL = 3.0
FOG = (172, 196, 222)
FOGD = 85.0
_l = math.sqrt(0.45 ** 2 + 0.8 ** 2 + 0.35 ** 2)
LX, LY, LZ = 0.45 / _l, 0.8 / _l, 0.35 / _l

WEAPONS = [
    dict(id="w0", dmg=14, rate=0.085, spread=0.030, mag=30, reload=1.7, auto=True, melee=False, rng=60, fov=62),
    dict(id="w1", dmg=65, rate=0.85, spread=0.003, mag=6, reload=2.3, auto=False, melee=False, rng=90, fov=34),
    dict(id="w2", dmg=55, rate=0.45, spread=0.0, mag=0, reload=0, auto=True, melee=True, rng=2.3, fov=70),
]

# ----------------------------------------------------------------------------
# TRADUCTIONS
# ----------------------------------------------------------------------------
LANGS = ["en", "fr", "es", "de", "ru"]
LANG_NAMES = {"en": "English", "fr": "Français", "es": "Español", "de": "Deutsch", "ru": "Русский"}

TXT = {
    "en": dict(
        title="3D SHOOTER", play="Play", settings="Settings", language="Language", back="Back",
        select_map="Choose a map", map0="Arena", map1="Bunker", map2="Hills", map3="Fortress",
        resume="Resume", quit_menu="Main menu", hp="Health", kills="Kills",
        goal="First to {n} kills wins", reloading="Reloading...", dead="You died",
        respawn="Respawn in {n}", win="VICTORY!", lose="DEFEAT", click="Click to continue",
        w0="Machine gun", w1="Rifle", w2="Knife", you="You", controls="Controls",
        c_move="Move (forward / left / back / right)", c_jump="Jump", c_sprint="Sprint",
        c_crouch="Crouch", c_slide="Slide (while sprinting)", c_lean="Lean left / right",
        c_look="Look around", c_fire="Shoot / stab", c_aim="Aim (zoom)", c_reload="Reload",
        c_weapon="Change weapon", c_pause="Pause / menu"),
    "fr": dict(
        title="TIREUR 3D", play="Jouer", settings="Paramètres", language="Langue", back="Retour",
        select_map="Choisis une carte", map0="Arène", map1="Bunker", map2="Collines", map3="Forteresse",
        resume="Reprendre", quit_menu="Menu principal", hp="Vie", kills="Éliminations",
        goal="Le premier à {n} éliminations gagne", reloading="Rechargement...", dead="Tu es mort",
        respawn="Réapparition dans {n}", win="VICTOIRE !", lose="DÉFAITE", click="Clique pour continuer",
        w0="Mitraillette", w1="Fusil", w2="Couteau", you="Toi", controls="Touches",
        c_move="Se déplacer (avancer / gauche / reculer / droite)", c_jump="Sauter", c_sprint="Courir",
        c_crouch="S'accroupir", c_slide="Glisser (en courant)", c_lean="Pencher à gauche / droite",
        c_look="Regarder autour", c_fire="Tirer / poignarder", c_aim="Viser (zoom)", c_reload="Recharger",
        c_weapon="Changer d'arme", c_pause="Pause / menu"),
    "es": dict(
        title="TIRADOR 3D", play="Jugar", settings="Ajustes", language="Idioma", back="Atrás",
        select_map="Elige un mapa", map0="Arena", map1="Búnker", map2="Colinas", map3="Fortaleza",
        resume="Continuar", quit_menu="Menú principal", hp="Vida", kills="Bajas",
        goal="El primero en {n} bajas gana", reloading="Recargando...", dead="Has muerto",
        respawn="Reaparecer en {n}", win="¡VICTORIA!", lose="DERROTA", click="Haz clic para continuar",
        w0="Ametralladora", w1="Fusil", w2="Cuchillo", you="Tú", controls="Controles",
        c_move="Moverse (adelante / izquierda / atrás / derecha)", c_jump="Saltar", c_sprint="Correr",
        c_crouch="Agacharse", c_slide="Deslizarse (corriendo)", c_lean="Inclinarse izquierda / derecha",
        c_look="Mirar alrededor", c_fire="Disparar / apuñalar", c_aim="Apuntar (zoom)", c_reload="Recargar",
        c_weapon="Cambiar de arma", c_pause="Pausa / menú"),
    "de": dict(
        title="3D-SHOOTER", play="Spielen", settings="Einstellungen", language="Sprache", back="Zurück",
        select_map="Wähle eine Karte", map0="Arena", map1="Bunker", map2="Hügel", map3="Festung",
        resume="Weiter", quit_menu="Hauptmenü", hp="Leben", kills="Abschüsse",
        goal="Wer zuerst {n} Abschüsse hat, gewinnt", reloading="Nachladen...", dead="Du bist gestorben",
        respawn="Wiedereinstieg in {n}", win="SIEG!", lose="NIEDERLAGE", click="Klicke zum Fortfahren",
        w0="Maschinengewehr", w1="Gewehr", w2="Messer", you="Du", controls="Steuerung",
        c_move="Bewegen (vor / links / zurück / rechts)", c_jump="Springen", c_sprint="Rennen",
        c_crouch="Ducken", c_slide="Rutschen (beim Rennen)", c_lean="Nach links / rechts lehnen",
        c_look="Umsehen", c_fire="Schießen / Zustechen", c_aim="Zielen (Zoom)", c_reload="Nachladen",
        c_weapon="Waffe wechseln", c_pause="Pause / Menü"),
    "ru": dict(
        title="3D ШУТЕР", play="Играть", settings="Настройки", language="Язык", back="Назад",
        select_map="Выбери карту", map0="Арена", map1="Бункер", map2="Холмы", map3="Крепость",
        resume="Продолжить", quit_menu="Главное меню", hp="Здоровье", kills="Убийства",
        goal="Побеждает первый, кто набрал {n} убийств", reloading="Перезарядка...", dead="Ты погиб",
        respawn="Возрождение через {n}", win="ПОБЕДА!", lose="ПОРАЖЕНИЕ", click="Нажми, чтобы продолжить",
        w0="Автомат", w1="Винтовка", w2="Нож", you="Ты", controls="Управление",
        c_move="Движение (вперёд / влево / назад / вправо)", c_jump="Прыжок", c_sprint="Бег",
        c_crouch="Присесть", c_slide="Скольжение (при беге)", c_lean="Наклон влево / вправо",
        c_look="Осмотр", c_fire="Стрелять / бить ножом", c_aim="Прицелиться (зум)", c_reload="Перезарядка",
        c_weapon="Сменить оружие", c_pause="Пауза / меню"),
}

KEY_ROWS = [
    ("W/Z  A/Q  S  D", "c_move"), ("SPACE", "c_jump"), ("SHIFT", "c_sprint"),
    ("CTRL / C", "c_crouch"), ("SHIFT + CTRL / C", "c_slide"), ("<  /  >", "c_lean"),
    ("MOUSE", "c_look"), ("LMB", "c_fire"), ("RMB", "c_aim"), ("R", "c_reload"),
    ("1 2 3 / WHEEL", "c_weapon"), ("ESC", "c_pause"),
]


# ----------------------------------------------------------------------------
# MONDE : solides (boîtes, rampes, collines) + faces à dessiner
# ----------------------------------------------------------------------------
def newell(poly):
    nx = ny = nz = 0.0
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    l = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / l, ny / l, nz / l


def dist3(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def subdivide(quad, normal, color, out):
    """Découpe un quad en petites cellules (meilleur tri painter)."""
    a, b, c, d = quad
    nu = max(1, int(math.ceil(max(dist3(a, b), dist3(d, c)) / CELL)))
    nv = max(1, int(math.ceil(max(dist3(a, d), dist3(b, c)) / CELL)))

    def P(u, v):
        return tuple((1 - v) * ((1 - u) * a[k] + u * b[k]) + v * ((1 - u) * d[k] + u * c[k]) for k in range(3))

    for i in range(nu):
        for j in range(nv):
            u0, u1, v0, v1 = i / nu, (i + 1) / nu, j / nv, (j + 1) / nv
            verts = [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)]
            cx = sum(p[0] for p in verts) / 4
            cy = sum(p[1] for p in verts) / 4
            cz = sum(p[2] for p in verts) / 4
            k = 0.92 if (i + j) & 1 else 1.0
            col = (int(color[0] * k), int(color[1] * k), int(color[2] * k))
            out.append((cx, cy, cz, normal[0], normal[1], normal[2], verts, col))


class Solid:
    def __init__(self, kind, x0, z0, x1, z1, h, d, color):
        self.kind, self.x0, self.z0, self.x1, self.z1, self.h, self.d, self.color = kind, x0, z0, x1, z1, h, d, color

    def height(self, x, z):
        if self.kind == "box":
            return self.h
        if self.kind == "ramp":
            d = self.d
            if d == 0:
                t = (x - self.x0) / (self.x1 - self.x0)
            elif d == 1:
                t = (self.x1 - x) / (self.x1 - self.x0)
            elif d == 2:
                t = (z - self.z0) / (self.z1 - self.z0)
            else:
                t = (self.z1 - z) / (self.z1 - self.z0)
            return self.h * t
        cx, cz = (self.x0 + self.x1) / 2, (self.z0 + self.z1) / 2
        rx, rz = (self.x1 - self.x0) / 2, (self.z1 - self.z0) / 2
        t = max(abs(x - cx) / rx, abs(z - cz) / rz)
        return max(0.0, self.h * (1 - t))

    def cells(self):
        x0, z0, x1, z1, h = self.x0, self.z0, self.x1, self.z1, self.h
        cs = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        quads = []
        if self.kind == "box":
            quads.append([(x, h, z) for x, z in cs])
            for i in range(4):
                a, b = cs[i], cs[(i + 1) % 4]
                quads.append([(a[0], 0, a[1]), (b[0], 0, b[1]), (b[0], h, b[1]), (a[0], h, a[1])])
            cy = h / 2
        elif self.kind == "ramp":
            hh = [self.height(x, z) for x, z in cs]
            quads.append([(cs[i][0], hh[i], cs[i][1]) for i in range(4)])
            for i in range(4):
                j = (i + 1) % 4
                if hh[i] < 1e-6 and hh[j] < 1e-6:
                    continue
                a, b = cs[i], cs[j]
                quads.append([(a[0], 0, a[1]), (b[0], 0, b[1]), (b[0], hh[j], b[1]), (a[0], hh[i], a[1])])
            cy = h / 2
        else:  # pyramide / colline
            apex = ((x0 + x1) / 2, h, (z0 + z1) / 2)
            for i in range(4):
                a, b = cs[i], cs[(i + 1) % 4]
                quads.append([(a[0], 0, a[1]), (b[0], 0, b[1]), apex, apex])
            cy = h * 0.3
        center = ((x0 + x1) / 2, cy, (z0 + z1) / 2)
        out = []
        for q in quads:
            n = newell(q)
            fc = (sum(p[0] for p in q) / 4, sum(p[1] for p in q) / 4, sum(p[2] for p in q) / 4)
            if n[0] * (fc[0] - center[0]) + n[1] * (fc[1] - center[1]) + n[2] * (fc[2] - center[2]) < 0:
                n = (-n[0], -n[1], -n[2])
            subdivide(q, n, self.color, out)
        return out


WALL = (150, 140, 130)
CRATE = (160, 120, 70)
CONC = (125, 130, 140)
HILL = (80, 140, 70)
RAMPC = (190, 160, 100)
STONE = (140, 150, 160)


def B(x0, z0, x1, z1, h, c=CONC):
    return ("box", x0, z0, x1, z1, h, 0, c)


def R(x0, z0, x1, z1, h, d, c=RAMPC):
    return ("ramp", x0, z0, x1, z1, h, d, c)


def P(x0, z0, x1, z1, h, c=HILL):
    return ("pyr", x0, z0, x1, z1, h, 0, c)


def outer():
    return [B(-1, -1, 41, 0, 5, WALL), B(-1, 40, 41, 41, 5, WALL), B(-1, 0, 0, 40, 5, WALL), B(40, 0, 41, 40, 5, WALL)]


def map_spec(i):
    s = outer()
    if i == 0:  # Arène
        s += [P(16, 16, 24, 24, 3.5),
              B(8, 8, 10, 10, .9, CRATE), B(30, 8, 32, 10, .9, CRATE), B(8, 30, 10, 32, .9, CRATE),
              B(30, 30, 32, 32, .9, CRATE), B(18, 6, 22, 8, .9, CRATE), B(18, 32, 22, 34, .9, CRATE),
              B(6, 18, 8, 22, .9, CRATE), B(32, 18, 34, 22, .9, CRATE),
              B(12, 12, 14, 13, 2.5), B(26, 12, 28, 13, 2.5), B(12, 27, 14, 28, 2.5), B(26, 27, 28, 28, 2.5),
              B(15, 10, 25, 11, 2.2), B(15, 29, 25, 30, 2.2)]
        sp = [(4, 4), (36, 4), (4, 36), (36, 36), (20, 3), (20, 37)]
    elif i == 1:  # Bunker
        s += [B(10, 0, 11, 15, 3.2), B(10, 21, 11, 40, 3.2), B(29, 0, 30, 19, 3.2), B(29, 25, 30, 40, 3.2),
              B(14, 19, 18, 20, 3.2), B(22, 19, 26, 20, 3.2), B(14, 24, 18, 25, 3.2), B(22, 24, 26, 25, 3.2),
              B(3, 5, 5, 7, .9, CRATE), B(5, 30, 7, 32, .9, CRATE), B(33, 8, 35, 10, .9, CRATE),
              B(34, 30, 36, 32, .9, CRATE), B(18, 28, 22, 31, .9, CRATE), B(18, 9, 22, 12, .9, CRATE),
              B(14, 5, 16, 7, 2.2), B(24, 33, 26, 35, 2.2)]
        sp = [(4, 20), (36, 22), (20, 4), (20, 36), (5, 5), (35, 35)]
    elif i == 2:  # Collines
        s += [P(5, 5, 17, 17, 3), P(23, 5, 35, 17, 2.6), P(5, 23, 17, 35, 2.6), P(23, 23, 35, 35, 3),
              B(17, 17, 23, 23, 1.8, STONE),
              R(23, 17, 28, 23, 1.8, 1), R(12, 17, 17, 23, 1.8, 0), R(17, 23, 23, 28, 1.8, 3), R(17, 12, 23, 17, 1.8, 2),
              B(19, 2, 21, 6, 2.2), B(19, 34, 21, 38, 2.2), B(2, 19, 6, 21, 2.2), B(34, 19, 38, 21, 2.2)]
        sp = [(3, 20), (37, 20), (20, 3), (20, 37), (3, 3), (37, 37)]
    else:  # Forteresse
        s += [B(14, 14, 26, 26, 2.4, STONE),
              R(26, 16, 32, 24, 2.4, 1), R(8, 16, 14, 24, 2.4, 0), R(16, 26, 24, 32, 2.4, 3), R(16, 8, 24, 14, 2.4, 2),
              B(14, 14, 16, 16, 3.4), B(24, 14, 26, 16, 3.4), B(14, 24, 16, 26, 3.4), B(24, 24, 26, 26, 3.4),
              B(4, 4, 8, 5, 2.2), B(32, 4, 36, 5, 2.2), B(4, 35, 8, 36, 2.2), B(32, 35, 36, 36, 2.2),
              B(4, 18, 6, 20, .9, CRATE), B(34, 20, 36, 22, .9, CRATE), B(18, 4, 20, 6, .9, CRATE),
              B(20, 34, 22, 36, .9, CRATE), P(2, 8, 8, 14, 2), P(32, 26, 38, 32, 2)]
        sp = [(4, 10), (36, 10), (4, 30), (36, 30), (20, 3), (20, 37)]
    return dict(solids=s, spawns=sp)


class World:
    def __init__(self, idx):
        spec = map_spec(idx)
        self.idx = idx
        self.solids = [Solid(*t) for t in spec["solids"]]
        self.spawns = spec["spawns"]
        self.cells = []
        for s in self.solids:
            self.cells += s.cells()
        self.floor = []
        for gx in range(0, 40, 5):
            for gz in range(0, 40, 5):
                col = (98, 112, 92) if ((gx + gz) // 5) & 1 else (86, 100, 82)
                v = [(gx, 0, gz), (gx + 5, 0, gz), (gx + 5, 0, gz + 5), (gx, 0, gz + 5)]
                self.floor.append((gx + 2.5, 0, gz + 2.5, v, col))

    def h(self, x, z):
        best = 0.0
        for s in self.solids:
            if s.x0 <= x <= s.x1 and s.z0 <= z <= s.z1:
                v = s.height(x, z)
                if v > best:
                    best = v
        return best

    def ground(self, x, z, r=RADIUS):
        g = self.h(x, z)
        for dx, dz in ((r, 0), (-r, 0), (0, r), (0, -r)):
            v = self.h(x + dx, z + dz)
            if v > g:
                g = v
        return g


# ----------------------------------------------------------------------------
# ENTITÉS (joueur + bots)
# ----------------------------------------------------------------------------
class Ent:
    def __init__(self, name, col, player=False):
        self.name, self.col, self.player = name, col, player
        self.kills = self.deaths = 0
        self.x = self.y = self.z = 0.0
        self.vx = self.vz = self.vy = 0.0
        self.yaw = self.pitch = 0.0
        self.hp = 100
        self.alive = False
        self.respawn = 0.0
        self.wi = 0
        self.ammo = [30, 6, 0]
        self.cd = self.rel = self.recoil = self.swing = self.inv = 0.0
        self.on_ground = True
        self.eye = 1.7
        self.lean = 0.0
        self.slide = 0.0
        self.sdx = self.sdz = 0.0
        self.height = 1.8
        # IA
        self.target = None
        self.think = 0.0
        self.strafe = 0
        self.strafe_t = 0.0
        self.wp = None
        self.wp_t = 0.0
        self.stuck = 0.0


def angdiff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


def clamp(v, a, b):
    return a if v < a else b if v > b else v


# ----------------------------------------------------------------------------
# JEU
# ----------------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("3D SHOOTER")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        names = "dejavusans,arial,freesans,liberationsans,verdana"
        self.f_big = pygame.font.SysFont(names, 76, bold=True)
        self.f_med = pygame.font.SysFont(names, 34, bold=True)
        self.f_txt = pygame.font.SysFont(names, 24)
        self.f_sm = pygame.font.SysFont(names, 19)
        self.lang = "en"
        self.state = "menu"
        self.btns = []
        self.bg = self.make_bg()
        self.world = None
        self.ents = []
        self.paused = False
        self.fire_prev = False
        self.tracers = []
        self.feed = []
        self.flash = 0.0
        self.hitmark = 0.0
        self.bob = 0.0
        self.winner = None
        self.worlds = {}
        self.hw, self.hh = W / 2, H / 2

    # ---------- utilitaires UI ----------
    def tr(self, k, **kw):
        s = TXT[self.lang].get(k, k)
        return s.format(**kw) if kw else s

    def make_bg(self):
        s = pygame.Surface((W, H))
        for y in range(0, H, 4):
            t = y / H
            pygame.draw.rect(s, (int(20 + 30 * t), int(25 + 40 * t), int(50 + 60 * t)), (0, y, W, 4))
        # silhouettes décoratives
        rnd = random.Random(4)
        for i in range(14):
            x = rnd.randint(-40, W)
            w = rnd.randint(60, 140)
            h = rnd.randint(80, 260)
            pygame.draw.rect(s, (18, 22, 34), (x, H - h, w, h))
        return s

    def text(self, s, font, col, pos, center=False, right=False):
        img = font.render(s, True, col)
        r = img.get_rect()
        if center:
            r.center = pos
        elif right:
            r.topright = pos
        else:
            r.topleft = pos
        self.screen.blit(img, r)
        return r

    def button(self, rect, label, cb, font=None):
        rect = pygame.Rect(rect)
        hover = rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, (230, 120, 40) if hover else (45, 60, 95), rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=10)
        self.text(label, font or self.f_med, (255, 255, 255), rect.center, center=True)
        self.btns.append((rect, cb))

    # ---------- états / menus ----------
    def set_state(self, st):
        self.state = st
        if st != "game":
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)

    def draw_main(self):
        self.screen.blit(self.bg, (0, 0))
        self.text(self.tr("title"), self.f_big, (255, 200, 60), (W // 2, 120), center=True)
        bw, bh, x = 380, 70, W // 2 - 190
        self.button((x, 240, bw, bh), self.tr("play"), lambda: self.set_state("maps"))
        self.button((x, 330, bw, bh), self.tr("settings"), lambda: self.set_state("settings"))
        self.button((x, 420, bw, bh), self.tr("language") + "  [" + LANG_NAMES[self.lang] + "]",
                    lambda: self.set_state("lang"))

    def draw_settings(self):
        self.screen.blit(self.bg, (0, 0))
        self.text(self.tr("settings") + " - " + self.tr("controls"), self.f_med, (255, 200, 60), (W // 2, 50), center=True)
        y = 100
        for keys, act in KEY_ROWS:
            pygame.draw.rect(self.screen, (40, 55, 90), (60, y, 880, 36), border_radius=6)
            pygame.draw.rect(self.screen, (230, 230, 240), (70, y + 4, 250, 28), border_radius=5)
            self.text(keys, self.f_sm, (20, 20, 40), (195, y + 18), center=True)
            self.text(self.tr(act), self.f_txt, (255, 255, 255), (340, y + 4))
            y += 41
        self.button((W // 2 - 110, H - 60, 220, 48), self.tr("back"), lambda: self.set_state("menu"), self.f_txt)

    def draw_lang(self):
        self.screen.blit(self.bg, (0, 0))
        self.text(self.tr("language"), self.f_med, (255, 200, 60), (W // 2, 70), center=True)
        for i, l in enumerate(LANGS):
            def cb(l=l):
                self.lang = l
            self.button((W // 2 - 190, 130 + i * 78, 380, 64), LANG_NAMES[l] + ("  ✔" if l == self.lang else ""), cb)
        self.button((W // 2 - 110, H - 60, 220, 48), self.tr("back"), lambda: self.set_state("menu"), self.f_txt)

    def draw_maps(self):
        self.screen.blit(self.bg, (0, 0))
        self.text(self.tr("select_map"), self.f_med, (255, 200, 60), (W // 2, 45), center=True)
        self.text(self.tr("goal", n=GOAL) + "  -  " + str(NUM_BOTS) + " bots", self.f_sm, (210, 220, 240), (W // 2, 85), center=True)
        for i in range(4):
            cx = 70 + (i % 2) * 450
            cy = 115 + (i // 2) * 230
            rect = pygame.Rect(cx, cy, 410, 210)
            hover = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, (230, 120, 40) if hover else (45, 60, 95), rect, border_radius=10)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=10)
            # aperçu vue de dessus
            pv = pygame.Rect(cx + 12, cy + 12, 186, 186)
            pygame.draw.rect(self.screen, (70, 85, 65), pv)
            wspec = map_spec(i)["solids"]
            k = 186 / 40.0
            for kind, x0, z0, x1, z1, h, d, col in wspec[4:]:
                c = col if kind != "box" or col != CONC else (110, 115, 125)
                pygame.draw.rect(self.screen, c, (pv.x + x0 * k, pv.y + z0 * k, (x1 - x0) * k, (z1 - z0) * k))
            self.text(self.tr("map%d" % i), self.f_med, (255, 255, 255), (cx + 215, cy + 70))
            self.text("%d / 4" % (i + 1), self.f_txt, (220, 230, 255), (cx + 215, cy + 120))
            self.btns.append((rect, lambda i=i: self.start_game(i)))
        self.button((W // 2 - 110, H - 56, 220, 44), self.tr("back"), lambda: self.set_state("menu"), self.f_txt)

    # ---------- démarrage partie ----------
    def start_game(self, idx):
        if idx not in self.worlds:
            self.worlds[idx] = World(idx)
        self.world = self.worlds[idx]
        self.player = Ent(self.tr("you"), (60, 120, 220), True)
        cols = [(200, 60, 60), (60, 170, 80), (210, 150, 40), (150, 70, 190), (60, 180, 190)]
        self.ents = [self.player] + [Ent("Bot %d" % (i + 1), cols[i % 5]) for i in range(NUM_BOTS)]
        for e in self.ents:
            e.wi = 0 if e.player else random.choice((0, 0, 1))
            self.spawn(e)
        self.tracers, self.feed = [], []
        self.flash = self.hitmark = 0.0
        self.paused = False
        self.winner = None
        self.fire_prev = False
        self.state = "game"
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)
        pygame.mouse.get_rel()

    def spawn(self, e):
        best = None
        cands = list(self.world.spawns)
        random.shuffle(cands)
        scored = []
        for sx, sz in cands:
            dmin = 999
            for o in self.ents:
                if o is not e and o.alive:
                    dmin = min(dmin, math.hypot(o.x - sx, o.z - sz))
            scored.append((dmin, sx, sz))
        scored.sort(reverse=True)
        _, sx, sz = random.choice(scored[:3])
        e.x, e.z = sx + random.uniform(-.5, .5), sz + random.uniform(-.5, .5)
        e.y = self.world.ground(e.x, e.z)
        e.vx = e.vz = e.vy = 0
        e.yaw = math.atan2(20 - e.x, 20 - e.z)
        e.pitch = 0
        e.hp = 100
        e.alive = True
        e.ammo = [30, 6, 0]
        e.cd = e.rel = e.recoil = e.swing = 0
        e.inv = 1.5
        e.on_ground = True
        e.slide = 0
        e.eye = 1.7 if e.player else 1.55
        e.height = 1.8
        e.target = None
        e.wp = None

    # ---------- physique ----------
    def move_ent(self, e, tvx, tvz, dt, accel=None):
        if accel is None:
            accel = 60.0 if e.on_ground else 7.0
        k = min(1.0, accel * dt)
        e.vx += (tvx - e.vx) * k
        e.vz += (tvz - e.vz) * k
        ox, oz = e.x, e.z
        w = self.world
        nx = e.x + e.vx * dt
        if w.ground(nx, e.z) - e.y <= STEP_H:
            e.x = nx
        else:
            e.vx = 0
        nz = e.z + e.vz * dt
        if w.ground(e.x, nz) - e.y <= STEP_H:
            e.z = nz
        else:
            e.vz = 0
        # vertical
        g = w.ground(e.x, e.z)
        if e.on_ground and e.vy <= 0 and e.y - g < 0.45:
            e.y = g
            e.vy = 0
        else:
            e.vy -= GRAV * dt
            e.y += e.vy * dt
            if e.y <= g:
                e.y = g
                e.vy = 0
        e.on_ground = e.y <= g + 0.02
        return math.hypot(e.x - ox, e.z - oz)

    def eye_pos(self, e):
        c, s = math.cos(e.yaw), math.sin(e.yaw)
        return e.x + c * e.lean * 0.45, e.y + e.eye, e.z - s * e.lean * 0.45

    # ---------- armes ----------
    def try_fire(self, e):
        w = WEAPONS[e.wi]
        if not e.alive or e.cd > 0 or e.rel > 0:
            return False
        mult = BOT_DMG if not e.player else 1.0
        if w["melee"]:
            e.cd = w["rate"]
            e.swing = 0.3
            fx, fz = math.sin(e.yaw), math.cos(e.yaw)
            for t in self.ents:
                if t is e or not t.alive:
                    continue
                dx, dz = t.x - e.x, t.z - e.z
                d = math.hypot(dx, dz)
                if d < w["rng"] and abs(t.y - e.y) < 1.6 and (dx * fx + dz * fz) / (d or 1) > 0.55:
                    self.damage(t, w["dmg"] * mult, e)
                    break
            return True
        if e.ammo[e.wi] <= 0:
            e.rel = w["reload"]
            return False
        e.ammo[e.wi] -= 1
        e.cd = w["rate"] * (1.8 if not e.player else 1.0)
        e.recoil = 1.0
        o = self.eye_pos(e)
        cy, sy, cp, sp = math.cos(e.yaw), math.sin(e.yaw), math.cos(e.pitch), math.sin(e.pitch)
        fwd = (sy * cp, sp, cy * cp)
        right = (cy, 0, -sy)
        up = (-sy * sp, cp, -cy * sp)
        spr = w["spread"] * (2.2 if not e.player else 1.0)
        if e.player and e.crouch_ads:
            spr *= 0.4
        rx, ry = random.uniform(-spr, spr), random.uniform(-spr, spr)
        d = [fwd[k] + right[k] * rx + up[k] * ry for k in range(3)]
        l = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
        d = [v / l for v in d]
        hit = self.trace(e, o, d, w["rng"])
        start = (o[0] + right[0] * .25, o[1] - .25, o[2] + right[2] * .25)
        self.tracers.append([start, (hit[0], hit[1], hit[2]), 0.07])
        if hit[3] is not None:
            self.damage(hit[3], w["dmg"] * mult, e, hit[4])
        return True

    def trace(self, shooter, o, d, rng):
        t = 0.6
        w = self.world
        while t < rng:
            px, py, pz = o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t
            if py < w.h(px, pz):
                return px, py, pz, None, False
            if py > 12 and d[1] > 0:
                break
            for e in self.ents:
                if e is shooter or not e.alive:
                    continue
                dx, dz = px - e.x, pz - e.z
                if dx * dx + dz * dz < 0.2 and e.y <= py <= e.y + e.height:
                    return px, py, pz, e, py > e.y + e.height - 0.3
            t += 0.25
        return o[0] + d[0] * rng, o[1] + d[1] * rng, o[2] + d[2] * rng, None, False

    def damage(self, v, amount, att, head=False):
        if not v.alive or v.inv > 0:
            return
        if head:
            amount *= 2
        v.hp -= amount
        if v.player:
            self.flash = min(1.0, self.flash + 0.55)
        else:
            v.target = att
            v.think = 0.6
        if att.player:
            self.hitmark = 0.35 if head else 0.2
        if v.hp <= 0:
            v.alive = False
            v.deaths += 1
            v.respawn = 3.0 if v.player else 4.0
            if att is not v:
                att.kills += 1
            self.feed.append([att.name + "  >  " + v.name, 4.0])
            if att.kills >= GOAL:
                self.winner = att
                self.set_state("end")

    def switch_weapon(self, e, i):
        if 0 <= i < 3 and i != e.wi:
            e.wi = i
            e.rel = 0
            e.cd = 0.35

    def start_reload(self, e):
        w = WEAPONS[e.wi]
        if not w["melee"] and e.rel <= 0 and e.ammo[e.wi] < w["mag"]:
            e.rel = w["reload"]

    # ---------- mise à jour ----------
    def tick_common(self, e, dt):
        e.cd = max(0, e.cd - dt)
        e.recoil = max(0, e.recoil - dt * 6)
        e.swing = max(0, e.swing - dt)
        e.inv = max(0, e.inv - dt)
        if e.rel > 0:
            e.rel -= dt
            if e.rel <= 0:
                e.rel = 0
                e.ammo[e.wi] = WEAPONS[e.wi]["mag"]

    def update_player(self, p, dt):
        keys = pygame.key.get_pressed()
        mb = pygame.mouse.get_pressed()
        mx, my = pygame.mouse.get_rel()
        ads = mb[2] and p.alive
        fov = WEAPONS[p.wi]["fov"] if ads else FOV
        self.cur_fov += (fov - self.cur_fov) * min(1, 14 * dt)
        sens = 0.0024 * (self.cur_fov / FOV)
        p.yaw += mx * sens
        p.pitch = clamp(p.pitch - my * sens, -1.45, 1.45)
        p.crouch_ads = False
        if not p.alive:
            p.respawn -= dt
            p.eye += (0.35 - p.eye) * min(1, 6 * dt)
            if p.respawn <= 0:
                self.spawn(p)
            return
        fw = keys[pygame.K_w] or keys[pygame.K_z]
        bk = keys[pygame.K_s]
        lf = keys[pygame.K_a] or keys[pygame.K_q]
        rt = keys[pygame.K_d]
        sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        ctrl = keys[pygame.K_LCTRL] or keys[pygame.K_c]
        ix = (1 if rt else 0) - (1 if lf else 0)
        iz = (1 if fw else 0) - (1 if bk else 0)
        n = math.hypot(ix, iz)
        if n:
            ix, iz = ix / n, iz / n
        crouch = ctrl or p.slide > 0
        speed = 5.0
        if sprint and iz > 0 and not ads and not crouch:
            speed = 8.0
        if crouch:
            speed = 2.6
        if ads:
            speed *= 0.6
        c, s = math.cos(p.yaw), math.sin(p.yaw)
        tvx = (ix * c + iz * s) * speed
        tvz = (-ix * s + iz * c) * speed
        accel = None
        if p.slide > 0:
            p.slide -= dt
            sp = 2.0 + 8.5 * max(0, p.slide) / 0.8
            tvx, tvz = p.sdx * sp, p.sdz * sp
            accel = 25.0
        if keys[pygame.K_SPACE] and p.on_ground:
            p.vy = JUMP_V
            p.on_ground = False
            p.slide = 0
        moved = self.move_ent(p, tvx, tvz, dt, accel)
        self.bob += moved * 2.2
        target_eye = 0.9 if p.slide > 0 else (1.1 if crouch else 1.7)
        p.eye += (target_eye - p.eye) * min(1, 12 * dt)
        p.height = p.eye + 0.15
        p.crouch_ads = crouch or ads
        lt = (1 if keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_LEFT] else 0)
        p.lean += (lt - p.lean) * min(1, 10 * dt)
        fire = mb[0]
        w = WEAPONS[p.wi]
        if fire and (w["auto"] or not self.fire_prev):
            self.try_fire(p)
        self.fire_prev = fire
        if p.ammo[p.wi] <= 0 and not w["melee"] and p.rel <= 0:
            self.start_reload(p)

    def visible(self, a, b):
        ax, ay, az = a.x, a.y + 1.5, a.z
        bx, by, bz = b.x, b.y + 1.2, b.z
        d = math.sqrt((bx - ax) ** 2 + (by - ay) ** 2 + (bz - az) ** 2)
        n = max(2, int(d / 0.6))
        for i in range(1, n):
            t = i / n
            if ay + (by - ay) * t < self.world.h(ax + (bx - ax) * t, az + (bz - az) * t):
                return False
        return True

    def update_bot(self, b, dt):
        if not b.alive:
            b.respawn -= dt
            if b.respawn <= 0:
                self.spawn(b)
            return
        b.think -= dt
        b.strafe_t -= dt
        if b.think <= 0:
            b.think = random.uniform(0.25, 0.5)
            best, bd = None, 1e9
            for e in self.ents:
                if e is b or not e.alive:
                    continue
                d = math.hypot(e.x - b.x, e.z - b.z)
                if d < 45 and d < bd and self.visible(b, e):
                    best, bd = e, d
            b.target = best
        t = b.target
        mvx, mvz = 0.0, 0.0
        if t is not None and t.alive:
            dx, dz = t.x - b.x, t.z - b.z
            d = math.hypot(dx, dz)
            diff = angdiff(math.atan2(dx, dz), b.yaw)
            turn = 3.2 * dt
            b.yaw += clamp(diff, -turn, turn)
            wp = math.atan2((t.y + 1.2) - (b.y + 1.5), d)
            b.pitch += clamp(wp - b.pitch, -2 * dt, 2 * dt)
            if b.strafe_t <= 0:
                b.strafe = random.choice((-1, 0, 1, 1, -1))
                b.strafe_t = random.uniform(0.6, 1.6)
            mvx = b.strafe
            mvz = 1 if d > 16 else (-1 if d < 5 else 0)
            if abs(diff) < 0.13 and d < 50:
                self.try_fire(b)
        else:
            b.wp_t -= dt
            if b.wp is None or b.wp_t <= 0 or math.hypot(b.wp[0] - b.x, b.wp[1] - b.z) < 2.0:
                b.wp = (random.uniform(3, 37), random.uniform(3, 37))
                b.wp_t = random.uniform(4, 8)
            diff = angdiff(math.atan2(b.wp[0] - b.x, b.wp[1] - b.z), b.yaw)
            turn = 2.5 * dt
            b.yaw += clamp(diff, -turn, turn)
            b.pitch += (0 - b.pitch) * min(1, 3 * dt)
            mvz = 1 if abs(diff) < 1.0 else 0
        c, s = math.cos(b.yaw), math.sin(b.yaw)
        n = math.hypot(mvx, mvz) or 1
        sp = 4.3
        tvx = (mvx * c + mvz * s) / n * sp
        tvz = (-mvx * s + mvz * c) / n * sp
        if mvx == 0 and mvz == 0:
            tvx = tvz = 0
        moved = self.move_ent(b, tvx, tvz, dt)
        if (tvx or tvz) and moved < 0.25 * sp * dt:
            b.stuck += dt
        else:
            b.stuck = 0
        if b.stuck > 0.3 and b.on_ground:
            b.vy = JUMP_V
            b.on_ground = False
        if b.stuck > 0.9:
            b.stuck = 0
            b.wp = None
            b.strafe = -b.strafe or 1
            b.strafe_t = 1.0
            if t is None:
                b.yaw += random.uniform(1.0, 2.5)
        if WEAPONS[b.wi]["mag"] and b.ammo[b.wi] <= 0 and b.rel <= 0:
            self.start_reload(b)

    def update(self, dt):
        p = self.player
        self.update_player(p, dt)
        for e in self.ents:
            if not e.player:
                self.update_bot(e, dt)
            self.tick_common(e, dt)
        for tr in self.tracers:
            tr[2] -= dt
        self.tracers = [t for t in self.tracers if t[2] > 0]
        for f in self.feed:
            f[1] -= dt
        self.feed = [f for f in self.feed if f[1] > 0][-5:]
        self.flash = max(0, self.flash - dt * 1.5)
        self.hitmark = max(0, self.hitmark - dt)

    # ---------- rendu 3D ----------
    def obox(self, cx, cy, cz, sx, sy, sz, yaw, col, out):
        c, s = math.cos(yaw), math.sin(yaw)
        hx, hy, hz = sx / 2, sy / 2, sz / 2

        def Pt(lx, ly, lz):
            return (cx + lx * c + lz * s, cy + ly, cz - lx * s + lz * c)

        faces = [
            ((0, 1, 0), [(-hx, hy, -hz), (hx, hy, -hz), (hx, hy, hz), (-hx, hy, hz)]),
            ((0, 0, 1), [(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]),
            ((0, 0, -1), [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz)]),
            ((-1, 0, 0), [(-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz)]),
            ((1, 0, 0), [(hx, -hy, -hz), (hx, -hy, hz), (hx, hy, hz), (hx, hy, -hz)]),
        ]
        for (nl, vs) in faces:
            wv = [Pt(*v) for v in vs]
            n = (nl[0] * c + nl[2] * s, nl[1], -nl[0] * s + nl[2] * c)
            fc = (sum(v[0] for v in wv) / 4, sum(v[1] for v in wv) / 4, sum(v[2] for v in wv) / 4)
            out.append((fc[0], fc[1], fc[2], n[0], n[1], n[2], wv, col))

    def ent_cells(self, e, out):
        y = e.yaw
        c, s = math.cos(y), math.sin(y)

        def at(lx, ly, lz):
            return e.x + lx * c + lz * s, e.y + ly, e.z - lx * s + lz * c

        dark = tuple(int(v * 0.6) for v in e.col)
        for lx in (-0.15, 0.15):
            p = at(lx, 0.4, 0)
            self.obox(p[0], p[1], p[2], 0.22, 0.8, 0.26, y, dark, out)
        p = at(0, 1.15, 0)
        self.obox(p[0], p[1], p[2], 0.56, 0.7, 0.32, y, e.col, out)
        p = at(0, 1.68, 0)
        self.obox(p[0], p[1], p[2], 0.28, 0.28, 0.28, y, (225, 180, 140), out)
        p = at(0.3, 1.2, 0.3)
        self.obox(p[0], p[1], p[2], 0.1, 0.12, 0.7, y, (40, 40, 45), out)

    def poly(self, verts, color):
        cx, cy, cz = self.cx, self.cy, self.cz
        cY, sY, cP, sP = self.cY, self.sY, self.cP, self.sP
        cam = []
        minz = 1e9
        for (x, y, z) in verts:
            dx, dy, dz = x - cx, y - cy, z - cz
            xc = dx * cY - dz * sY
            z1 = dx * sY + dz * cY
            yc = dy * cP - z1 * sP
            zc = dy * sP + z1 * cP
            cam.append((xc, yc, zc))
            if zc < minz:
                minz = zc
        if minz < NEAR:
            out = []
            n = len(cam)
            for i in range(n):
                a, b = cam[i], cam[(i + 1) % n]
                ai, bi = a[2] >= NEAR, b[2] >= NEAR
                if ai:
                    out.append(a)
                if ai != bi:
                    t = (NEAR - a[2]) / (b[2] - a[2])
                    out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, NEAR))
            cam = out
            if len(cam) < 3:
                return
        f = self.f
        pts = [(self.hw + xc * f / zc, self.hh - yc * f / zc) for xc, yc, zc in cam]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        if max(xs) < 0 or min(xs) > W or max(ys) < 0 or min(ys) > H:
            return
        pygame.draw.polygon(self.screen, color, pts)

    def project_pt(self, p):
        dx, dy, dz = p[0] - self.cx, p[1] - self.cy, p[2] - self.cz
        xc = dx * self.cY - dz * self.sY
        z1 = dx * self.sY + dz * self.cY
        yc = dy * self.cP - z1 * self.sP
        zc = dy * self.sP + z1 * self.cP
        if zc < NEAR:
            return None
        return self.hw + xc * self.f / zc, self.hh - yc * self.f / zc

    def shade(self, col, n, d):
        lt = 0.5 + 0.5 * max(0.0, n[0] * LX + n[1] * LY + n[2] * LZ)
        fg = min(1.0, (d / FOGD) ** 1.4)
        return (int(col[0] * lt * (1 - fg) + FOG[0] * fg),
                int(col[1] * lt * (1 - fg) + FOG[1] * fg),
                int(col[2] * lt * (1 - fg) + FOG[2] * fg))

    def render(self):
        p = self.player
        ex, ey, ez = self.eye_pos(p)
        self.cx, self.cy, self.cz = ex, ey, ez
        self.cY, self.sY = math.cos(p.yaw), math.sin(p.yaw)
        self.cP, self.sP = math.cos(p.pitch), math.sin(p.pitch)
        self.f = self.hw / math.tan(math.radians(self.cur_fov) / 2)
        scr = self.screen
        # ciel + sol
        hy = int(clamp(self.hh + self.f * math.tan(p.pitch), -2000, 2000))
        scr.fill((100, 112, 98))
        if hy > 0:
            hyc = min(hy, H)
            steps = 12
            for i in range(steps):
                t = i / steps
                col = (int(60 + (FOG[0] - 60) * t), int(110 + (FOG[1] - 110) * t), int(200 + (FOG[2] - 200) * t))
                y0 = int(hyc * i / steps)
                y1 = int(hyc * (i + 1) / steps) + 1
                pygame.draw.rect(scr, col, (0, y0, W, y1 - y0))
        # sol (dalles)
        fl = []
        for (fx, fy, fz, v, col) in self.world.floor:
            d = math.sqrt((fx - ex) ** 2 + (fz - ez) ** 2 + ey * ey)
            fl.append((d, v, col))
        fl.sort(key=itemgetter(0), reverse=True)
        for d, v, col in fl:
            self.poly(v, self.shade(col, (0, 1, 0), d))
        # objets
        dyn = []
        for e in self.ents:
            if e is not p and e.alive:
                self.ent_cells(e, dyn)
        fx = math.sin(p.yaw) * self.cP
        fy = self.sP
        fz = math.cos(p.yaw) * self.cP
        vis = []
        for (cx, cy, cz, nx, ny, nz, verts, col) in chain(self.world.cells, dyn):
            dx, dy, dz = cx - ex, cy - ey, cz - ez
            if nx * dx + ny * dy + nz * dz >= 0:
                continue
            if dx * fx + dy * fy + dz * fz < -4:
                continue
            d2 = dx * dx + dy * dy + dz * dz
            if d2 > 12000:
                continue
            vis.append((d2, verts, nx, ny, nz, col))
        vis.sort(key=itemgetter(0), reverse=True)
        for d2, verts, nx, ny, nz, col in vis:
            self.poly(verts, self.shade(col, (nx, ny, nz), math.sqrt(d2)))
        # traçantes
        for a, b, life in self.tracers:
            pa, pb = self.project_pt(a), self.project_pt(b)
            if pa and pb:
                pygame.draw.line(scr, (255, 235, 130), pa, pb, 2)

    # ---------- arme en vue FPS ----------
    def draw_viewmodel(self, p):
        w = WEAPONS[p.wi]
        ads = pygame.mouse.get_pressed()[2]
        bx = W / 2 + 40 if ads else W - 230
        by = H - 20 if ads else H
        bx += math.sin(self.bob) * (3 if ads else 9)
        by += abs(math.cos(self.bob)) * (2 if ads else 7)
        by += p.recoil * 14
        bx -= p.recoil * 4
        if p.rel > 0:
            ph = math.sin(math.pi * min(1, p.rel / w["reload"]))
            by += ph * 160
        sc = self.screen
        skin = (215, 170, 130)
        if w["id"] == "w0":
            pygame.draw.rect(sc, (35, 35, 40), (bx - 150, by - 175, 190, 26))
            pygame.draw.rect(sc, (55, 58, 66), (bx - 70, by - 160, 150, 70))
            pygame.draw.rect(sc, (25, 25, 28), (bx - 20, by - 95, 32, 70))
            pygame.draw.rect(sc, (70, 72, 80), (bx - 140, by - 190, 30, 14))
            pygame.draw.rect(sc, skin, (bx - 70, by - 100, 90, 50), border_radius=10)
        elif w["id"] == "w1":
            pygame.draw.rect(sc, (30, 30, 35), (bx - 290, by - 172, 360, 16))
            pygame.draw.rect(sc, (60, 60, 68), (bx - 120, by - 185, 140, 40))
            pygame.draw.rect(sc, (110, 75, 40), (bx - 20, by - 165, 160, 56), border_radius=6)
            pygame.draw.rect(sc, (20, 20, 22), (bx - 130, by - 205, 70, 18))
            pygame.draw.rect(sc, skin, (bx - 110, by - 150, 80, 46), border_radius=10)
        else:
            sw = math.sin(math.pi * (1 - p.swing / 0.3)) if p.swing > 0 else 0
            ox, oy = -sw * 170, -sw * 90
            pts = [(bx - 40 + ox, by - 80 + oy), (bx - 200 + ox, by - 260 + oy), (bx - 170 + ox, by - 285 + oy), (bx + 10 + ox, by - 110 + oy)]
            pygame.draw.polygon(sc, (205, 210, 220), pts)
            pygame.draw.polygon(sc, (60, 45, 35), [(bx - 40 + ox, by - 80 + oy), (bx + 10 + ox, by - 110 + oy), (bx + 50 + ox, by - 50 + oy), (bx + ox, by - 20 + oy)])
            pygame.draw.circle(sc, skin, (int(bx + 20 + ox), int(by - 40 + oy)), 28)
        if w["id"] == "w0" and p.recoil > 0.6:
            pygame.draw.circle(self.screen, (255, 210, 90), (int(bx - 155), int(by - 162)), int(10 + 14 * p.recoil))

    # ---------- HUD ----------
    def draw_hud(self):
        p = self.player
        sc = self.screen
        if p.alive:
            self.draw_viewmodel(p)
        # viseur
        cx, cy = W // 2, H // 2
        for dx, dy in ((-12, 0), (4, 0), (0, -12), (0, 4)):
            pygame.draw.rect(sc, (255, 255, 255), (cx + dx, cy + dy, 8 if dy == 0 else 2, 8 if dx == 0 else 2))
        if self.hitmark > 0:
            col = (255, 80, 80)
            for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                pygame.draw.line(sc, col, (cx + sx * 6, cy + sy * 6), (cx + sx * 14, cy + sy * 14), 3)
        # sang
        if self.flash > 0:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((200, 0, 0, int(110 * self.flash)))
            sc.blit(ov, (0, 0))
        # vie
        pygame.draw.rect(sc, (30, 30, 30), (20, H - 46, 260, 26), border_radius=6)
        hw = int(256 * max(0, p.hp) / 100)
        pygame.draw.rect(sc, (60, 200, 90) if p.hp > 35 else (220, 60, 60), (22, H - 44, hw, 22), border_radius=5)
        self.text(self.tr("hp") + " " + str(max(0, int(p.hp))), self.f_sm, (255, 255, 255), (30, H - 43))
        # munitions
        w = WEAPONS[p.wi]
        name = self.tr(w["id"])
        if w["melee"]:
            self.text(name, self.f_med, (255, 255, 255), (W - 20, H - 50), right=True)
        else:
            self.text("%d / %d" % (p.ammo[p.wi], w["mag"]), self.f_med, (255, 220, 90), (W - 20, H - 78), right=True)
            self.text(name, self.f_txt, (255, 255, 255), (W - 20, H - 40), right=True)
        if p.rel > 0:
            self.text(self.tr("reloading"), self.f_txt, (255, 200, 80), (W // 2, H // 2 + 60), center=True)
        # scores
        y = 10
        for e in sorted(self.ents, key=lambda e: -e.kills):
            col = (255, 230, 120) if e.player else (255, 255, 255)
            pygame.draw.rect(sc, e.col, (10, y + 4, 12, 14))
            self.text("%s : %d" % (e.name, e.kills), self.f_sm, col, (28, y))
            y += 22
        self.text(self.tr("goal", n=GOAL), self.f_sm, (200, 210, 230), (10, y + 4))
        y = 10
        for f, t in self.feed:
            self.text(f, self.f_sm, (255, 255, 255), (W - 12, y), right=True)
            y += 22
        if not p.alive:
            self.text(self.tr("dead"), self.f_big, (230, 60, 60), (W // 2, H // 2 - 40), center=True)
            self.text(self.tr("respawn", n=max(1, int(math.ceil(p.respawn)))), self.f_med, (255, 255, 255), (W // 2, H // 2 + 20), center=True)
        self.text("%d FPS" % self.clock.get_fps(), self.f_sm, (200, 200, 200), (W - 70, H - 100))

    def draw_pause(self):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        self.screen.blit(ov, (0, 0))
        self.button((W // 2 - 190, 240, 380, 70), self.tr("resume"), self.resume)
        self.button((W // 2 - 190, 330, 380, 70), self.tr("quit_menu"), lambda: self.set_state("menu"))

    def resume(self):
        self.paused = False
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)
        pygame.mouse.get_rel()

    def draw_end(self):
        self.render_frozen()
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        self.screen.blit(ov, (0, 0))
        win = self.winner is self.player
        self.text(self.tr("win") if win else self.tr("lose"), self.f_big,
                  (90, 230, 110) if win else (230, 70, 70), (W // 2, 200), center=True)
        y = 290
        for e in sorted(self.ents, key=lambda e: -e.kills):
            self.text("%s   %d / %d" % (e.name, e.kills, e.deaths), self.f_txt, (255, 255, 255), (W // 2, y), center=True)
            y += 32
        self.text(self.tr("click"), self.f_txt, (255, 220, 120), (W // 2, H - 60), center=True)
        self.btns.append((pygame.Rect(0, 0, W, H), lambda: self.set_state("menu")))

    def render_frozen(self):
        self.render()

    # ---------- boucle ----------
    def run(self):
        self.cur_fov = FOV
        while True:
            dt = min(0.05, self.clock.tick(60) / 1000.0)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.state != "game" or self.paused:
                        for rect, cb in list(self.btns):
                            if rect.collidepoint(ev.pos):
                                cb()
                                break
                elif ev.type == pygame.MOUSEWHEEL and self.state == "game" and not self.paused:
                    self.switch_weapon(self.player, (self.player.wi - ev.y) % 3)
                elif ev.type == pygame.KEYDOWN:
                    if self.state == "game":
                        if ev.key == pygame.K_ESCAPE:
                            if self.paused:
                                self.resume()
                            else:
                                self.paused = True
                                pygame.event.set_grab(False)
                                pygame.mouse.set_visible(True)
                        elif not self.paused and self.player.alive:
                            p = self.player
                            if ev.key in (pygame.K_1, pygame.K_KP1):
                                self.switch_weapon(p, 0)
                            elif ev.key in (pygame.K_2, pygame.K_KP2):
                                self.switch_weapon(p, 1)
                            elif ev.key in (pygame.K_3, pygame.K_KP3):
                                self.switch_weapon(p, 2)
                            elif ev.key == pygame.K_r:
                                self.start_reload(p)
                            elif ev.key in (pygame.K_LCTRL, pygame.K_c):
                                k = pygame.key.get_pressed()
                                sp = math.hypot(p.vx, p.vz)
                                if (k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT]) and p.on_ground and sp > 3 and p.slide <= 0:
                                    p.slide = 0.8
                                    p.sdx, p.sdz = p.vx / sp, p.vz / sp
                    elif ev.key == pygame.K_ESCAPE and self.state != "menu":
                        self.set_state("menu")
            self.btns = []
            st = self.state
            if st == "menu":
                self.draw_main()
            elif st == "settings":
                self.draw_settings()
            elif st == "lang":
                self.draw_lang()
            elif st == "maps":
                self.draw_maps()
            elif st == "game":
                if not self.paused:
                    self.update(dt)
                if self.state == "game":
                    self.render()
                    self.draw_hud()
                    if self.paused:
                        self.draw_pause()
            elif st == "end":
                self.draw_end()
            pygame.display.flip()


if __name__ == "__main__":
    Game().run()
