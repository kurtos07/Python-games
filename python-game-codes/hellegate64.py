#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HELLEGATE 64  -  FPS "raycasting" inspiré de Doom 64  /  Doom 64-style FPS
Python 3 + pygame.  Aucun fichier externe : textures, sprites, sons et niveaux
sont tous générés par le code.

Installation :   pip install pygame
Lancement    :   python3 hellegate64.py

COMMANDES
  Z/W Q/A S D / flèches ... se déplacer (flèches gauche/droite = tourner)
  Souris .................. tourner         Clic gauche / Espace ... tirer
  Maj ..................... courir          E ...................... ouvrir porte / sortie
  1 2 3 4 ou molette ...... changer d'arme  TAB .................... mini-carte
  Echap ................... pause           F11 .................... plein écran

Si le jeu rame : baisse RAYS (ex : 240 ou 160) juste en dessous.
"""
import math
import random
import sys
import array
import os
import pygame

# ----------------------------------------------------------------------------
#  CONFIG
# ----------------------------------------------------------------------------
W, H = 640, 360          # résolution interne (agrandie à la taille de la fenêtre)
RAYS = 320               # nombre de colonnes de rendu (doit diviser W). 320 = joli, 160 = rapide
COLW = W // RAYS
HALF_H = H // 2
FPS = 60
SHADES = 16              # niveaux de brouillard / lumière
HUD_H = 40
PLANE = 0.80             # champ de vision (0.66 = 66 deg, 0.80 = 77 deg, 1.0 = 90 deg)
MOUSE_SENS = 0.0022

# ----------------------------------------------------------------------------
#  LANGUES  (français / anglais)
# ----------------------------------------------------------------------------
LANG = 'fr'
LANG_FILE = os.path.join(os.path.expanduser('~'), '.hellegate64_lang')


def load_lang():
    global LANG
    try:
        with open(LANG_FILE, 'r', encoding='utf-8') as f:
            v = f.read().strip()
        if v in ('fr', 'en'):
            LANG = v
    except Exception:
        pass


def save_lang():
    try:
        with open(LANG_FILE, 'w', encoding='utf-8') as f:
            f.write(LANG)
    except Exception:
        pass


TXT = {
    'subtitle': ("Un FPS inspiré de Doom 64", "A Doom 64-inspired FPS"),
    'press_enter': ("Appuie sur ENTRÉE pour commencer", "Press ENTER to start"),
    'ctrl1': ("ZQSD / WASD : bouger   Souris : viser   Clic / Espace : tirer   Maj : courir",
              "WASD : move   Mouse : aim   Click / Space : fire   Shift : run"),
    'ctrl2': ("E : portes / sortie   1-2-3-4 : armes   TAB : carte   L : langue   Échap : pause",
              "E : doors / exit   1-2-3-4 : weapons   TAB : map   L : language   Esc : pause"),
    'ammo': ("MUNITIONS", "AMMO"),
    'health': ("SANTÉ", "HEALTH"),
    'armor': ("ARMURE", "ARMOR"),
    'enemies': ("ENNEMIS %d/%d", "ENEMIES %d/%d"),
    'level': ("NIVEAU %d  -  %s", "LEVEL %d  -  %s"),
    'dead': ("VOUS ÊTES MORT", "YOU DIED"),
    'retry': ("Appuie sur R pour recommencer le niveau", "Press R to restart the level"),
    'pause': ("PAUSE", "PAUSED"),
    'resume': ("Échap : reprendre", "Esc : resume"),
    'quit': ("Q : quitter", "Q : quit"),
    'lang_change': ("L : changer de langue", "L : change language"),
    'lvl_done': ("NIVEAU TERMINÉ", "LEVEL COMPLETE"),
    'kills': ("Ennemis tués : %d / %d", "Enemies killed: %d / %d"),
    'time': ("Temps : %d:%02d", "Time: %d:%02d"),
    'continue': ("ENTRÉE pour continuer", "ENTER to continue"),
    'victory': ("VICTOIRE !", "VICTORY!"),
    'win1': ("Le Seigneur de l'Abîme est vaincu.", "The Abyss Lord has been slain."),
    'win2': ("Les portes de l'enfer sont refermées.", "The gates of hell are sealed."),
    'win3': ("ENTRÉE : retour au menu", "ENTER : back to menu"),
    'boss_guard': ("Un boss garde encore la sortie !", "A boss still guards the exit!"),
    'm_health': ("Trousse de soins  +25", "Medkit  +25"),
    'm_armor': ("Armure  +50", "Armor  +50"),
    'm_bullets': ("Balles  +20", "Bullets  +20"),
    'm_shells': ("Cartouches  +8", "Shells  +8"),
    'm_shotgun': ("FUSIL À POMPE !", "SHOTGUN!"),
    'm_chain': ("MITRAILLEUSE !", "CHAINGUN!"),
    'm_cannon': ("ANNIHILATEUR !  (rechargement : 25 s)", "ANNIHILATOR!  (25 s reload)"),
    'm_ready': ("ANNIHILATEUR PRÊT !", "ANNIHILATOR READY!"),
    'ready': ("PRÊT", "READY"),
    'lang_hint': ("Haut / Bas puis ENTRÉE   |   Up / Down then ENTER", ""),
}


def tr(key):
    return TXT[key][0 if LANG == 'fr' else 1]


def L2(pair):
    """Choisit la bonne langue dans un couple (français, anglais)."""
    return pair[0 if LANG == 'fr' else 1]


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp_col(c1, c2, t):
    t = clamp(t, 0.0, 1.0)
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


# ----------------------------------------------------------------------------
#  SONS  (synthétisés par le code)
# ----------------------------------------------------------------------------
class Sounds:
    def __init__(self):
        self.ok = False
        self.s = {}
        self.ch = 1
        self.sr = 22050
        try:
            pygame.mixer.init(22050, -16, 1, 512)
            init = pygame.mixer.get_init()
            if not init or init[1] != -16:
                return
            self.sr, _, self.ch = init
            pygame.mixer.set_num_channels(24)
            self._build()
            self.ok = True
        except Exception:
            self.ok = False

    def _synth(self, dur, fn, vol=0.6):
        n = int(self.sr * dur)
        a = array.array('h')
        for i in range(n):
            v = int(clamp(fn(i / self.sr) * vol, -1.0, 1.0) * 32767)
            for _ in range(self.ch):
                a.append(v)
        return pygame.mixer.Sound(buffer=a.tobytes())

    def _build(self):
        pi2 = 2 * math.pi
        rnd = random.uniform
        sin = math.sin
        exp = math.exp
        S = self.s
        S['pistol'] = self._synth(0.25, lambda t: rnd(-1, 1) * exp(-t * 28) + 0.8 * sin(pi2 * 140 * t) * exp(-t * 30), 0.8)
        S['shotgun'] = self._synth(0.55, lambda t: rnd(-1, 1) * exp(-t * 9) + sin(pi2 * 70 * t) * exp(-t * 10), 0.85)
        S['chain'] = self._synth(0.12, lambda t: rnd(-1, 1) * exp(-t * 40) + 0.6 * sin(pi2 * 160 * t) * exp(-t * 40), 0.7)
        S['click'] = self._synth(0.05, lambda t: rnd(-1, 1) * exp(-t * 120), 0.5)
        S['fire'] = self._synth(0.45, lambda t: rnd(-1, 1) * 0.5 * exp(-t * 6) * (0.5 + 0.5 * sin(pi2 * 30 * t)) + 0.5 * sin(pi2 * 260 * (1 - t) * t * 3), 0.6)
        S['boom'] = self._synth(0.45, lambda t: rnd(-1, 1) * exp(-t * 8) + sin(pi2 * 55 * t) * exp(-t * 6), 0.7)
        S['growl'] = self._synth(0.6, lambda t: sin(pi2 * (85 + 25 * sin(pi2 * 7 * t)) * t) * exp(-t * 3) + rnd(-1, 1) * 0.15 * exp(-t * 4), 0.6)
        S['pain'] = self._synth(0.28, lambda t: (((t * 190) % 1.0) * 2 - 1) * exp(-t * 10), 0.5)
        S['death'] = self._synth(0.85, lambda t: (((t * (120 - 80 * t)) % 1.0) * 2 - 1) * exp(-t * 3) + rnd(-1, 1) * 0.2 * exp(-t * 8), 0.6)
        S['claw'] = self._synth(0.18, lambda t: rnd(-1, 1) * exp(-t * 18) * 0.8, 0.6)
        S['pickup'] = self._synth(0.25, lambda t: sin(pi2 * (500 * t + 1000 * t * t)) * exp(-t * 9), 0.5)
        S['door'] = self._synth(0.9, lambda t: (rnd(-1, 1) * 0.3 * (0.5 + 0.5 * sin(pi2 * 6 * t)) + 0.5 * sin(pi2 * 55 * t)) * min(1.0, t * 10) * exp(-t * 1.5), 0.6)
        S['hurt'] = self._synth(0.3, lambda t: sin(pi2 * 70 * t) * exp(-t * 12) + rnd(-1, 1) * 0.5 * exp(-t * 20), 0.8)
        S['cannon'] = self._synth(1.4, lambda t: rnd(-1, 1) * exp(-t * 3.5) + 1.2 * sin(pi2 * 38 * t) * exp(-t * 2.2) + 0.6 * sin(pi2 * 90 * t) * exp(-t * 6), 0.95)
        S['ready'] = self._synth(0.35, lambda t: sin(pi2 * (700 * t + 600 * t * t)) * exp(-t * 6) * 0.6 + sin(pi2 * 1400 * t) * exp(-t * 12) * 0.3, 0.5)
        S['drone'] = self._synth(4.0, lambda t: 0.35 * sin(pi2 * 55 * t) + 0.25 * sin(pi2 * 55.5 * t) + 0.15 * sin(pi2 * 82.5 * t + sin(pi2 * 0.25 * t)), 0.5)

    def play(self, name, dist=0.0, vol=1.0):
        if not self.ok:
            return
        snd = self.s.get(name)
        if snd is None:
            return
        v = vol if dist <= 0 else vol * clamp(1.0 - dist / 22.0, 0.12, 1.0)
        snd.set_volume(v)
        snd.play()

    def start_drone(self):
        if self.ok:
            d = self.s['drone']
            d.set_volume(0.22)
            d.play(loops=-1)


# ----------------------------------------------------------------------------
#  TEXTURES de murs (générées)
# ----------------------------------------------------------------------------
def _noise(surf, r, amount, count):
    w, h = surf.get_size()
    for _ in range(count):
        x = r.randrange(w)
        y = r.randrange(h)
        c = surf.get_at((x, y))
        d = r.randint(-amount, amount)
        surf.set_at((x, y), (clamp(c[0] + d, 0, 255), clamp(c[1] + d, 0, 255), clamp(c[2] + d, 0, 255)))


def tex_brick(base, mortar, seed):
    r = random.Random(seed)
    s = pygame.Surface((64, 64))
    s.fill(mortar)
    for row in range(4):
        y0 = row * 16
        off = 0 if row % 2 == 0 else 16
        for bx in range(-1, 3):
            x0 = bx * 32 + off
            col = tuple(clamp(c + r.randint(-14, 14), 0, 255) for c in base)
            pygame.draw.rect(s, col, (x0 + 1, y0 + 1, 30, 14))
            pygame.draw.line(s, tuple(clamp(c + 24, 0, 255) for c in col), (x0 + 1, y0 + 1), (x0 + 30, y0 + 1))
            pygame.draw.line(s, tuple(clamp(c - 24, 0, 255) for c in col), (x0 + 1, y0 + 14), (x0 + 30, y0 + 14))
    _noise(s, r, 18, 700)
    return s


def tex_tech(seed):
    r = random.Random(seed)
    s = pygame.Surface((64, 64))
    s.fill((40, 48, 62))
    for px in (0, 32):
        for py in (0, 32):
            pygame.draw.rect(s, (58, 70, 90), (px + 2, py + 2, 28, 28))
            pygame.draw.rect(s, (24, 30, 40), (px + 2, py + 2, 28, 28), 1)
            pygame.draw.line(s, (96, 110, 134), (px + 3, py + 3), (px + 28, py + 3))
            for rx, ry in ((4, 4), (27, 4), (4, 27), (27, 27)):
                pygame.draw.circle(s, (120, 130, 150), (px + rx, py + ry), 1)
    pygame.draw.rect(s, (60, 230, 255), (8, 12, 6, 3))
    pygame.draw.rect(s, (60, 255, 120), (40, 12, 6, 3))
    pygame.draw.rect(s, (255, 60, 40), (40, 44, 6, 3))
    pygame.draw.rect(s, (255, 190, 40), (8, 44, 6, 3))
    for i in range(5):
        pygame.draw.line(s, (20, 24, 32), (10, 36 + i * 3), (24, 36 + i * 3))
    _noise(s, r, 10, 500)
    return s


def tex_hell(seed):
    r = random.Random(seed)
    s = pygame.Surface((64, 64))
    s.fill((92, 24, 22))
    for _ in range(40):
        pygame.draw.circle(s, (r.randint(70, 130), r.randint(14, 34), r.randint(14, 30)),
                           (r.randrange(64), r.randrange(64)), r.randint(3, 9))
    for _ in range(14):
        x, y = r.randrange(64), r.randrange(64)
        for _ in range(10):
            nx = clamp(x + r.randint(-5, 5), 0, 63)
            ny = clamp(y + r.randint(-5, 5), 0, 63)
            pygame.draw.line(s, (46, 8, 10), (x, y), (nx, ny), 1)
            x, y = nx, ny
    cx, cy, rad = 32, 32, 22
    pygame.draw.circle(s, (20, 4, 6), (cx, cy), rad + 3, 3)
    pts = [(cx + rad * math.sin(2 * math.pi * k / 5), cy + rad * math.cos(2 * math.pi * k / 5)) for k in range(5)]
    order = [0, 2, 4, 1, 3, 0]
    for a, b in zip(order, order[1:]):
        pygame.draw.line(s, (230, 50, 30), pts[a], pts[b], 1)
    _noise(s, r, 12, 500)
    return s


def tex_slime(seed):
    r = random.Random(seed)
    s = pygame.Surface((64, 64))
    s.fill((28, 66, 40))
    for _ in range(60):
        pygame.draw.circle(s, (40, 90, 52), (r.randrange(64), r.randrange(64)), r.randint(1, 4))
    for k in range(24):
        x, y = r.randrange(64), r.randrange(64)
        col = (70, 140, 80) if k % 2 else (14, 36, 22)
        for _ in range(8):
            nx = clamp(x + r.randint(-6, 6), 0, 63)
            ny = clamp(y + r.randint(-6, 6), 0, 63)
            pygame.draw.line(s, col, (x, y), (nx, ny), 1)
            x, y = nx, ny
    pygame.draw.line(s, (10, 24, 14), (0, 0), (63, 0), 2)
    pygame.draw.line(s, (10, 24, 14), (0, 32), (63, 32), 2)
    pygame.draw.line(s, (10, 24, 14), (0, 0), (0, 63), 2)
    pygame.draw.line(s, (10, 24, 14), (32, 0), (32, 63), 2)
    _noise(s, r, 12, 400)
    return s


def tex_metal(seed):
    r = random.Random(seed)
    s = pygame.Surface((64, 64))
    s.fill((84, 86, 92))
    for x in range(0, 64, 8):
        pygame.draw.line(s, (58, 60, 66), (x, 0), (x, 63))
        pygame.draw.line(s, (116, 118, 128), (x + 1, 0), (x + 1, 63))
    pygame.draw.rect(s, (20, 20, 20), (0, 26, 64, 12))
    for x0 in range(-12, 64, 12):
        pygame.draw.polygon(s, (230, 190, 20), [(x0, 38), (x0 + 6, 38), (x0 + 12, 26), (x0 + 6, 26)])
    _noise(s, r, 12, 500)
    return s


def tex_exit():
    s = pygame.Surface((64, 64))
    s.fill((18, 40, 24))
    pygame.draw.rect(s, (90, 255, 110), (0, 0, 64, 64), 3)
    pygame.draw.rect(s, (30, 90, 44), (6, 6, 52, 52), 2)
    font = pygame.font.Font(None, 26)
    t = font.render("EXIT", True, (140, 255, 150))
    s.blit(t, (32 - t.get_width() // 2, 24))
    pygame.draw.polygon(s, (140, 255, 150), [(20, 46), (44, 46), (32, 56)])
    return s


def tex_door(seed):
    r = random.Random(seed)
    s = pygame.Surface((64, 64))
    s.fill((96, 96, 108))
    pygame.draw.rect(s, (56, 56, 66), (0, 0, 64, 64), 2)
    pygame.draw.line(s, (30, 30, 38), (32, 0), (32, 63), 2)
    for y0 in (2, 54):
        pygame.draw.rect(s, (20, 20, 20), (2, y0, 60, 8))
        for x0 in range(-8, 64, 10):
            pygame.draw.polygon(s, (230, 190, 20), [(x0, y0 + 8), (x0 + 5, y0 + 8), (x0 + 10, y0), (x0 + 5, y0)])
    pygame.draw.rect(s, (220, 30, 30), (28, 30, 8, 5))
    pygame.draw.rect(s, (255, 120, 120), (30, 31, 4, 2))
    for rx, ry in ((6, 14), (57, 14), (6, 49), (57, 49)):
        pygame.draw.circle(s, (130, 130, 144), (rx, ry), 2)
    _noise(s, r, 10, 400)
    return s


def tex_lava(seed):
    r = random.Random(seed)
    s = pygame.Surface((64, 64))
    s.fill((38, 22, 18))
    for _ in range(60):
        pygame.draw.circle(s, (r.randint(30, 60), r.randint(16, 30), r.randint(12, 24)),
                           (r.randrange(64), r.randrange(64)), r.randint(2, 7))
    for _ in range(10):
        x, y = r.randrange(64), r.randrange(64)
        for _ in range(9):
            nx = clamp(x + r.randint(-6, 6), 0, 63)
            ny = clamp(y + r.randint(-6, 6), 0, 63)
            pygame.draw.line(s, (255, 90, 10), (x, y), (nx, ny), 2)
            pygame.draw.line(s, (255, 210, 70), (x, y), (nx, ny), 1)
            x, y = nx, ny
    _noise(s, r, 14, 500)
    return s


def make_textures():
    return {
        1: tex_brick((112, 98, 84), (40, 34, 30), 1),
        2: tex_tech(2),
        3: tex_hell(3),
        4: tex_slime(4),
        5: tex_metal(5),
        6: tex_exit(),
        7: tex_door(7),
        8: tex_lava(8),
    }


def build_columns(base, fog):
    """Pour chaque texture et chaque niveau de brouillard : 64 colonnes d'1 pixel."""
    cols = {}
    for t, surf in base.items():
        lst = []
        for sh in range(SHADES):
            f = (sh / (SHADES - 1)) ** 0.85
            img = surf.copy()
            if f > 0:
                ov = pygame.Surface((64, 64))
                ov.fill(fog)
                ov.set_alpha(int(255 * f))
                img.blit(ov, (0, 0))
            lst.append([img.subsurface((x, 0, 1, 64)) for x in range(64)])
        cols[t] = lst
    return cols


