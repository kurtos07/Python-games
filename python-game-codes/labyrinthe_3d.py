"""
LABYRINTHE 3D - de la 3D avec seulement pygame

On utilise le "raycasting", la technique des tout premiers jeux de tir à la
première personne (Wolfenstein 3D) : pour chaque colonne de l'écran, on lance
un rayon dans le labyrinthe, on mesure la distance du mur touché, et on dessine
une barre plus ou moins haute (un mur proche paraît plus grand qu'un mur lointain).

Lancer le jeu :   python3 labyrinthe_3d.py      (ou Ctrl+Maj+E dans Pyzo)

But du jeu : trouve la sortie dorée le plus vite possible !

Touches :
  Z / flèche haut     avancer           S / flèche bas    reculer
  Q (ou A)            pas à gauche      D                 pas à droite
  souris ou flèches gauche/droite       tourner
  M  afficher/cacher la carte           T  souris capturée ou libre
  R  recommencer                        Échap  quitter
(Sur un clavier QWERTY, W remplace Z.)
"""

import math
import sys
import pygame

pygame.init()

# ----------------------------------------------------------------------
# RÉGLAGES
# ----------------------------------------------------------------------
LARGEUR, HAUTEUR = 960, 600
PAS = 3                                  # largeur d'une colonne (plus petit = plus joli, mais plus lent)
CHAMP_VISION = math.radians(66)          # l'angle de vue
VITESSE = 3.0                            # cases par seconde
VITESSE_ROTATION = 2.2                   # vitesse de rotation avec les flèches
SENSIBILITE_SOURIS = 0.003

# Le plan du labyrinthe : # = mur, . = vide, P = départ, E = sortie
PLAN = [
    "################",
    "#P.....#.......#",
    "#.####.#.#####.#",
    "#.#....#.#...#.#",
    "#.#.####.#.#.#.#",
    "#.#......#.#...#",
    "#.########.#####",
    "#..........#...#",
    "####.#######.#.#",
    "#....#.......#.#",
    "#.####.#######.#",
    "#......#.......#",
    "#.######.#####.#",
    "#........#...#.#",
    "#.########.#.#.#",
    "##############E#",
]

COULEURS_MURS = [(190, 80, 70), (80, 120, 200), (90, 170, 100)]
COULEUR_SORTIE = (255, 215, 0)

ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Labyrinthe 3D")
horloge = pygame.time.Clock()
police = pygame.font.SysFont(None, 30)
grosse_police = pygame.font.SysFont(None, 80)
petite_police = pygame.font.SysFont(None, 22)

# ----------------------------------------------------------------------
# LA CARTE
# ----------------------------------------------------------------------
CARTE = [list(ligne.replace("P", ".")) for ligne in PLAN]
DEPART = next((c + 0.5, r + 0.5)
              for r, ligne in enumerate(PLAN) for c, case in enumerate(ligne) if case == "P")
CASE_SORTIE = next((c, r)
                   for r, ligne in enumerate(PLAN) for c, case in enumerate(ligne) if case == "E")
CENTRE_SORTIE = (CASE_SORTIE[0] + 0.5, CASE_SORTIE[1] + 0.5)

# Pour chaque colonne de l'écran : de combien l'angle du rayon s'écarte du regard
NB_COLONNES = LARGEUR // PAS
DIST_ECRAN = (LARGEUR / 2) / math.tan(CHAMP_VISION / 2)
DECALAGES = [math.atan((i + 0.5 - NB_COLONNES / 2) / (NB_COLONNES / 2) * math.tan(CHAMP_VISION / 2))
             for i in range(NB_COLONNES)]


def libre(x, y, marge=0.2):
    """Vrai si on peut se tenir en (x, y) sans toucher un mur."""
    for ox in (-marge, marge):
        for oy in (-marge, marge):
            if CARTE[int(y + oy)][int(x + ox)] != ".":
                return False
    return True


