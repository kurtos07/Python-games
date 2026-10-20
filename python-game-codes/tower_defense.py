"""
TOWER DEFENSE - un petit jeu en Python avec pygame

Installation (une seule fois) :   pip install pygame
Lancer le jeu :                   python3 tower_defense.py

Comment jouer :
  - Clique sur une tourelle dans le menu du bas (ou touches 1 à 5)
  - Clique sur la carte pour la poser (pas sur le chemin marron !)
  - Clic droit : annuler la sélection
  - ESPACE : lancer la vague suivante
  - Tuer un ennemi rapporte de l'or. Plus la tourelle est chère, plus elle fait mal.
  - À chaque vague, les ennemis ont plus de points de vie.
  - Toutes les 10 vagues, un BOSS arrive (de plus en plus fort) !
"""

import math
import sys
import pygame

pygame.init()

# ----------------------------------------------------------------------
# RÉGLAGES DU JEU (tu peux modifier ces valeurs pour changer la difficulté)
# ----------------------------------------------------------------------
LARGEUR, HAUTEUR = 900, 700
HAUTEUR_JEU = 600            # en dessous de 600 pixels : le menu
OR_DEPART = 100
VIES_DEPART = 20
PV_ENNEMI_BASE = 30          # points de vie des ennemis à la vague 1
AUGMENTATION_PV = 1.25       # à chaque vague, les PV sont multipliés par 1.25
LARGEUR_CHEMIN = 40

# Le chemin que suivent les ennemis (liste de points)
CHEMIN = [(0, 100), (700, 100), (700, 250), (150, 250),
          (150, 400), (700, 400), (700, 520), (900, 520)]

# Les tourelles : plus elles coûtent cher, plus elles font de dégâts
TOURELLES = [
    {"nom": "Petite",  "prix": 50,  "degats": 8,   "portee": 110, "cadence": 0.5, "couleur": (80, 200, 80)},
    {"nom": "Moyenne", "prix": 100, "degats": 20,  "portee": 130, "cadence": 0.5, "couleur": (80, 140, 255)},
    {"nom": "Grosse",  "prix": 200, "degats": 50,  "portee": 150, "cadence": 0.6, "couleur": (255, 160, 40)},
    {"nom": "Canon",   "prix": 400, "degats": 130, "portee": 170, "cadence": 0.7, "couleur": (230, 60, 60)},
    {"nom": "Titan",   "prix": 3000, "degats": 500, "portee": 200, "cadence": 0.8, "couleur": (190, 80, 255)},
]

# Un boss arrive toutes les BOSS_TOUS_LES vagues
BOSS_TOUS_LES = 10

ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Tower Defense")
horloge = pygame.time.Clock()
police = pygame.font.SysFont(None, 26)
petite_police = pygame.font.SysFont(None, 21)
grosse_police = pygame.font.SysFont(None, 80)


# ----------------------------------------------------------------------
# OUTILS
# ----------------------------------------------------------------------
def distance_segment(px, py, ax, ay, bx, by):
    """Distance entre le point (px,py) et le segment [A,B]."""
    dx, dy = bx - ax, by - ay
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def sur_le_chemin(x, y):
    for i in range(len(CHEMIN) - 1):
        ax, ay = CHEMIN[i]
        bx, by = CHEMIN[i + 1]
        if distance_segment(x, y, ax, ay, bx, by) < LARGEUR_CHEMIN / 2 + 15:
            return True
    return False


# ----------------------------------------------------------------------
# LES OBJETS DU JEU
# ----------------------------------------------------------------------
class Ennemi:
    def __init__(self, pv, vitesse, recompense, boss=False):
        self.boss = boss
        self.rayon = 22 if boss else 12
        self.couleur = (150, 0, 200) if boss else (200, 40, 40)
        self.vies_perdues = 5 if boss else 1   # un boss qui passe fait très mal
        self.x, self.y = CHEMIN[0]
        self.cible = 1               # indice du prochain point du chemin
        self.pv = pv
        self.pv_max = pv
        self.vitesse = vitesse
        self.recompense = recompense
        self.parcouru = 0            # distance faite (pour savoir qui est en tête)
        self.arrive = False

    def avancer(self, dt):
        reste = self.vitesse * dt
        while reste > 0 and not self.arrive:
            tx, ty = CHEMIN[self.cible]
            dx, dy = tx - self.x, ty - self.y
            d = math.hypot(dx, dy)
            if d <= reste:
                self.x, self.y = tx, ty
                reste -= d
                self.parcouru += d
                self.cible += 1
                if self.cible >= len(CHEMIN):
                    self.arrive = True
            else:
                self.x += dx / d * reste
                self.y += dy / d * reste
                self.parcouru += reste
                reste = 0

    def dessiner(self):
        pygame.draw.circle(ecran, self.couleur, (int(self.x), int(self.y)), self.rayon)
        if self.boss:
            pygame.draw.circle(ecran, (255, 215, 0), (int(self.x), int(self.y)), self.rayon, 3)
        # barre de vie
        largeur = 50 if self.boss else 26
        haut = self.y - self.rayon - 9
        ratio = max(0, self.pv / self.pv_max)
        pygame.draw.rect(ecran, (60, 0, 0), (self.x - largeur / 2, haut, largeur, 5))
        pygame.draw.rect(ecran, (0, 220, 0), (self.x - largeur / 2, haut, largeur * ratio, 5))