def build_bg(meta):
    s = pygame.Surface((W, H))
    fog = meta['fog']
    for y in range(HALF_H):
        t = y / HALF_H
        pygame.draw.line(s, lerp_col(meta['ceil'], fog, t ** 1.5), (0, y), (W, y))
    for y in range(HALF_H, H):
        t = (y - HALF_H) / (H - HALF_H)
        pygame.draw.line(s, lerp_col(fog, meta['floor'], t ** 0.8), (0, y), (W, y))
    return s


# ----------------------------------------------------------------------------
#  SPRITES (générés)
# ----------------------------------------------------------------------------
def _flash_add(s, amt=70):
    s.fill((amt, amt // 2, amt // 2, 0), special_flags=pygame.BLEND_RGB_ADD)
    return s


def draw_biped(skin, dark, eye, horns, bulk, glow, pose):
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    cx = 32
    lw = int(9 * bulk)
    lb = 63 - (4 if pose == 'w0' else 0)
    rb = 63 - (4 if pose == 'w1' else 0)
    pygame.draw.rect(s, dark, (cx - 2 - lw, 42, lw, lb - 41))
    pygame.draw.rect(s, dark, (cx + 2, 42, lw, rb - 41))
    pygame.draw.rect(s, (30, 20, 20), (cx - 3 - lw, lb - 3, lw + 2, 4))
    pygame.draw.rect(s, (30, 20, 20), (cx + 2, rb - 3, lw + 2, 4))
    tw = int(15 * bulk)
    bw = int(11 * bulk)
    torso = [(cx - tw, 22), (cx + tw, 22), (cx + bw, 46), (cx - bw, 46)]
    pygame.draw.polygon(s, skin, torso)
    pygame.draw.polygon(s, dark, torso, 2)
    for i in range(3):
        y = 28 + i * 6
        pygame.draw.line(s, dark, (cx - bw + 3, y), (cx + bw - 3, y), 1)
    for sgn in (-1, 1):
        sh = (cx + sgn * tw, 24)
        if pose == 'at':
            hand = (cx + sgn * 22, 8)
        elif pose == 'pa':
            hand = (cx + sgn * 27, 30)
        else:
            hand = (cx + sgn * (21 if pose == 'w0' else 19), 44)
        pygame.draw.line(s, skin, sh, hand, 6)
        pygame.draw.circle(s, dark, hand, 4)
        for k in (-1, 0, 1):
            pygame.draw.line(s, (240, 230, 200), hand, (hand[0] + k * 3, hand[1] + (-5 if pose == 'at' else 5)), 1)
    if pose == 'at' and glow:
        pygame.draw.circle(s, (255, 150, 30), (cx, 7), 7)
        pygame.draw.circle(s, (255, 240, 160), (cx, 7), 3)
    hr = int(10 * bulk)
    pygame.draw.circle(s, skin, (cx, 15), hr)
    pygame.draw.circle(s, dark, (cx, 15), hr, 2)
    if horns:
        pygame.draw.polygon(s, (232, 222, 190), [(cx - hr + 2, 10), (cx - hr - 4, 0), (cx - hr + 7, 6)])
        pygame.draw.polygon(s, (232, 222, 190), [(cx + hr - 2, 10), (cx + hr + 4, 0), (cx + hr - 7, 6)])
    pygame.draw.rect(s, eye, (cx - 6, 11, 4, 3))
    pygame.draw.rect(s, eye, (cx + 2, 11, 4, 3))
    if pose in ('at', 'pa'):
        pygame.draw.ellipse(s, (20, 0, 0), (cx - 5, 17, 10, 7))
        for k in range(3):
            pygame.draw.polygon(s, (245, 245, 235), [(cx - 4 + k * 3, 17), (cx - 3 + k * 3, 20), (cx - 2 + k * 3, 17)])
    else:
        pygame.draw.line(s, (20, 0, 0), (cx - 5, 20), (cx + 5, 20), 2)
    return s


def draw_caco(pose):
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    bob = 2 if pose == 'w1' else 0
    body = (190, 40, 36)
    dark = (100, 18, 22)
    pygame.draw.polygon(s, (232, 222, 190), [(18, 12 + bob), (13, 1), (25, 9 + bob)])
    pygame.draw.polygon(s, (232, 222, 190), [(46, 12 + bob), (51, 1), (39, 9 + bob)])
    pygame.draw.circle(s, body, (32, 33 + bob), 26)
    pygame.draw.circle(s, dark, (32, 33 + bob), 26, 3)
    pygame.draw.ellipse(s, (214, 84, 72), (14, 44 + bob, 36, 14))
    pygame.draw.circle(s, (240, 240, 226), (32, 24 + bob), 10)
    pygame.draw.circle(s, (80, 220, 60), (32, 24 + bob), 6)
    pygame.draw.circle(s, (0, 0, 0), (32, 24 + bob), 3)
    if pose in ('at', 'pa'):
        pygame.draw.ellipse(s, (20, 0, 0), (14, 38 + bob, 36, 20))
        pygame.draw.ellipse(s, (255, 130, 20), (22, 44 + bob, 20, 10))
        for k in range(6):
            pygame.draw.polygon(s, (245, 245, 235), [(17 + k * 5, 40 + bob), (19 + k * 5, 46 + bob), (21 + k * 5, 40 + bob)])
    else:
        pygame.draw.arc(s, (20, 0, 0), (14, 36 + bob, 36, 14), math.pi, 2 * math.pi, 3)
        for k in range(6):
            pygame.draw.polygon(s, (245, 245, 235), [(17 + k * 5, 43 + bob), (19 + k * 5, 48 + bob), (21 + k * 5, 43 + bob)])
    return s


ART = {
    'imp':   dict(skin=(128, 78, 46), dark=(66, 38, 24), eye=(255, 230, 60), horns=False, bulk=1.0, glow=True),
    'demon': dict(skin=(214, 112, 126), dark=(128, 58, 70), eye=(255, 255, 100), horns=True, bulk=1.3, glow=False),
    'baron': dict(skin=(186, 64, 56), dark=(84, 24, 28), eye=(90, 255, 90), horns=True, bulk=1.2, glow=True),
    'titan': dict(skin=(70, 74, 96), dark=(22, 24, 38), eye=(255, 50, 50), horns=True, bulk=1.35, glow=True),
}


def make_enemy_frames(kind):
    if kind == 'caco':
        def draw(pose):
            return draw_caco(pose)
    else:
        a = ART[kind]

        def draw(pose):
            return draw_biped(a['skin'], a['dark'], a['eye'], a['horns'], a['bulk'], a['glow'], pose)
    frames = {
        'walk': [draw('w0'), draw('w1')],
        'attack': [draw('at')],
        'pain': [_flash_add(draw('pa'))],
        'dead': [],
    }
    stand = draw('w0')
    if kind == 'caco':
        for hh in (46, 30, 14):
            d = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.ellipse(d, (110, 8, 8), (2, 52, 60, 11))
            d.blit(pygame.transform.scale(stand, (64, hh)), (0, 64 - hh))
            frames['dead'].append(d)
    else:
        for ang, drop in ((28, 2), (62, 6), (90, 10)):
            d = pygame.Surface((64, 64), pygame.SRCALPHA)
            if ang > 30:
                pygame.draw.ellipse(d, (110, 8, 8), (4, 52, 56, 11))
            r = pygame.transform.rotate(stand, ang)
            d.blit(r, r.get_rect(center=(32, 32 + drop)))
            frames['dead'].append(d)
    return frames


def radial(size, stops):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    for rf, col in stops:
        pygame.draw.circle(s, col, (c, c), max(1, int(c * rf)))
    return s


def make_fx():
    fx = {
        'fire': radial(32, [(1.0, (255, 60, 0, 60)), (0.75, (255, 120, 10, 150)), (0.5, (255, 190, 40, 230)), (0.25, (255, 255, 200, 255))]),
        'plasma': radial(32, [(1.0, (0, 255, 80, 60)), (0.75, (40, 255, 120, 150)), (0.5, (120, 255, 160, 230)), (0.25, (230, 255, 240, 255))]),
        'boom': radial(48, [(1.0, (255, 80, 0, 90)), (0.8, (255, 140, 20, 170)), (0.55, (255, 210, 60, 230)), (0.3, (255, 255, 220, 255))]),
        'spark': radial(16, [(1.0, (255, 200, 60, 120)), (0.5, (255, 255, 200, 255))]),
        'blood': radial(24, [(1.0, (120, 0, 0, 170)), (0.6, (180, 10, 10, 230))]),
    }
    return fx


def make_pickups():
    P = {}
    s = pygame.Surface((32, 32), pygame.SRCALPHA)           # trousse de soins
    pygame.draw.rect(s, (235, 235, 235), (4, 10, 24, 18))
    pygame.draw.rect(s, (90, 90, 90), (4, 10, 24, 18), 2)
    pygame.draw.rect(s, (210, 20, 20), (14, 12, 4, 14))
    pygame.draw.rect(s, (210, 20, 20), (9, 17, 14, 4))
    P['h'] = s
    s = pygame.Surface((32, 32), pygame.SRCALPHA)           # armure
    pts = [(6, 6), (26, 6), (28, 16), (22, 28), (10, 28), (4, 16)]
    pygame.draw.polygon(s, (60, 110, 230), pts)
    pygame.draw.polygon(s, (20, 40, 120), pts, 2)
    pygame.draw.line(s, (200, 220, 255), (16, 8), (16, 26), 2)
    P['r'] = s
    s = pygame.Surface((32, 32), pygame.SRCALPHA)           # balles
    pygame.draw.rect(s, (90, 100, 50), (4, 16, 24, 12))
    for i in range(5):
        pygame.draw.rect(s, (230, 190, 60), (7 + i * 4, 8, 3, 9))
        pygame.draw.rect(s, (160, 90, 40), (7 + i * 4, 6, 3, 3))
    P['a'] = s
    s = pygame.Surface((32, 32), pygame.SRCALPHA)           # cartouches
    pygame.draw.rect(s, (150, 40, 30), (4, 16, 24, 12))
    for i in range(4):
        pygame.draw.rect(s, (200, 50, 40), (7 + i * 5, 6, 4, 11))
        pygame.draw.rect(s, (220, 180, 70), (7 + i * 5, 14, 4, 3))
    P['b'] = s
    s = pygame.Surface((32, 32), pygame.SRCALPHA)           # fusil
    pygame.draw.rect(s, (120, 120, 132), (2, 14, 28, 4))
    pygame.draw.rect(s, (120, 120, 132), (2, 19, 28, 3))
    pygame.draw.polygon(s, (110, 70, 34), [(2, 14), (10, 14), (10, 24), (4, 26)])
    P['s'] = s
    s = pygame.Surface((32, 32), pygame.SRCALPHA)           # mitrailleuse
    pygame.draw.rect(s, (80, 82, 92), (2, 12, 26, 8))
    pygame.draw.circle(s, (110, 112, 124), (22, 16), 7)
    pygame.draw.circle(s, (40, 40, 46), (22, 16), 3)
    pygame.draw.rect(s, (60, 40, 20), (3, 20, 8, 8))
    P['g'] = s
    s = pygame.Surface((32, 32), pygame.SRCALPHA)           # annihilateur
    pygame.draw.rect(s, (60, 62, 74), (2, 11, 28, 11))
    pygame.draw.rect(s, (110, 112, 130), (2, 11, 28, 3))
    pygame.draw.circle(s, (255, 120, 20), (22, 16), 6)
    pygame.draw.circle(s, (255, 240, 160), (22, 16), 3)
    pygame.draw.rect(s, (40, 40, 48), (2, 22, 10, 7))
    P['x'] = s
    return P


# ----------------------------------------------------------------------------
#  ARMES (dessinées par le code)
# ----------------------------------------------------------------------------
def _flash_star(surf, x, y, r):
    pts = []
    for k in range(16):
        rad = r if k % 2 == 0 else r * 0.35
        a = k * math.pi / 8
        pts.append((x + math.cos(a) * rad, y + math.sin(a) * rad))
    pygame.draw.polygon(surf, (255, 170, 40), pts)
    pygame.draw.circle(surf, (255, 240, 170), (int(x), int(y)), int(r * 0.4))
    pygame.draw.circle(surf, (255, 255, 255), (int(x), int(y)), int(r * 0.2))


def draw_weapon(surf, wid, cx, by, kick, flash, spin, charge=1.0):
    y = by + kick * 14
    glove = (52, 50, 56)
    if wid == 0:
        pygame.draw.polygon(surf, glove, [(cx - 30, by + 30), (cx - 14, y - 30), (cx + 14, y - 30), (cx + 30, by + 30)])
        pygame.draw.rect(surf, (70, 72, 82), (cx - 9, y - 90, 18, 64))
        pygame.draw.rect(surf, (128, 132, 146), (cx - 9, y - 90, 5, 64))
        pygame.draw.rect(surf, (40, 40, 48), (cx - 11, y - 62, 22, 12))
        pygame.draw.rect(surf, (20, 20, 24), (cx - 4, y - 92, 8, 4))
        if flash:
            _flash_star(surf, cx, y - 98, 26)
    elif wid == 1:
        pump = math.sin(min(1.0, kick) * math.pi) * 10
        pygame.draw.polygon(surf, glove, [(cx - 36, by + 30), (cx - 18, y - 24), (cx + 18, y - 24), (cx + 36, by + 30)])
        pygame.draw.rect(surf, (62, 64, 72), (cx - 15, y - 112, 13, 90))
        pygame.draw.rect(surf, (62, 64, 72), (cx + 2, y - 112, 13, 90))
        pygame.draw.rect(surf, (130, 134, 148), (cx - 15, y - 112, 4, 90))
        pygame.draw.rect(surf, (130, 134, 148), (cx + 2, y - 112, 4, 90))
        pygame.draw.rect(surf, (20, 20, 24), (cx - 13, y - 114, 9, 4))
        pygame.draw.rect(surf, (20, 20, 24), (cx + 4, y - 114, 9, 4))
        pygame.draw.rect(surf, (116, 74, 36), (cx - 20, y - 66 + pump, 40, 20))
        pygame.draw.rect(surf, (70, 44, 20), (cx - 20, y - 66 + pump, 40, 20), 2)
        for i in range(4):
            pygame.draw.line(surf, (70, 44, 20), (cx - 14 + i * 9, y - 64 + pump), (cx - 14 + i * 9, y - 48 + pump))
        if flash:
            _flash_star(surf, cx, y - 120, 44)
    elif wid == 2:
        pygame.draw.polygon(surf, glove, [(cx - 40, by + 30), (cx - 22, y - 20), (cx + 22, y - 20), (cx + 40, by + 30)])
        pygame.draw.rect(surf, (68, 70, 80), (cx - 18, y - 74, 36, 54))
        pygame.draw.rect(surf, (110, 112, 124), (cx - 18, y - 74, 36, 5))
        pygame.draw.rect(surf, (150, 120, 40), (cx + 18, y - 60, 8, 30))
        for k in range(4):
            a = spin + k * math.pi / 2
            bx = cx + math.cos(a) * 10
            shade = 90 + int(50 * math.sin(a))
            pygame.draw.rect(surf, (shade, shade, shade + 8), (bx - 3, y - 118, 6, 48))
        pygame.draw.rect(surf, (28, 28, 34), (cx - 14, y - 120, 28, 5))
        if flash:
            _flash_star(surf, cx, y - 126, 36)
    else:
        pygame.draw.polygon(surf, glove, [(cx - 50, by + 30), (cx - 28, y - 14), (cx + 28, y - 14), (cx + 50, by + 30)])
        pygame.draw.rect(surf, (54, 56, 68), (cx - 28, y - 84, 56, 72))
        pygame.draw.rect(surf, (104, 108, 128), (cx - 28, y - 84, 7, 72))
        pygame.draw.rect(surf, (70, 72, 86), (cx - 15, y - 130, 30, 50))
        pygame.draw.rect(surf, (20, 20, 26), (cx - 11, y - 132, 22, 6))
        col = lerp_col((210, 40, 20), (60, 255, 140), charge)
        for k in range(4):
            lit = charge >= (k + 1) / 4.0 - 1e-6
            pygame.draw.rect(surf, col if lit else (50, 30, 30), (cx - 18, y - 122 + k * 12, 36, 5))
        pygame.draw.circle(surf, col, (cx, y - 58), 11)
        pygame.draw.circle(surf, (255, 255, 255) if charge >= 1.0 else (90, 60, 50), (cx, y - 58), 4)
        if flash:
            _flash_star(surf, cx, y - 138, 72)


# ----------------------------------------------------------------------------
#  NIVEAUX
# ----------------------------------------------------------------------------
class Builder:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [[1] * w for _ in range(h)]
        self.ents = []

    def room(self, x0, y0, x1, y1, wall=None):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.g[y][x] = 0
        if wall:
            for y in range(y0 - 1, y1 + 2):
                for x in range(x0 - 1, x1 + 2):
                    inside = x0 <= x <= x1 and y0 <= y <= y1
                    if not inside and 0 <= x < self.w and 0 <= y < self.h and self.g[y][x] in (1, 2, 3, 4, 5, 8):
                        self.g[y][x] = wall

    def pillar(self, x, y, tex=5):
        self.g[y][x] = tex

    def door(self, x, y):
        self.g[y][x] = 7

    def exit(self, x, y):
        self.g[y][x] = 6

    def at(self, ch, x, y):
        self.ents.append((ch, x + 0.5, y + 0.5))

    def many(self, ch, pts):
        for x, y in pts:
            self.at(ch, x, y)


def level1():
    b = Builder(36, 28)
    b.room(1, 1, 8, 7, 2)
    b.room(10, 1, 24, 9, 2)
    b.room(26, 1, 34, 9, 1)
    b.room(4, 9, 4, 10)
    b.room(1, 11, 20, 20, 2)
    b.room(22, 12, 34, 20, 2)
    for x, y in ((13, 3), (13, 7), (17, 3), (17, 7), (21, 3), (21, 7)):
        b.pillar(x, y, 5)
    for x, y in ((7, 14), (7, 17), (12, 14), (12, 17), (16, 15)):
        b.pillar(x, y, 5)
    b.door(9, 4)
    b.door(25, 5)
    b.door(4, 8)
    b.door(21, 16)
    b.exit(35, 16)
    b.at('P', 3, 4)
    b.at('a', 6, 2)
    b.many('i', [(15, 2), (19, 8), (22, 4), (12, 8)])
    b.many('h', [(11, 2)])
    b.many('a', [(23, 2), (11, 8)])
    b.many('d', [(30, 5)])
    b.many('i', [(32, 8), (28, 2)])
    b.at('s', 33, 8)
    b.at('r', 33, 2)
    b.many('b', [(31, 8), (27, 8)])
    b.many('i', [(6, 14), (10, 18), (15, 13), (17, 19)])
    b.at('d', 18, 16)
    b.many('h', [(2, 19), (20, 12)])
    b.many('a', [(3, 12), (19, 19)])
    b.many('i', [(26, 14), (30, 18), (24, 18)])
    b.at('d', 29, 13)
    b.at('h', 23, 13)
    b.at('a', 23, 19)
    return b


def level2():
    b = Builder(40, 30)
    b.room(1, 1, 6, 6, 1)
    b.room(8, 1, 20, 12, 3)
    b.room(22, 3, 31, 10, 3)
    b.room(14, 14, 14, 17)
    b.room(8, 18, 22, 26, 1)
    b.room(24, 22, 30, 22)
    b.room(31, 19, 37, 25, 3)
    for x, y in ((11, 4), (11, 9), (15, 4), (15, 9), (18, 6), (18, 7)):
        b.pillar(x, y, 5)
    for x, y in ((11, 21), (11, 24), (19, 21), (19, 24), (15, 22)):
        b.pillar(x, y, 5)
    b.door(7, 3)
    b.door(21, 6)
    b.door(14, 13)
    b.door(23, 22)
    b.exit(38, 22)
    b.at('P', 3, 3)
    b.at('s', 5, 5)
    b.at('a', 2, 5)
    b.at('h', 5, 2)
    b.many('i', [(12, 2), (17, 10), (19, 3)])
    b.many('d', [(14, 6), (10, 10)])
    b.many('h', [(9, 11)])
    b.many('a', [(20, 11)])
    b.at('b', 20, 2)
    b.at('c', 27, 6)
    b.many('i', [(24, 4), (29, 9), (25, 9)])
    b.at('g', 30, 4)
    b.at('r', 30, 9)
    b.at('h', 23, 10)
    b.at('c', 15, 24)
    b.many('d', [(10, 19), (20, 20), (12, 25)])
    b.many('i', [(9, 22), (21, 25), (17, 19)])
    b.many('h', [(9, 25)])
    b.at('a', 21, 19)
    b.at('b', 8, 19)
    b.many('d', [(34, 22), (36, 20)])
    b.many('i', [(34, 24)])
    b.at('h', 32, 25)
    return b


def level3():
    b = Builder(34, 24)
    b.room(1, 9, 5, 13, 1)
    b.room(7, 11, 8, 11)
    b.room(10, 3, 30, 19, 3)
    for x, y in ((14, 6), (14, 16), (20, 5), (20, 17), (26, 6), (26, 16), (17, 11), (23, 11)):
        b.pillar(x, y, 5)
    b.door(6, 11)
    b.door(9, 11)
    b.exit(31, 11)
    b.at('P', 3, 11)
    b.many('h', [(2, 10), (2, 12)])
    b.many('a', [(4, 10), (3, 13)])
    b.many('b', [(4, 12), (3, 9)])
    b.at('r', 5, 11)
    b.at('B', 27, 11)
    b.many('c', [(20, 8), (20, 14)])
    b.many('i', [(13, 4), (13, 18), (16, 9), (16, 13)])
    b.many('d', [(24, 6), (24, 16)])
    b.many('h', [(11, 4), (11, 18)])
    b.many('a', [(11, 11), (12, 14)])
    b.many('b', [(12, 8)])
    return b


def level4():
    b = Builder(64, 34)
    b.room(1, 1, 7, 6, 8)
    b.room(9, 1, 22, 10, 1)
    b.room(24, 2, 32, 9, 8)
    b.room(15, 12, 15, 14)
    b.room(8, 15, 24, 24, 3)
    b.room(26, 20, 30, 20)
    b.room(31, 16, 38, 24, 5)
    b.room(40, 8, 60, 26, 3)
    for x, y in ((12, 4), (12, 7), (16, 4), (16, 7), (20, 4), (20, 7)):
        b.pillar(x, y, 5)
    for x, y in ((11, 18), (11, 21), (17, 18), (17, 21), (21, 19), (21, 22)):
        b.pillar(x, y, 8)
    for x, y in ((44, 12), (44, 22), (50, 10), (50, 24), (56, 12), (56, 22), (47, 17), (53, 17)):
        b.pillar(x, y, 5)
    b.door(8, 3)
    b.door(23, 5)
    b.door(15, 11)
    b.door(25, 20)
    b.door(39, 20)
    b.exit(61, 17)
    # salle de départ (début tranquille)
    b.at('P', 3, 3)
    b.many('h', [(6, 2)])
    b.many('a', [(2, 5)])
    b.many('b', [(6, 5)])
    # grand hall
    b.many('i', [(13, 2), (18, 9), (21, 2), (14, 9)])
    b.many('d', [(11, 5), (19, 5)])
    b.many('h', [(10, 2)])
    b.many('a', [(22, 9)])
    b.many('b', [(10, 9)])
    # salle annexe (optionnelle)
    b.many('d', [(27, 4), (30, 7), (26, 8)])
    b.at('c', 30, 4)
    b.at('r', 32, 9)
    b.at('h', 24, 2)
    b.at('a', 32, 2)
    # salle basse
    b.many('c', [(14, 18), (19, 24)])
    b.many('i', [(9, 17), (23, 17), (10, 23), (15, 22)])
    b.many('d', [(13, 20), (22, 21)])
    b.at('g', 9, 24)
    b.at('h', 24, 24)
    b.at('a', 24, 15)
    b.at('b', 8, 15)
    b.at('r', 16, 24)
    # armurerie : l'ANNIHILATEUR
    b.at('x', 35, 20)
    b.many('h', [(32, 17), (32, 23)])
    b.at('r', 37, 17)
    b.at('a', 37, 23)
    b.at('b', 35, 17)
    b.many('i', [(34, 18), (36, 22)])
    b.at('d', 35, 24)
    # arène du boss
    b.at('T', 56, 17)
    b.many('c', [(48, 13), (48, 21)])
    b.many('i', [(42, 12), (42, 22), (58, 10), (58, 24)])
    b.many('d', [(45, 17), (52, 9)])
    b.many('h', [(41, 9), (41, 25), (59, 17)])
    b.at('a', 42, 17)
    b.at('b', 43, 10)
    b.at('r', 41, 17)
    return b


LEVELS = [
    dict(name=('HANGAR 7', 'HANGAR 7'), build=level1, fog=(12, 20, 34), ceil=(3, 5, 10), floor=(30, 34, 44), flicker=False, boss=False),
    dict(name=('CATACOMBES', 'CATACOMBS'), build=level2, fog=(38, 8, 10), ceil=(6, 1, 2), floor=(58, 20, 16), flicker=True, boss=False),
    dict(name=('SANCTUAIRE DU BARON', "BARON'S SANCTUM"), build=level3, fog=(40, 6, 30), ceil=(8, 0, 6), floor=(66, 14, 30), flicker=True, boss=True),
    dict(name=('FORGE INFERNALE', 'HELLFORGE'), build=level4, fog=(44, 20, 4), ceil=(12, 5, 0), floor=(74, 36, 10), flicker=True, boss=True),
]


class Level:
    def __init__(self, meta):
        b = meta['build']()
        self.meta = meta
        self.name = meta['name']
        self.grid = b.g
        self.w = b.w
        self.h = b.h
        self.ents = b.ents
        self.doors = {}

    def solid(self, mx, my):
        if mx < 0 or my < 0 or mx >= self.w or my >= self.h:
            return True
        t = self.grid[my][mx]
        if t == 0:
            return False
        if t == 7:
            return self.doors.get((mx, my), 0.0) < 0.7
        return True

    def cast(self, px, py, rdx, rdy):
        """DDA. Renvoie (distance, texture, côté, position sur le mur, case x, case y)."""
        mx = int(px)
        my = int(py)
        ddx = abs(1.0 / rdx) if rdx else 1e30
        ddy = abs(1.0 / rdy) if rdy else 1e30
        if rdx < 0:
            stx = -1
            sdx = (px - mx) * ddx
        else:
            stx = 1
            sdx = (mx + 1.0 - px) * ddx
        if rdy < 0:
            sty = -1
            sdy = (py - my) * ddy
        else:
            sty = 1
            sdy = (my + 1.0 - py) * ddy
        grid = self.grid
        w = self.w
        h = self.h
        doors = self.doors
        while True:
            if sdx < sdy:
                side = 0
                mx += stx
                dist = sdx
                sdx += ddx
            else:
                side = 1
                my += sty
                dist = sdy
                sdy += ddy
            if mx < 0 or my < 0 or mx >= w or my >= h:
                return dist, 1, side, 0.0, mx, my
            t = grid[my][mx]
            if t:
                if side == 0:
                    wx = py + dist * rdy
                else:
                    wx = px + dist * rdx
                wx -= math.floor(wx)
                if t == 7:
                    pr = doors.get((mx, my))
                    if pr:
                        wx -= pr
                        if wx < 0:
                            continue
                return dist, t, side, wx, mx, my

    def los(self, x0, y0, x1, y1):
        dx = x1 - x0
        dy = y1 - y0
        d = math.hypot(dx, dy)
        if d < 0.01:
            return True
        return self.cast(x0, y0, dx / d, dy / d)[0] >= d


# ----------------------------------------------------------------------------
#  ENTITES
# ----------------------------------------------------------------------------
WEAPONS = [
    dict(name=('PISTOLET', 'PISTOL'), ammo='bullets', cool=0.30, pellets=1, spread=0.010, dmg=(14, 20), snd='pistol', kick=0.6),
    dict(name=('FUSIL À POMPE', 'SHOTGUN'), ammo='shells', cool=0.85, pellets=8, spread=0.075, dmg=(8, 13), snd='shotgun', kick=1.0),
    dict(name=('MITRAILLEUSE', 'CHAINGUN'), ammo='bullets', cool=0.085, pellets=1, spread=0.040, dmg=(9, 14), snd='chain', kick=0.3),
    dict(name=('ANNIHILATEUR', 'ANNIHILATOR'), ammo=None, cool=0.8, pellets=1, spread=0.0, dmg=(900, 1100), snd='cannon', kick=1.8),
]
CANNON_RELOAD = 25.0     # secondes de rechargement de l'ANNIHILATEUR
CANNON_SPLASH = 2.6      # rayon de l'explosion
AMMO_MAX = {'bullets': 200, 'shells': 50}

ENEMIES = {
    'imp':   dict(hp=60,  speed=1.9, radius=0.30, scale=0.95, lift=0.0,  ranged=True,  rdmg=(8, 14),  proj='fire',   pspeed=5.0, range=12, melee=(8, 15),  mrange=1.0,  windup=0.45, cool=(1.0, 2.2), pain=0.55, mind=2.5),
    'demon': dict(hp=130, speed=3.5, radius=0.38, scale=1.05, lift=0.0,  ranged=False, rdmg=(0, 0),   proj=None,     pspeed=0.0, range=0,  melee=(14, 24), mrange=1.05, windup=0.35, cool=(0.6, 1.0), pain=0.35, mind=0.8),
    'caco':  dict(hp=240, speed=1.2, radius=0.42, scale=1.15, lift=0.18, ranged=True,  rdmg=(14, 24), proj='plasma', pspeed=5.5, range=14, melee=(18, 28), mrange=1.2,  windup=0.55, cool=(1.4, 2.6), pain=0.30, mind=3.5),
    'baron': dict(hp=900, speed=1.6, radius=0.50, scale=1.55, lift=0.0,  ranged=True,  rdmg=(18, 28), proj='plasma', pspeed=6.0, range=16, melee=(30, 45), mrange=1.5,  windup=0.60, cool=(1.0, 1.8), pain=0.06, mind=3.0, shots=2, boss=True),
    'titan': dict(hp=3000, speed=1.7, radius=0.60, scale=1.95, lift=0.0, ranged=True, rdmg=(25, 40), proj='plasma', pspeed=6.5, range=18, melee=(40, 60), mrange=1.8, windup=0.55, cool=(0.9, 1.6), pain=0.0, mind=3.5, shots=3, boss=True),
}
CHAR_TO_ENEMY = {'i': 'imp', 'd': 'demon', 'c': 'caco', 'B': 'baron', 'T': 'titan'}
BOSS_NAMES = {'baron': ("BARON DE L'ENFER", 'BARON OF HELL'), 'titan': ("SEIGNEUR DE L'ABÎME", 'ABYSS LORD')}


class Player:
    def __init__(self):
        self.x = self.y = 2.5
        self.angle = 0.0
        self.health = 100
        self.armor = 0.0
        self.ammo = {'bullets': 50, 'shells': 0}
        self.has = [True, False, False, False]
        self.weapon = 0
        self.cool = 0.0
        self.kick = 0.0
        self.flash = 0.0
        self.bob = 0.0
        self.spin = 0.0
        self.spin_v = 0.0
        self.hurt = 0.0
        self.pick = 0.0
        self.cannon_cd = 0.0


class Enemy:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.st = ENEMIES[kind]
        self.x = x
        self.y = y
        self.hp = self.st['hp']
        self.maxhp = self.st['hp']
        self.state = 'idle'
        self.t = 0.0
        self.cool = random.uniform(0.5, 1.5)
        self.anim = 0.0
        self.seen = False
        self.fired = False
        self.akind = 'melee'
        self.side = random.choice((-1, 1))

    def image(self, frames):
        f = frames[self.kind]
        if self.state == 'dead':
            return f['dead'][min(2, int(self.t / 0.2))]
        if self.state == 'pain':
            return f['pain'][0]
        if self.state == 'attack':
            return f['attack'][0]
        return f['walk'][int(self.anim) % 2]

    def damage(self, g, dmg):
        if self.state == 'dead':
            return
        self.hp -= dmg
        g.fx(self.x, self.y, 0.4, 'blood')
        d = math.hypot(self.x - g.p.x, self.y - g.p.y)
        if self.hp <= 0:
            self.state = 'dead'
            self.t = 0.0
            g.kills += 1
            g.snd.play('death', d)
        else:
            if self.state == 'idle':
                self.state = 'chase'
            if random.random() < self.st['pain']:
                self.state = 'pain'
                self.t = 0.3
                g.snd.play('pain', d)

    def begin_attack(self, kind):
        self.state = 'attack'
        self.t = self.st['windup']
        self.fired = False
        self.akind = kind

    def do_attack(self, g, d):
        st = self.st
        p = g.p
        if self.akind == 'melee':
            if d < st['mrange'] + 0.6:
                g.snd.play('claw', d)
                g.hurt_player(random.randint(*st['melee']))
            return
        ang = math.atan2(p.y - self.y, p.x - self.x)
        n = st.get('shots', 1)
        angs = [ang + (k - (n - 1) / 2.0) * 0.2 + random.uniform(-0.03, 0.03) for k in range(n)]
        for a in angs:
            g.projectiles.append(Projectile(self.x + math.cos(a) * 0.5, self.y + math.sin(a) * 0.5,
                                            a, st['pspeed'], random.randint(*st['rdmg']), st['proj']))
        g.snd.play('fire', d)

    def step(self, g, ang, dist):
        s = self.side
        for off in (0.0, s * 0.55, -s * 0.55, s * 1.1, -s * 1.1, s * 1.7):
            a = ang + off
            nx = self.x + math.cos(a) * dist
            ny = self.y + math.sin(a) * dist
            r = self.st['radius']
            if g.can_stand(nx, ny, r, self):
                self.x, self.y = nx, ny
                return True
            if g.can_stand(nx, self.y, r, self):
                self.x = nx
                return True
            if g.can_stand(self.x, ny, r, self):
                self.y = ny
                return True
        self.side = -self.side
        return False

    def update(self, g, dt):
        st = self.st
        p = g.p
        if self.state == 'dead':
            self.t += dt
            return
        dx = p.x - self.x
        dy = p.y - self.y
        d = math.hypot(dx, dy)
        self.cool -= dt
        self.seen = d < 20 and g.lv.los(self.x, self.y, p.x, p.y)
        if self.state == 'idle':
            if (self.seen and d < 14) or (g.noise_t > 0 and d < 9):
                self.state = 'chase'
                g.snd.play('growl', d)
            return
        if self.state == 'pain':
            self.t -= dt
            if self.t <= 0:
                self.state = 'chase'
            return
        if self.state == 'attack':
            self.t -= dt
            if not self.fired and self.t <= st['windup'] * 0.35:
                self.fired = True
                self.do_attack(g, d)
            if self.t <= 0:
                self.state = 'chase'
                self.cool = random.uniform(*st['cool'])
            return
        # poursuite
        self.anim += dt * 4.0
        ang = math.atan2(dy, dx)
        if self.cool <= 0:
            if d < st['mrange']:
                self.begin_attack('melee')
                return
            if st['ranged'] and self.seen and d < st['range'] and random.random() < 0.08:
                self.begin_attack('ranged')
                return
        if d > st['mind'] or not self.seen:
            spd = st['speed'] * (1.5 if st.get('boss') and self.hp < self.maxhp * 0.5 else 1.0)
            self.step(g, ang, spd * dt)


class Projectile:
    def __init__(self, x, y, ang, speed, dmg, kind):
        self.x = x
        self.y = y
        self.dx = math.cos(ang)
        self.dy = math.sin(ang)
        self.speed = speed
        self.dmg = dmg
        self.kind = kind
        self.alive = True
        self.life = 6.0

    def update(self, g, dt):
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt
        self.life -= dt
        hit = False
        if g.lv.solid(int(self.x), int(self.y)) or self.life <= 0:
            hit = True
        elif math.hypot(self.x - g.p.x, self.y - g.p.y) < 0.35:
            g.hurt_player(self.dmg)
            hit = True
        if hit:
            self.alive = False
            g.fx(self.x, self.y, 0.25, 'boom')
            g.snd.play('boom', math.hypot(self.x - g.p.x, self.y - g.p.y))


class Effect:
    TTL = {'spark': 0.12, 'blood': 0.25, 'boom': 0.30}
    SCALE = {'spark': 0.12, 'blood': 0.25, 'boom': 0.65}

    def __init__(self, x, y, lift, kind):
        self.x, self.y, self.lift, self.kind = x, y, lift, kind
        self.t = self.TTL[kind]
        self.alive = True


class Pickup:
    def __init__(self, kind, x, y):
        self.kind, self.x, self.y = kind, x, y
        self.taken = False


# ----------------------------------------------------------------------------
#  JEU
# ----------------------------------------------------------------------------
class Game:
    def __init__(self):
        load_lang()
        self.snd = Sounds()
        pygame.init()
        pygame.display.set_caption("HELLEGATE 64")
        self.screen = pygame.display.set_mode((W * 2, H * 2), pygame.RESIZABLE)
        self.canvas = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.f_title = pygame.font.Font(None, 84)
        self.f_big = pygame.font.Font(None, 34)
        self.f_num = pygame.font.Font(None, 30)
        self.f_mid = pygame.font.Font(None, 22)
        self.f_lab = pygame.font.Font(None, 14)
        self.base_tex = make_textures()
        self.frames = {k: make_enemy_frames(k) for k in ('imp', 'demon', 'caco', 'baron', 'titan')}
        self.fxart = make_fx()
        self.pickart = make_pickups()
        self.zbuf = [0.0] * RAYS
        self.state = 'lang'
        self.lang_sel = 0 if LANG == 'fr' else 1
        self.lang_rects = [pygame.Rect(W // 2 - 130, 136, 260, 40), pygame.Rect(W // 2 - 130, 188, 260, 40)]
        self.p = Player()
        self.lvl_idx = 0
        self.lv = None
        self.enemies = []
        self.pickups = []
        self.projectiles = []
        self.effects = []
        self.kills = 0
        self.total_enemies = 0
        self.noise_t = 0.0
        self.msg_text = ''
        self.msg_t = 0.0
        self.intro_t = 0.0
        self.level_time = 0.0
        self.dead_t = 0.0
        self.show_map = False
        self.flick = 0
        self.flick_t = 0.0
        self.snap = None
        self.title_bg = self._make_title_bg()
        self.light_t = 0.0
        self.set_mouse(False)
        self.snd.start_drone()

    # ---------- utilitaires ----------
    def _make_title_bg(self):
        s = pygame.Surface((W, H))
        for y in range(H):
            t = y / H
            pygame.draw.line(s, lerp_col((6, 0, 2), (60, 6, 8), t ** 1.6), (0, y), (W, y))
        return s

    def set_mouse(self, play):
        pygame.mouse.set_visible(not play)
        pygame.event.set_grab(play)
        pygame.mouse.get_rel()

    def lname(self):
        return L2(self.lv.name)

    def choose_lang(self, idx):
        global LANG
        LANG = 'fr' if idx == 0 else 'en'
        self.lang_sel = idx
        save_lang()
        if self.state == 'lang':
            self.state = 'title'

    def canvas_mouse(self):
        mx, my = pygame.mouse.get_pos()
        sw, sh = self.screen.get_size()
        sc = min(sw / W, sh / H)
        return (mx - (sw - W * sc) / 2) / sc, (my - (sh - H * sc) / 2) / sc

    def message(self, text):
        self.msg_text = text
        self.msg_t = 2.5

    def fx(self, x, y, lift, kind):
        self.effects.append(Effect(x, y, lift, kind))

    def draw_text(self, surf, text, font, color, pos, center=False, shadow=True):
        img = font.render(text, True, color)
        x, y = pos
        if center:
            x -= img.get_width() // 2
        if shadow:
            surf.blit(font.render(text, True, (0, 0, 0)), (x + 1, y + 1))
        surf.blit(img, (x, y))

    # ---------- niveaux ----------
    def new_game(self):
        self.p = Player()
        self.lvl_idx = 0
        self.start_level()

    def start_level(self):
        p = self.p
        self.snap = (p.health, p.armor, dict(p.ammo), list(p.has), p.weapon)
        self.load_level()

    def restart_level(self):
        h, a, am, has, w = self.snap
        p = self.p = Player()
        p.health = max(h, 50)
        p.armor = a
        p.ammo = dict(am)
        p.has = list(has)
        p.weapon = w
        self.load_level()

    def load_level(self):
        meta = LEVELS[self.lvl_idx]
        self.lv = Level(meta)
        self.cols = build_columns(self.base_tex, meta['fog'])
        self.bg = build_bg(meta)
        self.enemies, self.pickups, self.projectiles, self.effects = [], [], [], []
        p = self.p
        for ch, x, y in self.lv.ents:
            if ch == 'P':
                p.x, p.y = x, y
            elif ch in CHAR_TO_ENEMY:
                self.enemies.append(Enemy(CHAR_TO_ENEMY[ch], x, y))
            else:
                self.pickups.append(Pickup(ch, x, y))
        p.angle = 0.0
        p.cool = p.kick = p.flash = p.hurt = p.pick = 0.0
        p.cannon_cd = 0.0
        self.kills = 0
        self.total_enemies = len(self.enemies)
        self.noise_t = 0.0
        self.intro_t = 3.0
        self.level_time = 0.0
        self.state = 'play'
        self.set_mouse(True)

    # ---------- collisions ----------
    def can_stand(self, x, y, r, me=None):
        lv = self.lv
        if (lv.solid(int(x - r), int(y - r)) or lv.solid(int(x + r), int(y - r)) or
                lv.solid(int(x - r), int(y + r)) or lv.solid(int(x + r), int(y + r))):
            return False
        for e in self.enemies:
            if e is me or e.state == 'dead':
                continue
            rr = r + e.st['radius']
            if (e.x - x) ** 2 + (e.y - y) ** 2 < rr * rr * 0.8:
                return False
        if me is not None:
            rr = r + 0.25
            if (self.p.x - x) ** 2 + (self.p.y - y) ** 2 < rr * rr:
                return False
        return True

    def move_player(self, dx, dy):
        p = self.p
        if self.can_stand(p.x + dx, p.y, 0.22):
            p.x += dx
        if self.can_stand(p.x, p.y + dy, 0.22):
            p.y += dy

    # ---------- combat ----------
    def hurt_player(self, dmg):
        p = self.p
        if self.state != 'play' or p.health <= 0:
            return
        absorbed = min(p.armor, dmg * 0.5)
        p.armor -= absorbed
        dmg = int(dmg - absorbed)
        p.health -= dmg
        p.hurt = min(0.7, 0.2 + dmg / 50.0)
        self.snd.play('hurt')
        if p.health <= 0:
            p.health = 0
            self.state = 'dead'
            self.dead_t = 0.0
            self.set_mouse(False)

    def hitscan(self, w):
        p = self.p
        ang = p.angle + random.uniform(-w['spread'], w['spread'])
        dx, dy = math.cos(ang), math.sin(ang)
        wall_d = self.lv.cast(p.x, p.y, dx, dy)[0]
        best = None
        bd = wall_d
        for e in self.enemies:
            if e.state == 'dead':
                continue
            ex, ey = e.x - p.x, e.y - p.y
            proj = ex * dx + ey * dy
            if proj <= 0 or proj > bd:
                continue
            perp = abs(ex * dy - ey * dx)
            if perp < e.st['radius'] + 0.12:
                best, bd = e, proj
        if best:
            best.damage(self, random.randint(*w['dmg']))
        else:
            self.fx(p.x + dx * (wall_d - 0.05), p.y + dy * (wall_d - 0.05), 0.5, 'spark')

    def auto_switch(self):
        p = self.p
        for i in (2, 1, 0):
            if p.has[i] and p.ammo[WEAPONS[i]['ammo']] > 0:
                p.weapon = i
                return

    def fire(self):
        p = self.p
        w = WEAPONS[p.weapon]
        if p.weapon == 3:
            self.fire_cannon()
            return
        if p.ammo[w['ammo']] <= 0:
            self.snd.play('click')
            p.cool = 0.25
            self.auto_switch()
            return
        p.ammo[w['ammo']] -= 1
        p.cool = w['cool']
        p.kick = w['kick']
        p.flash = 0.10 if p.weapon == 1 else 0.07
        self.noise_t = 0.6
        self.snd.play(w['snd'])
        for _ in range(w['pellets']):
            self.hitscan(w)
        if p.ammo[w['ammo']] <= 0:
            self.auto_switch()

    def fire_cannon(self):
        p = self.p
        if p.cannon_cd > 0:
            self.snd.play('click', vol=0.5)
            p.cool = 0.5
            return
        w = WEAPONS[3]
        p.cannon_cd = CANNON_RELOAD
        p.cool = 0.8
        p.kick = w['kick']
        p.flash = 0.25
        self.noise_t = 1.0
        self.snd.play('cannon')
        dx, dy = math.cos(p.angle), math.sin(p.angle)
        wall_d = self.lv.cast(p.x, p.y, dx, dy)[0]
        best, bd = None, wall_d
        for e in self.enemies:
            if e.state == 'dead':
                continue
            ex, ey = e.x - p.x, e.y - p.y
            proj = ex * dx + ey * dy
            if proj <= 0 or proj > bd:
                continue
            if abs(ex * dy - ey * dx) < e.st['radius'] + 0.3:
                best, bd = e, proj
        ix, iy = p.x + dx * (bd - 0.1), p.y + dy * (bd - 0.1)
        if best:
            best.damage(self, random.randint(*w['dmg']))
        for e in self.enemies:
            if e.state != 'dead' and e is not best and math.hypot(e.x - ix, e.y - iy) < CANNON_SPLASH:
                e.damage(self, 400)
        for k in range(1, int(min(bd, 14) * 2)):
            self.fx(p.x + dx * k * 0.5, p.y + dy * k * 0.5, 0.5, 'spark')
        for _ in range(6):
            self.fx(ix + random.uniform(-0.6, 0.6), iy + random.uniform(-0.6, 0.6), random.uniform(0.1, 0.7), 'boom')

    def use(self):
        p = self.p
        dist, t, side, wx, mx, my = self.lv.cast(p.x, p.y, math.cos(p.angle), math.sin(p.angle))
        if dist > 1.6:
            return
        if t == 7 and (mx, my) not in self.lv.doors:
            self.lv.doors[(mx, my)] = 0.001
            self.snd.play('door')
        elif t == 6:
            if self.lv.meta['boss'] and any(e.st.get('boss') and e.state != 'dead' for e in self.enemies):
                self.message(tr('boss_guard'))
            else:
                self.state = 'levelend'
                self.set_mouse(False)

    def give(self, pk):
        p = self.p
        k = pk.kind
        if k == 'h':
            if p.health >= 100:
                return False
            p.health = min(100, p.health + 25)
            self.message(tr('m_health'))
        elif k == 'r':
            if p.armor >= 100:
                return False
            p.armor = min(100, p.armor + 50)
            self.message(tr('m_armor'))
        elif k == 'a':
            if p.ammo['bullets'] >= AMMO_MAX['bullets']:
                return False
            p.ammo['bullets'] = min(AMMO_MAX['bullets'], p.ammo['bullets'] + 20)
            self.message(tr('m_bullets'))
        elif k == 'b':
            if p.ammo['shells'] >= AMMO_MAX['shells']:
                return False
            p.ammo['shells'] = min(AMMO_MAX['shells'], p.ammo['shells'] + 8)
            self.message(tr('m_shells'))
        elif k == 's':
            if not p.has[1]:
                p.weapon = 1
            p.has[1] = True
            p.ammo['shells'] = min(AMMO_MAX['shells'], p.ammo['shells'] + 8)
            self.message(tr('m_shotgun'))
        elif k == 'g':
            if not p.has[2]:
                p.weapon = 2
            p.has[2] = True
            p.ammo['bullets'] = min(AMMO_MAX['bullets'], p.ammo['bullets'] + 40)
            self.message(tr('m_chain'))
        elif k == 'x':
            if not p.has[3]:
                p.weapon = 3
            p.has[3] = True
            self.message(tr('m_cannon'))
        return True

    # ---------- mise à jour ----------
    def update_play(self, dt):
        p = self.p
        lv = self.lv
        keys = pygame.key.get_pressed()
        mx, _ = pygame.mouse.get_rel()
        p.angle += mx * MOUSE_SENS
        if keys[pygame.K_LEFT]:
            p.angle -= 2.5 * dt
        if keys[pygame.K_RIGHT]:
            p.angle += 2.5 * dt
        ca, sa = math.cos(p.angle), math.sin(p.angle)
        fx = fy = 0.0
        if keys[pygame.K_w] or keys[pygame.K_z] or keys[pygame.K_UP]:
            fx += ca
            fy += sa
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            fx -= ca
            fy -= sa
        if keys[pygame.K_d]:
            fx -= sa
            fy += ca
        if keys[pygame.K_a] or keys[pygame.K_q]:
            fx += sa
            fy -= ca
        moving = fx != 0 or fy != 0
        if moving:
            n = math.hypot(fx, fy)
            speed = 5.4 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else 3.7
            self.move_player(fx / n * speed * dt, fy / n * speed * dt)
            p.bob += dt * speed * 2.0
        # tir
        p.cool -= dt
        p.kick = max(0.0, p.kick - dt * 5.0)
        p.flash = max(0.0, p.flash - dt)
        p.hurt = max(0.0, p.hurt - dt)
        p.pick = max(0.0, p.pick - dt)
        if p.cannon_cd > 0:
            p.cannon_cd -= dt
            if p.cannon_cd <= 0:
                p.cannon_cd = 0.0
                if p.has[3]:
                    self.snd.play('ready')
                    self.message(tr('m_ready'))
        firing = pygame.mouse.get_pressed()[0] or keys[pygame.K_SPACE]
        if firing and p.cool <= 0:
            self.fire()
        target = 22.0 if (firing and p.weapon == 2 and p.ammo['bullets'] > 0) else 0.0
        p.spin_v += (target - p.spin_v) * min(1.0, dt * 8)
        p.spin += p.spin_v * dt
        self.noise_t = max(0.0, self.noise_t - dt)
        self.msg_t = max(0.0, self.msg_t - dt)
        self.intro_t = max(0.0, self.intro_t - dt)
        self.level_time += dt
        # portes
        for k in list(lv.doors.keys()):
            lv.doors[k] += dt * 0.9
            if lv.doors[k] >= 1.0:
                lv.grid[k[1]][k[0]] = 0
                del lv.doors[k]
        # objets
        for pk in self.pickups:
            if not pk.taken and (pk.x - p.x) ** 2 + (pk.y - p.y) ** 2 < 0.45:
                if self.give(pk):
                    pk.taken = True
                    p.pick = 0.25
                    self.snd.play('pickup')
        self.update_world(dt)
        # lumière qui vacille
        if lv.meta['flicker']:
            self.flick_t -= dt
            if self.flick_t <= 0:
                self.flick_t = random.uniform(0.05, 0.25)
                self.flick = random.choice((0, 0, 0, 0, 1, 2, 3))

    def update_world(self, dt):
        for e in self.enemies:
            e.update(self, dt)
        for pr in self.projectiles:
            pr.update(self, dt)
        self.projectiles = [pr for pr in self.projectiles if pr.alive]
        for ef in self.effects:
            ef.t -= dt
        self.effects = [ef for ef in self.effects if ef.t > 0]

    # ---------- rendu 3D ----------
    def render_walls(self):
        p = self.p
        lv = self.lv
        canvas = self.canvas
        cols = self.cols
        zbuf = self.zbuf
        dirx, diry = math.cos(p.angle), math.sin(p.angle)
        plx, ply = -diry * PLANE, dirx * PLANE
        boost = 3 if p.flash > 0 else 0
        boost += 1 if p.pick > 0 else 0
        base_off = self.flick - boost
        cast = lv.cast
        scale = pygame.transform.scale
        blit = canvas.blit
        px, py = p.x, p.y
        smax = SHADES - 1
        for i in range(RAYS):
            cx = 2.0 * i / RAYS - 1.0
            rdx = dirx + plx * cx
            rdy = diry + ply * cx
            dist, t, side, wx, mx, my = cast(px, py, rdx, rdy)
            zbuf[i] = dist
            if dist < 0.05:
                dist = 0.05
            line_h = int(H / dist)
            if line_h < 1:
                line_h = 1
            tx = int(wx * 64)
            if tx > 63:
                tx = 63
            if (side == 0 and rdx > 0) or (side == 1 and rdy < 0):
                tx = 63 - tx
            sh = int(dist * 1.15) + side * 2 + base_off
            sh = 0 if sh < 0 else smax if sh > smax else sh
            col = cols[t][sh][tx]
            if line_h <= H:
                blit(scale(col, (COLW, line_h)), (i * COLW, HALF_H - line_h // 2))
            else:
                rows = max(1, int(64 * H / line_h))
                r0 = (64 - rows) // 2
                blit(scale(col.subsurface((0, r0, 1, rows)), (COLW, H)), (i * COLW, 0))

    def collect_sprites(self):
        out = []
        for e in self.enemies:
            lift = 0.0 if e.state == 'dead' else e.st['lift']
            out.append((e.x, e.y, e.image(self.frames), e.st['scale'], lift, False))
        for pk in self.pickups:
            if not pk.taken:
                out.append((pk.x, pk.y, self.pickart[pk.kind], 0.42, 0.0, False))
        for pr in self.projectiles:
            out.append((pr.x, pr.y, self.fxart[pr.kind], 0.30, 0.35, True))
        for ef in self.effects:
            out.append((ef.x, ef.y, self.fxart[ef.kind], Effect.SCALE[ef.kind], ef.lift, True))
        return out

    def render_sprites(self):
        p = self.p
        canvas = self.canvas
        zbuf = self.zbuf
        dirx, diry = math.cos(p.angle), math.sin(p.angle)
        plx, ply = -diry * PLANE, dirx * PLANE
        inv = 1.0 / (plx * diry - dirx * ply)
        items = []
        for (x, y, img, sc, lift, lit) in self.collect_sprites():
            sx = x - p.x
            sy = y - p.y
            tx = inv * (diry * sx - dirx * sy)
            ty = inv * (-ply * sx + plx * sy)
            if ty < 0.15:
                continue
            items.append((ty, tx, img, sc, lift, lit))
        items.sort(key=lambda it: -it[0])
        boost = 0.25 if p.flash > 0 else 0.0
        for ty, tx, img, sc, lift, lit in items:
            screen_x = int(W / 2 * (1 + tx / ty))
            unit = H / ty
            size = int(unit * sc)
            if size < 2:
                continue
            if size > 800:
                size = 800
            left = screen_x - size // 2
            if left >= W or left + size <= 0:
                continue
            floor_y = HALF_H + int(unit / 2)
            top = floor_y - int(lift * unit) - size
            scaled = pygame.transform.scale(img, (size, size))
            if not lit:
                b = int(255 * clamp(1.1 - ty / 14.0 + boost + (0.0 if not self.lv.meta['flicker'] else -0.05 * self.flick), 0.22, 1.0))
                scaled.fill((b, b, b, 255), special_flags=pygame.BLEND_RGBA_MULT)
            i0 = max(0, left) // COLW
            i1 = min(W - 1, left + size - 1) // COLW
            for i in range(i0, i1 + 1):
                if ty < zbuf[i]:
                    sx0 = i * COLW
                    dest_x = max(sx0, left)
                    srcx = dest_x - left
                    wid = min(COLW - (dest_x - sx0), size - srcx)
                    if wid > 0:
                        canvas.blit(scaled, (dest_x, top), (srcx, 0, wid, size))

    def draw_world(self):
        self.canvas.blit(self.bg, (0, 0))
        self.render_walls()
        self.render_sprites()

    # ---------- HUD ----------
    def draw_face(self, x, y):
        c = self.canvas
        hp = self.p.health
        pygame.draw.rect(c, (20, 18, 22), (x - 2, y - 2, 36, 34))
        skin = lerp_col((120, 40, 36), (214, 160, 120), hp / 100.0)
        pygame.draw.ellipse(c, skin, (x, y, 32, 30))
        pygame.draw.ellipse(c, (60, 30, 20), (x, y, 32, 30), 1)
        if hp <= 0:
            for ex in (x + 9, x + 22):
                pygame.draw.line(c, (0, 0, 0), (ex - 3, y + 8), (ex + 3, y + 14), 2)
                pygame.draw.line(c, (0, 0, 0), (ex - 3, y + 14), (ex + 3, y + 8), 2)
        else:
            pygame.draw.rect(c, (250, 250, 250), (x + 6, y + 9, 7, 4))
            pygame.draw.rect(c, (250, 250, 250), (x + 19, y + 9, 7, 4))
            pygame.draw.rect(c, (20, 20, 20), (x + 9, y + 9, 3, 4))
            pygame.draw.rect(c, (20, 20, 20), (x + 20, y + 9, 3, 4))
            pygame.draw.line(c, (60, 20, 20), (x + 5, y + 6), (x + 13, y + 7), 2)
            pygame.draw.line(c, (60, 20, 20), (x + 19, y + 7), (x + 27, y + 6), 2)
            if self.p.hurt > 0 or hp < 35:
                pygame.draw.ellipse(c, (30, 0, 0), (x + 11, y + 19, 10, 7))
            else:
                pygame.draw.line(c, (70, 20, 20), (x + 11, y + 22), (x + 21, y + 22), 2)
        if hp < 70 and hp > 0:
            pygame.draw.line(c, (170, 0, 0), (x + 4, y + 18), (x + 8, y + 26), 1)
        if hp < 40 and hp > 0:
            pygame.draw.line(c, (170, 0, 0), (x + 24, y + 4), (x + 28, y + 14), 2)

    def draw_hud(self):
        c = self.canvas
        p = self.p
        y0 = H - HUD_H
        pygame.draw.rect(c, (36, 33, 38), (0, y0, W, HUD_H))
        pygame.draw.rect(c, (92, 86, 96), (0, y0, W, 2))
        pygame.draw.rect(c, (12, 10, 14), (0, y0 + 2, W, 2))
        w = WEAPONS[p.weapon]
        self.draw_text(c, tr('ammo'), self.f_lab, (170, 160, 150), (14, y0 + 6))
        if w['ammo'] is None:
            if p.cannon_cd > 0:
                self.draw_text(c, "%d s" % math.ceil(p.cannon_cd), self.f_num, (255, 90, 60), (14, y0 + 16))
            else:
                self.draw_text(c, tr('ready'), self.f_num, (90, 255, 150), (14, y0 + 16))
        else:
            self.draw_text(c, str(p.ammo[w['ammo']]), self.f_num, (255, 200, 60), (14, y0 + 16))
        self.draw_text(c, L2(w['name']), self.f_lab, (150, 150, 150), (84, y0 + 6))
        hcol = (255, 80, 60) if p.health < 35 else (240, 220, 200)
        self.draw_text(c, tr('health'), self.f_lab, (170, 160, 150), (170, y0 + 6))
        self.draw_text(c, "%d%%" % p.health, self.f_num, hcol, (170, y0 + 16))
        self.draw_face(W // 2 - 16, y0 + 5)
        self.draw_text(c, tr('armor'), self.f_lab, (170, 160, 150), (W // 2 + 50, y0 + 6))
        self.draw_text(c, "%d%%" % int(p.armor), self.f_num, (110, 160, 255), (W // 2 + 50, y0 + 16))
        for i in range(4):
            bx = W - 156 + i * 38
            have = p.has[i]
            col = (255, 200, 60) if i == p.weapon else (130, 130, 130) if have else (60, 58, 62)
            pygame.draw.rect(c, (24, 22, 26), (bx, y0 + 8, 32, 26))
            pygame.draw.rect(c, col, (bx, y0 + 8, 32, 26), 2)
            self.draw_text(c, str(i + 1), self.f_big, col, (bx + 16, y0 + 12), center=True)
        if p.has[3]:
            fr = 1.0 - p.cannon_cd / CANNON_RELOAD
            pygame.draw.rect(c, (200, 60, 30) if fr < 1.0 else (60, 255, 140), (W - 156 + 3 * 38, y0 + 36, int(32 * fr), 3))

    def draw_minimap(self):
        lv = self.lv
        c = self.canvas
        s = 4
        ox, oy = 8, 8
        pygame.draw.rect(c, (0, 0, 0), (ox - 2, oy - 2, lv.w * s + 4, lv.h * s + 4))
        for y in range(lv.h):
            for x in range(lv.w):
                t = lv.grid[y][x]
                if t:
                    col = (200, 200, 60) if t == 7 else (80, 255, 120) if t == 6 else (90, 90, 110)
                    pygame.draw.rect(c, col, (ox + x * s, oy + y * s, s, s))
        for e in self.enemies:
            if e.state != 'dead' and e.seen:
                pygame.draw.rect(c, (255, 40, 40), (ox + int(e.x * s) - 1, oy + int(e.y * s) - 1, 3, 3))
        p = self.p
        px, py = ox + p.x * s, oy + p.y * s
        pygame.draw.circle(c, (80, 255, 80), (int(px), int(py)), 2)
        pygame.draw.line(c, (80, 255, 80), (px, py), (px + math.cos(p.angle) * 6, py + math.sin(p.angle) * 6))

    def draw_play(self):
        c = self.canvas
        p = self.p
        self.draw_world()
        bx = math.sin(p.bob) * 7
        by = abs(math.cos(p.bob)) * 5
        if self.state != 'dead':
            draw_weapon(c, p.weapon, W // 2 + int(bx), H - HUD_H + 12 + int(by), p.kick, p.flash > 0, p.spin, 1.0 - p.cannon_cd / CANNON_RELOAD)
        if p.flash > 0:
            c.fill((46, 30, 10), special_flags=pygame.BLEND_RGB_ADD)
        if p.hurt > 0:
            r = int(160 * min(1.0, p.hurt / 0.5))
            c.fill((r, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
        if p.pick > 0:
            c.fill((int(60 * p.pick / 0.25), int(50 * p.pick / 0.25), 0), special_flags=pygame.BLEND_RGB_ADD)
        if self.state == 'dead':
            a = min(1.0, self.dead_t / 1.5)
            c.fill((int(120 * a), 0, 0), special_flags=pygame.BLEND_RGB_ADD)
            c.fill((int(255 - 150 * a),) * 3, special_flags=pygame.BLEND_RGB_MULT)
        self.draw_hud()
        if self.show_map:
            self.draw_minimap()
        label = tr('enemies') % (self.kills, self.total_enemies)
        img = self.f_mid.render(label, True, (230, 200, 160))
        self.draw_text(c, label, self.f_mid, (230, 200, 160), (W - img.get_width() - 10, 8))
        boss = next((e for e in self.enemies if e.st.get('boss') and e.state not in ('dead', 'idle')), None)
        if boss:
            bw = 260
            bx = (W - bw) // 2
            self.draw_text(c, L2(BOSS_NAMES[boss.kind]), self.f_lab, (255, 220, 200), (W // 2, 62), center=True)
            pygame.draw.rect(c, (0, 0, 0), (bx - 2, 76, bw + 4, 12))
            pygame.draw.rect(c, (170, 20, 20), (bx, 78, int(bw * max(0.0, boss.hp) / boss.maxhp), 8))
        if self.msg_t > 0:
            self.draw_text(c, self.msg_text, self.f_mid, (255, 230, 120), (W // 2, 24), center=True)
        if self.intro_t > 0:
            self.draw_text(c, tr('level') % (self.lvl_idx + 1, self.lname()), self.f_big, (255, 90, 70), (W // 2, 70), center=True)
        if self.state == 'dead' and self.dead_t > 1.0:
            self.draw_text(c, tr('dead'), self.f_title, (220, 20, 20), (W // 2, 110), center=True)
            self.draw_text(c, tr('retry'), self.f_mid, (230, 230, 230), (W // 2, 190), center=True)

    # ---------- écrans ----------
    def draw_title(self):
        c = self.canvas
        t = pygame.time.get_ticks() / 1000.0
        c.blit(self.title_bg, (0, 0))
        cx, cy, r = W // 2, H // 2 + 20, 118
        ang = t * 0.15
        col = (130 + int(50 * math.sin(t * 3)), 10, 10)
        pygame.draw.circle(c, col, (cx, cy), r, 2)
        pygame.draw.circle(c, col, (cx, cy), r + 8, 1)
        pts = [(cx + r * math.sin(ang + 2 * math.pi * k / 5 + math.pi), cy - r * math.cos(ang + 2 * math.pi * k / 5 + math.pi)) for k in range(5)]
        order = [0, 2, 4, 1, 3, 0]
        for a, b in zip(order, order[1:]):
            pygame.draw.line(c, col, pts[a], pts[b], 2)
        self.draw_text(c, "HELLEGATE 64", self.f_title, (210, 24, 12), (W // 2, 36), center=True)
        self.draw_text(c, tr('subtitle'), self.f_mid, (200, 170, 150), (W // 2, 100), center=True)
        if int(t * 2) % 2 == 0:
            self.draw_text(c, tr('press_enter'), self.f_big, (255, 220, 120), (W // 2, 168), center=True)
        lines = [tr('ctrl1'), tr('ctrl2')]
        for i, ln in enumerate(lines):
            self.draw_text(c, ln, self.f_lab, (190, 180, 170), (W // 2, H - 40 + i * 14), center=True)
        if random.random() < 0.012:
            c.fill((90, 90, 110), special_flags=pygame.BLEND_RGB_ADD)

    def draw_lang(self):
        c = self.canvas
        t = pygame.time.get_ticks() / 1000.0
        c.blit(self.title_bg, (0, 0))
        cx, cy, r = W // 2, H // 2 + 20, 118
        ang = t * 0.15
        col = (130 + int(50 * math.sin(t * 3)), 10, 10)
        pygame.draw.circle(c, col, (cx, cy), r, 2)
        pygame.draw.circle(c, col, (cx, cy), r + 8, 1)
        pts = [(cx + r * math.sin(ang + 2 * math.pi * k / 5 + math.pi), cy - r * math.cos(ang + 2 * math.pi * k / 5 + math.pi)) for k in range(5)]
        for a, b in zip([0, 2, 4, 1, 3, 0], [2, 4, 1, 3, 0]):
            pygame.draw.line(c, col, pts[a], pts[b], 2)
        self.draw_text(c, "HELLEGATE 64", self.f_title, (210, 24, 12), (W // 2, 36), center=True)
        self.draw_text(c, "CHOISIS TA LANGUE  /  CHOOSE YOUR LANGUAGE", self.f_mid, (230, 200, 170), (W // 2, 104), center=True)
        for i, name in enumerate(("FRANÇAIS", "ENGLISH")):
            rect = self.lang_rects[i]
            sel = (i == self.lang_sel)
            pygame.draw.rect(c, (60, 8, 8) if sel else (22, 6, 8), rect)
            pygame.draw.rect(c, (255, 200, 60) if sel else (120, 40, 36), rect, 2)
            self.draw_text(c, name, self.f_big, (255, 220, 120) if sel else (190, 160, 140), (rect.centerx, rect.y + 9), center=True)
        self.draw_text(c, TXT['lang_hint'][0], self.f_lab, (190, 180, 170), (W // 2, H - 30), center=True)

    def draw_overlay_screen(self, title, lines, color):
        c = self.canvas
        c.fill((70, 70, 70), special_flags=pygame.BLEND_RGB_MULT)
        self.draw_text(c, title, self.f_title, color, (W // 2, 70), center=True)
        for i, ln in enumerate(lines):
            self.draw_text(c, ln, self.f_big, (235, 225, 210), (W // 2, 150 + i * 30), center=True)

    # ---------- boucle principale ----------
    def toggle_fullscreen(self):
        pygame.display.toggle_fullscreen()

    def handle_event(self, ev):
        if ev.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.state == 'lang':
            pos = self.canvas_mouse()
            for i, rect in enumerate(self.lang_rects):
                if rect.collidepoint(pos):
                    self.choose_lang(i)
            return
        if ev.type == pygame.MOUSEWHEEL and self.state == 'play':
            p = self.p
            for _ in range(4):
                p.weapon = (p.weapon + (1 if ev.y < 0 else -1)) % 4
                if p.has[p.weapon]:
                    break
        if ev.type != pygame.KEYDOWN:
            return
        k = ev.key
        if k == pygame.K_F11:
            self.toggle_fullscreen()
            return
        if self.state == 'lang':
            if k in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s, pygame.K_z):
                self.lang_sel = 1 - self.lang_sel
            elif k == pygame.K_f:
                self.lang_sel = 0
            elif k == pygame.K_e:
                self.lang_sel = 1
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.choose_lang(self.lang_sel)
            elif k == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
        elif self.state == 'title':
            if k == pygame.K_l:
                self.state = 'lang'
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.new_game()
            elif k == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
        elif self.state == 'play':
            if k == pygame.K_ESCAPE:
                self.state = 'pause'
                self.set_mouse(False)
            elif k in (pygame.K_e, pygame.K_f):
                self.use()
            elif k == pygame.K_TAB:
                self.show_map = not self.show_map
            elif k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                i = k - pygame.K_1
                if self.p.has[i]:
                    self.p.weapon = i
        elif self.state == 'pause':
            if k == pygame.K_ESCAPE:
                self.state = 'play'
                self.set_mouse(True)
            elif k == pygame.K_l:
                self.choose_lang(1 if LANG == 'fr' else 0)
            elif k == pygame.K_q:
                pygame.quit()
                sys.exit()
        elif self.state == 'dead':
            if k in (pygame.K_r, pygame.K_RETURN) and self.dead_t > 1.0:
                self.restart_level()
        elif self.state == 'levelend':
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.lvl_idx += 1
                if self.lvl_idx >= len(LEVELS):
                    self.state = 'win'
                else:
                    self.start_level()
        elif self.state == 'win':
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.state = 'title'

    def present(self):
        sw, sh = self.screen.get_size()
        if (sw, sh) == (W, H):
            self.screen.blit(self.canvas, (0, 0))
        else:
            sc = min(sw / W, sh / H)
            nw, nh = int(W * sc), int(H * sc)
            self.screen.fill((0, 0, 0))
            self.screen.blit(pygame.transform.scale(self.canvas, (nw, nh)), ((sw - nw) // 2, (sh - nh) // 2))
        pygame.display.flip()

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for ev in pygame.event.get():
                self.handle_event(ev)
            st = self.state
            if st == 'lang':
                pos = self.canvas_mouse()
                for i, rect in enumerate(self.lang_rects):
                    if rect.collidepoint(pos):
                        self.lang_sel = i
                self.draw_lang()
            elif st == 'title':
                self.draw_title()
            elif st == 'play':
                self.update_play(dt)
                self.draw_play()
            elif st == 'pause':
                self.draw_play()
                self.draw_overlay_screen(tr('pause'), [tr('resume'), tr('lang_change'), tr('quit')], (230, 60, 40))
            elif st == 'dead':
                self.dead_t += dt
                self.update_world(dt * 0.3)
                self.draw_play()
            elif st == 'levelend':
                self.draw_play()
                mins = int(self.level_time // 60)
                secs = int(self.level_time % 60)
                self.draw_overlay_screen(tr('lvl_done'), [
                    self.lname(),
                    tr('kills') % (self.kills, self.total_enemies),
                    tr('time') % (mins, secs),
                    tr('continue')], (90, 255, 120))
            elif st == 'win':
                self.canvas.blit(self.title_bg, (0, 0))
                self.draw_overlay_screen(tr('victory'), [
                    tr('win1'), tr('win2'), tr('win3')], (255, 210, 60))
            self.present()


def main():
    Game().run()


if __name__ == "__main__":
    main()