def lancer_rayon(px, py, angle):
    """Lance un rayon depuis (px, py). Renvoie (distance, case du mur touché, côté touché)."""
    dx, dy = math.cos(angle), math.sin(angle)
    mx, my = int(px), int(py)                   # la case où l'on se trouve

    # Distance à parcourir pour traverser une case entière dans chaque direction
    delta_x = abs(1 / dx) if dx != 0 else 1e30
    delta_y = abs(1 / dy) if dy != 0 else 1e30

    if dx < 0:
        pas_x, dist_x = -1, (px - mx) * delta_x
    else:
        pas_x, dist_x = 1, (mx + 1 - px) * delta_x
    if dy < 0:
        pas_y, dist_y = -1, (py - my) * delta_y
    else:
        pas_y, dist_y = 1, (my + 1 - py) * delta_y

    # On avance de case en case jusqu'à toucher un mur
    while True:
        if dist_x < dist_y:
            dist_x += delta_x
            mx += pas_x
            cote = 0
        else:
            dist_y += delta_y
            my += pas_y
            cote = 1
        if CARTE[my][mx] != ".":
            break

    distance = (dist_x - delta_x) if cote == 0 else (dist_y - delta_y)
    return distance, mx, my, cote


# ----------------------------------------------------------------------
# DESSIN
# ----------------------------------------------------------------------
def fabriquer_fond():
    """Le plafond (bleu sombre) et le sol (brun), dessinés une seule fois."""
    fond = pygame.Surface((LARGEUR, HAUTEUR))
    moitie = HAUTEUR // 2
    for y in range(moitie):
        t = y / moitie
        pygame.draw.line(fond, (int(15 + 40 * t), int(15 + 40 * t), int(35 + 50 * t)),
                         (0, y), (LARGEUR, y))
    for y in range(moitie, HAUTEUR):
        t = (y - moitie) / moitie
        pygame.draw.line(fond, (int(35 + 60 * t), int(30 + 55 * t), int(25 + 40 * t)),
                         (0, y), (LARGEUR, y))
    return fond


FOND = fabriquer_fond()