class Projectile:
    def __init__(self, x, y, cible, degats, couleur):
        self.x, self.y = x, y
        self.cible = cible
        self.degats = degats
        self.couleur = couleur
        self.vitesse = 450
        self.fini = False

    def avancer(self, dt):
        if self.cible.pv <= 0 or self.cible.arrive:
            self.fini = True
            return
        dx, dy = self.cible.x - self.x, self.cible.y - self.y
        d = math.hypot(dx, dy)
        pas = self.vitesse * dt
        if d <= pas:
            self.cible.pv -= self.degats
            self.fini = True
        else:
            self.x += dx / d * pas
            self.y += dy / d * pas

    def dessiner(self):
        pygame.draw.circle(ecran, self.couleur, (int(self.x), int(self.y)), 5)


class Tourelle:
    def __init__(self, x, y, modele):
        self.x, self.y = x, y
        self.modele = modele
        self.recharge = 0

    def mettre_a_jour(self, dt, ennemis, projectiles):
        self.recharge -= dt
        if self.recharge > 0:
            return
        m = self.modele
        a_portee = [e for e in ennemis
                    if math.hypot(e.x - self.x, e.y - self.y) <= m["portee"]]
        if a_portee:
            cible = max(a_portee, key=lambda e: e.parcouru)  # le plus avancé
            projectiles.append(Projectile(self.x, self.y, cible, m["degats"], m["couleur"]))
            self.recharge = m["cadence"]

    def dessiner(self):
        pygame.draw.circle(ecran, self.modele["couleur"], (self.x, self.y), 15)
        pygame.draw.circle(ecran, (20, 20, 20), (self.x, self.y), 15, 2)


