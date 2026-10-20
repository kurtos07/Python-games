"""
MORPION - un petit jeu en Python avec pygame

Lancer le jeu :   python3 morpion.py      (ou Ctrl+Maj+E dans Pyzo)

Comment jouer :
  - Au menu, choisis : 1 = deux joueurs, 2 = contre l'ordinateur
  - Clique sur une case pour jouer. X commence toujours.
  - Le premier qui aligne 3 symboles (ligne, colonne ou diagonale) gagne.
  - R (ou un clic une fois la manche finie) : nouvelle manche
  - M : retour au menu (les scores repartent à zéro)
"""

import random
import sys
import pygame

pygame.init()

# ----------------------------------------------------------------------
# RÉGLAGES
# ----------------------------------------------------------------------
LARGEUR, HAUTEUR = 600, 700
TAILLE_CASE = 180          # une case fait 180 x 180 pixels
X0, Y0 = 30, 130           # coin en haut à gauche de la grille
DELAI_ORDI = 500           # l'ordinateur "réfléchit" 0,5 seconde

COULEUR_FOND = (30, 30, 45)
COULEUR_GRILLE = (200, 200, 220)
COULEUR_X = (230, 70, 70)
COULEUR_O = (80, 150, 255)
COULEUR_VICTOIRE = (255, 215, 0)

# Les 8 façons de gagner (les cases sont numérotées de 0 à 8)
#   0 | 1 | 2
#   3 | 4 | 5
#   6 | 7 | 8
LIGNES = [(0, 1, 2), (3, 4, 5), (6, 7, 8),      # lignes
          (0, 3, 6), (1, 4, 7), (2, 5, 8),      # colonnes
          (0, 4, 8), (2, 4, 6)]                 # diagonales

ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Morpion")
horloge = pygame.time.Clock()
police = pygame.font.SysFont(None, 38)
petite_police = pygame.font.SysFont(None, 26)
grosse_police = pygame.font.SysFont(None, 100)


# ----------------------------------------------------------------------
# LA LOGIQUE DU JEU
# ----------------------------------------------------------------------
def gagnant(plateau):
    """Renvoie ("X" ou "O", la ligne gagnante), ("nul", None) ou (None, None)."""
    for a, b, c in LIGNES:
        if plateau[a] != "" and plateau[a] == plateau[b] == plateau[c]:
            return plateau[a], (a, b, c)
    if "" not in plateau:
        return "nul", None
    return None, None


def coup_ordinateur(plateau):
    """Choisit une case pour l'ordinateur (qui joue les O)."""
    vides = [i for i in range(9) if plateau[i] == ""]

    # 1. Si je peux gagner tout de suite, je le fais
    for i in vides:
        essai = plateau.copy()
        essai[i] = "O"
        if gagnant(essai)[0] == "O":
            return i

    # 2. Si le joueur va gagner, je bloque
    for i in vides:
        essai = plateau.copy()
        essai[i] = "X"
        if gagnant(essai)[0] == "X":
            return i

    # 3. Sinon je prends le centre, puis au hasard
    if 4 in vides:
        return 4
    return random.choice(vides)


def poser(plateau, i, joueur, scores):
    """Pose le symbole du joueur sur la case i et regarde si la manche est finie."""
    plateau[i] = joueur
    resultat, ligne = gagnant(plateau)
    if resultat:
        scores[resultat] += 1
    return resultat, ligne