def dessiner_vue(px, py, angle):
    for i in range(NB_COLONNES):
        decalage = DECALAGES[i]
        distance, mx, my, cote = lancer_rayon(px, py, angle + decalage)
        distance *= math.cos(decalage)          # évite l'effet "oeil de poisson"
        distance = max(distance, 0.05)

        hauteur = min(int(DIST_ECRAN / distance), HAUTEUR)

        if (mx, my) == CASE_SORTIE:
            base = COULEUR_SORTIE
        else:
            base = COULEURS_MURS[(mx * 3 + my * 5) % 3]
        # Plus c'est loin, plus c'est sombre. Les murs vus "de côté" sont un peu plus sombres.
        ombre = max(0.2, 1 - distance / 10) * (0.7 if cote == 1 else 1.0)
        couleur = (int(base[0] * ombre), int(base[1] * ombre), int(base[2] * ombre))

        pygame.draw.rect(ecran, couleur, (i * PAS, (HAUTEUR - hauteur) // 2, PAS, hauteur))


def dessiner_carte(px, py, angle):
    taille = 9
    pygame.draw.rect(ecran, (20, 20, 30), (10, 10, 16 * taille, 16 * taille))
    for r, ligne in enumerate(CARTE):
        for c, case in enumerate(ligne):
            if case != ".":
                couleur = COULEUR_SORTIE if (c, r) == CASE_SORTIE else (110, 110, 130)
                pygame.draw.rect(ecran, couleur, (10 + c * taille, 10 + r * taille, taille, taille))
    x, y = 10 + px * taille, 10 + py * taille
    pygame.draw.circle(ecran, (255, 60, 60), (int(x), int(y)), 3)
    pygame.draw.line(ecran, (255, 60, 60), (x, y),
                     (x + math.cos(angle) * 9, y + math.sin(angle) * 9), 2)


def ecrire(texte, police_utilisee, couleur, centre):
    ombre = police_utilisee.render(texte, True, (0, 0, 0))
    image = police_utilisee.render(texte, True, couleur)
    ecran.blit(ombre, ombre.get_rect(center=(centre[0] + 2, centre[1] + 2)))
    ecran.blit(image, image.get_rect(center=centre))


# ----------------------------------------------------------------------
# PROGRAMME PRINCIPAL
# ----------------------------------------------------------------------
def main():
    px, py = DEPART
    angle = 0.0                              # 0 = on regarde vers l'est
    debut = pygame.time.get_ticks()
    gagne = False
    temps_final = 0.0
    afficher_carte = True
    souris_active = True

    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)
    pygame.mouse.get_rel()                   # on vide le mouvement initial de la souris

    while True:
        dt = min(horloge.tick(60) / 1000, 0.05)

        # --- Événements ---
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif ev.key == pygame.K_m:
                    afficher_carte = not afficher_carte
                elif ev.key == pygame.K_t:
                    souris_active = not souris_active
                    pygame.event.set_grab(souris_active)
                    pygame.mouse.set_visible(not souris_active)
                    pygame.mouse.get_rel()
                elif ev.key == pygame.K_r:
                    px, py = DEPART
                    angle = 0.0
                    debut = pygame.time.get_ticks()
                    gagne = False

        # --- Déplacements ---
        rotation_souris = pygame.mouse.get_rel()[0]
        if not gagne:
            touches = pygame.key.get_pressed()

            if souris_active:
                angle += rotation_souris * SENSIBILITE_SOURIS
            if touches[pygame.K_LEFT]:
                angle -= VITESSE_ROTATION * dt
            if touches[pygame.K_RIGHT]:
                angle += VITESSE_ROTATION * dt

            avance = ((1 if (touches[pygame.K_UP] or touches[pygame.K_z] or touches[pygame.K_w]) else 0)
                      - (1 if touches[pygame.K_DOWN] or touches[pygame.K_s] else 0))
            cote = ((1 if touches[pygame.K_d] else 0)
                    - (1 if (touches[pygame.K_q] or touches[pygame.K_a]) else 0))

            # devant = (cos, sin) de l'angle ; droite = ce vecteur tourné d'un quart de tour
            dx = (math.cos(angle) * avance - math.sin(angle) * cote) * VITESSE * dt
            dy = (math.sin(angle) * avance + math.cos(angle) * cote) * VITESSE * dt
            # On teste les deux axes séparément : ça permet de glisser le long des murs
            if libre(px + dx, py):
                px += dx
            if libre(px, py + dy):
                py += dy

            if math.hypot(px - CENTRE_SORTIE[0], py - CENTRE_SORTIE[1]) < 1.3:
                gagne = True
                temps_final = (pygame.time.get_ticks() - debut) / 1000

        # --- Dessin ---
        ecran.blit(FOND, (0, 0))
        dessiner_vue(px, py, angle)
        if afficher_carte:
            dessiner_carte(px, py, angle)

        temps = temps_final if gagne else (pygame.time.get_ticks() - debut) / 1000
        ecrire(f"Temps : {temps:.1f} s", police, (255, 255, 255), (LARGEUR - 100, 25))
        ecrire("ZQSD / flèches : bouger     souris : tourner     M : carte     R : recommencer     Échap : quitter",
               petite_police, (210, 210, 220), (LARGEUR // 2, HAUTEUR - 16))

        if gagne:
            voile = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
            voile.fill((0, 0, 0, 150))
            ecran.blit(voile, (0, 0))
            ecrire("BRAVO !", grosse_police, COULEUR_SORTIE, (LARGEUR // 2, 240))
            ecrire(f"Tu as trouvé la sortie en {temps_final:.1f} secondes", police, (255, 255, 255), (LARGEUR // 2, 310))
            ecrire("Appuie sur R pour recommencer", police, (200, 200, 220), (LARGEUR // 2, 350))

        pygame.display.flip()


if __name__ == "__main__":
    main()