# ----------------------------------------------------------------------
# DESSIN
# ----------------------------------------------------------------------
def dessiner_carte():
    ecran.fill((50, 110, 50))
    for i in range(len(CHEMIN) - 1):
        pygame.draw.line(ecran, (140, 100, 60), CHEMIN[i], CHEMIN[i + 1], LARGEUR_CHEMIN)
    for point in CHEMIN:
        pygame.draw.circle(ecran, (140, 100, 60), point, LARGEUR_CHEMIN // 2)


def rectangle_bouton(i):
    return pygame.Rect(10 + i * 126, 610, 120, 80)


def dessiner_menu(argent, vies, vague, selection, en_cours):
    pygame.draw.rect(ecran, (30, 30, 40), (0, HAUTEUR_JEU, LARGEUR, HAUTEUR - HAUTEUR_JEU))
    for i, m in enumerate(TOURELLES):
        r = rectangle_bouton(i)
        abordable = argent >= m["prix"]
        fond = (70, 70, 90) if abordable else (45, 45, 50)
        pygame.draw.rect(ecran, fond, r, border_radius=8)
        if selection == i:
            pygame.draw.rect(ecran, (255, 255, 255), r, 3, border_radius=8)
        pygame.draw.circle(ecran, m["couleur"], (r.x + 16, r.y + 22), 10)
        couleur_texte = (255, 255, 255) if abordable else (130, 130, 130)
        ecran.blit(police.render(f"{i + 1}. {m['nom']}", True, couleur_texte), (r.x + 31, r.y + 14))
        ecran.blit(petite_police.render(f"{m['prix']} or", True, (255, 215, 0) if abordable else (130, 130, 130)), (r.x + 10, r.y + 44))
        ecran.blit(petite_police.render(f"Dégâts : {m['degats']}", True, couleur_texte), (r.x + 10, r.y + 61))

    ecran.blit(police.render(f"Or : {argent}", True, (255, 215, 0)), (665, 612))
    ecran.blit(police.render(f"Vies : {vies}", True, (255, 100, 100)), (665, 636))
    ecran.blit(police.render(f"Vague : {vague}", True, (255, 255, 255)), (665, 660))
    if not en_cours:
        ecran.blit(petite_police.render("ESPACE : vague suivante", True, (180, 255, 180)), (665, 685))


# ----------------------------------------------------------------------
# UNE PARTIE
# ----------------------------------------------------------------------
def jouer():
    argent = OR_DEPART
    vies = VIES_DEPART
    vague = 0
    en_cours = False          # une vague est-elle en train d'arriver ?
    a_envoyer = 0             # ennemis qu'il reste à faire apparaître
    delai_apparition = 0
    selection = None          # tourelle choisie dans le menu (0 à 3)

    ennemis, tourelles, projectiles = [], [], []

    while True:
        dt = horloge.tick(60) / 1000
        souris = pygame.mouse.get_pos()

        # --- Événements (clics, touches) ---
        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evenement.type == pygame.KEYDOWN:
                if evenement.key == pygame.K_SPACE and not en_cours and vies > 0:
                    vague += 1
                    en_cours = True
                    a_envoyer = 4 + 2 * vague
                    delai_apparition = 0
                if evenement.key == pygame.K_r and vies <= 0:
                    return  # relance une nouvelle partie
                if evenement.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                    selection = evenement.key - pygame.K_1

            if evenement.type == pygame.MOUSEBUTTONDOWN and vies > 0:
                if evenement.button == 3:          # clic droit
                    selection = None
                elif evenement.button == 1:        # clic gauche
                    x, y = evenement.pos
                    if y >= HAUTEUR_JEU:           # clic dans le menu
                        for i in range(len(TOURELLES)):
                            if rectangle_bouton(i).collidepoint(x, y):
                                selection = i
                    elif selection is not None:    # clic sur la carte : on pose
                        modele = TOURELLES[selection]
                        libre = not sur_le_chemin(x, y) and y < HAUTEUR_JEU - 15
                        libre = libre and all(math.hypot(t.x - x, t.y - y) >= 32 for t in tourelles)
                        if libre and argent >= modele["prix"]:
                            tourelles.append(Tourelle(x, y, modele))
                            argent -= modele["prix"]

        # --- Mise à jour du jeu ---
        if vies > 0:
            # Apparition des ennemis de la vague
            if en_cours and a_envoyer > 0:
                delai_apparition -= dt
                if delai_apparition <= 0:
                    pv = PV_ENNEMI_BASE * (AUGMENTATION_PV ** (vague - 1))
                    dernier = (a_envoyer == 1)
                    if dernier and vague % BOSS_TOUS_LES == 0:
                        # Le boss ferme la marche. Plus il y en a eu, plus il est fort.
                        numero = vague // BOSS_TOUS_LES      # 1er boss, 2e boss...
                        pv_boss = pv * (10 + 5 * numero)
                        ennemis.append(Ennemi(pv_boss, 40 + vague, 150 * numero, boss=True))
                    else:
                        ennemis.append(Ennemi(pv, 60 + 3 * vague, 8 + vague))
                    a_envoyer -= 1
                    delai_apparition = 0.8

            for e in ennemis:
                e.avancer(dt)
            for t in tourelles:
                t.mettre_a_jour(dt, ennemis, projectiles)
            for p in projectiles:
                p.avancer(dt)

            # Ennemis morts => de l'or ; ennemis arrivés => on perd une vie
            for e in ennemis:
                if e.pv <= 0:
                    argent += e.recompense
                elif e.arrive:
                    vies -= e.vies_perdues
            ennemis = [e for e in ennemis if e.pv > 0 and not e.arrive]
            projectiles = [p for p in projectiles if not p.fini]

            # Fin de vague
            if en_cours and a_envoyer == 0 and not ennemis:
                en_cours = False
                argent += 25   # petit bonus

        # --- Dessin ---
        dessiner_carte()
        for t in tourelles:
            t.dessiner()
        for e in ennemis:
            e.dessiner()
        for p in projectiles:
            p.dessiner()

        # Aperçu de la tourelle sous la souris
        if selection is not None and souris[1] < HAUTEUR_JEU and vies > 0:
            m = TOURELLES[selection]
            ok = not sur_le_chemin(*souris) and souris[1] < HAUTEUR_JEU - 15
            ok = ok and all(math.hypot(t.x - souris[0], t.y - souris[1]) >= 32 for t in tourelles)
            ok = ok and argent >= m["prix"]
            zone = pygame.Surface((LARGEUR, HAUTEUR_JEU), pygame.SRCALPHA)
            couleur = (255, 255, 255, 60) if ok else (255, 0, 0, 80)
            pygame.draw.circle(zone, couleur, souris, m["portee"])
            ecran.blit(zone, (0, 0))
            pygame.draw.circle(ecran, m["couleur"], souris, 15)

        dessiner_menu(argent, max(0, vies), vague, selection, en_cours)

        # Messages d'alerte pour les boss
        message = None
        if en_cours and vague % BOSS_TOUS_LES == 0:
            message = f"ATTENTION : BOSS {vague // BOSS_TOUS_LES} !"
        elif not en_cours and (vague + 1) % BOSS_TOUS_LES == 0:
            message = "La prochaine vague a un BOSS !"
        if message and vies > 0:
            texte_boss = police.render(message, True, (255, 120, 255))
            ecran.blit(texte_boss, (LARGEUR // 2 - texte_boss.get_width() // 2, 10))

        if vies <= 0:
            voile = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
            voile.fill((0, 0, 0, 170))
            ecran.blit(voile, (0, 0))
            texte = grosse_police.render("PERDU !", True, (255, 80, 80))
            ecran.blit(texte, texte.get_rect(center=(LARGEUR // 2, 280)))
            info = police.render(f"Tu as tenu jusqu'à la vague {vague}. Appuie sur R pour rejouer.", True, (255, 255, 255))
            ecran.blit(info, info.get_rect(center=(LARGEUR // 2, 350)))

        pygame.display.flip()


while True:
    jouer()