# ----------------------------------------------------------------------
# OUTILS DE DESSIN
# ----------------------------------------------------------------------
def centre_case(i):
    x = X0 + (i % 3) * TAILLE_CASE + TAILLE_CASE // 2
    y = Y0 + (i // 3) * TAILLE_CASE + TAILLE_CASE // 2
    return x, y


def case_cliquee(pos):
    """Renvoie le numéro de la case sous la souris, ou None."""
    x, y = pos
    if X0 <= x < X0 + 3 * TAILLE_CASE and Y0 <= y < Y0 + 3 * TAILLE_CASE:
        colonne = (x - X0) // TAILLE_CASE
        ligne = (y - Y0) // TAILLE_CASE
        return ligne * 3 + colonne
    return None


def ecrire(texte, police_utilisee, couleur, centre):
    image = police_utilisee.render(texte, True, couleur)
    ecran.blit(image, image.get_rect(center=centre))


def dessiner_grille():
    for k in (1, 2):
        # lignes verticales
        pygame.draw.line(ecran, COULEUR_GRILLE,
                         (X0 + k * TAILLE_CASE, Y0), (X0 + k * TAILLE_CASE, Y0 + 3 * TAILLE_CASE), 6)
        # lignes horizontales
        pygame.draw.line(ecran, COULEUR_GRILLE,
                         (X0, Y0 + k * TAILLE_CASE), (X0 + 3 * TAILLE_CASE, Y0 + k * TAILLE_CASE), 6)


def dessiner_symbole(i, symbole):
    cx, cy = centre_case(i)
    if symbole == "X":
        pygame.draw.line(ecran, COULEUR_X, (cx - 50, cy - 50), (cx + 50, cy + 50), 14)
        pygame.draw.line(ecran, COULEUR_X, (cx + 50, cy - 50), (cx - 50, cy + 50), 14)
    elif symbole == "O":
        pygame.draw.circle(ecran, COULEUR_O, (cx, cy), 55, 14)


# ----------------------------------------------------------------------
# LE PROGRAMME PRINCIPAL
# ----------------------------------------------------------------------
def main():
    etat = "menu"                      # "menu" ou "jeu"
    mode = 2                           # 1 = deux joueurs, 2 = contre l'ordinateur
    plateau = [""] * 9                 # 9 cases vides
    tour = "X"                         # à qui de jouer
    resultat = None                    # None, "X", "O" ou "nul"
    ligne_gagnante = None
    scores = {"X": 0, "O": 0, "nul": 0}
    moment_coup = 0                    # pour faire attendre un peu l'ordinateur

    bouton_1 = pygame.Rect(150, 300, 300, 70)
    bouton_2 = pygame.Rect(150, 400, 300, 70)

    while True:
        horloge.tick(60)

        # --- Événements (clics, touches) ---
        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if etat == "menu":
                choix = None
                if evenement.type == pygame.KEYDOWN:
                    if evenement.key in (pygame.K_1, pygame.K_KP1):
                        choix = 1
                    elif evenement.key in (pygame.K_2, pygame.K_KP2):
                        choix = 2
                if evenement.type == pygame.MOUSEBUTTONDOWN and evenement.button == 1:
                    if bouton_1.collidepoint(evenement.pos):
                        choix = 1
                    elif bouton_2.collidepoint(evenement.pos):
                        choix = 2
                if choix:
                    mode = choix
                    plateau, tour, resultat, ligne_gagnante = [""] * 9, "X", None, None
                    scores = {"X": 0, "O": 0, "nul": 0}
                    etat = "jeu"

            else:  # etat == "jeu"
                nouvelle_manche = False
                if evenement.type == pygame.KEYDOWN:
                    if evenement.key == pygame.K_r:
                        nouvelle_manche = True
                    elif evenement.key == pygame.K_m:
                        etat = "menu"

                if evenement.type == pygame.MOUSEBUTTONDOWN and evenement.button == 1:
                    if resultat:
                        nouvelle_manche = True       # manche finie : un clic relance
                    else:
                        i = case_cliquee(evenement.pos)
                        humain_joue = (mode == 1 or tour == "X")
                        if i is not None and plateau[i] == "" and humain_joue:
                            resultat, ligne_gagnante = poser(plateau, i, tour, scores)
                            if not resultat:
                                tour = "O" if tour == "X" else "X"
                                moment_coup = pygame.time.get_ticks()

                if nouvelle_manche:
                    plateau, tour, resultat, ligne_gagnante = [""] * 9, "X", None, None

        # --- L'ordinateur joue ---
        if etat == "jeu" and mode == 2 and tour == "O" and not resultat:
            if pygame.time.get_ticks() - moment_coup >= DELAI_ORDI:
                i = coup_ordinateur(plateau)
                resultat, ligne_gagnante = poser(plateau, i, "O", scores)
                if not resultat:
                    tour = "X"

        # --- Dessin ---
        ecran.fill(COULEUR_FOND)

        if etat == "menu":
            ecrire("MORPION", grosse_police, (255, 255, 255), (LARGEUR // 2, 170))
            ecrire("Choisis un mode de jeu", petite_police, (180, 180, 200), (LARGEUR // 2, 250))
            pygame.draw.rect(ecran, (70, 70, 100), bouton_1, border_radius=10)
            pygame.draw.rect(ecran, (70, 70, 100), bouton_2, border_radius=10)
            ecrire("1 : Deux joueurs", police, (255, 255, 255), bouton_1.center)
            ecrire("2 : Contre l'ordinateur", police, (255, 255, 255), bouton_2.center)

        else:
            # Texte du haut
            noms = {"X": "X", "O": "O"}
            if mode == 2:
                noms = {"X": "Toi (X)", "O": "L'ordinateur (O)"}

            if resultat == "nul":
                statut = "Match nul !"
            elif resultat:
                statut = f"{noms[resultat]} gagne !"
            elif mode == 2 and tour == "O":
                statut = "L'ordinateur réfléchit..."
            else:
                statut = f"Tour de {noms[tour]}" if mode == 1 else "À toi de jouer"
            ecrire(statut, police, (255, 255, 255), (LARGEUR // 2, 35))

            texte_scores = f"{noms['X']} : {scores['X']}     {noms['O']} : {scores['O']}     Nuls : {scores['nul']}"
            ecrire(texte_scores, petite_police, (255, 215, 0), (LARGEUR // 2, 72))
            aide = "Clique pour rejouer  -  M : menu" if resultat else "R : recommencer  -  M : menu"
            ecrire(aide, petite_police, (140, 140, 160), (LARGEUR // 2, 102))

            # La grille et les symboles
            dessiner_grille()
            for i in range(9):
                dessiner_symbole(i, plateau[i])

            # Ligne dorée sur la combinaison gagnante
            if ligne_gagnante:
                debut = centre_case(ligne_gagnante[0])
                fin = centre_case(ligne_gagnante[2])
                pygame.draw.line(ecran, COULEUR_VICTOIRE, debut, fin, 10)

        pygame.display.flip()


if __name__ == "__main__":
    main()
