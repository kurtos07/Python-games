"""
ÉCHECS - un jeu d'échecs en Python avec pygame

Lancer le jeu :   python3 echecs.py      (ou Ctrl+Maj+E dans Pyzo)

Comment jouer :
  - Au menu, choisis un mode (touches 1 à 4, ou clic sur un bouton)
  - Clique sur une de tes pièces : les cases où elle peut aller s'affichent
  - Clique sur une de ces cases pour jouer le coup
  - Les blancs (en bas) commencent. Contre l'ordinateur, tu joues les blancs.

Règles gérées : tous les déplacements, la prise en passant, le roque,
la promotion (tu choisis la pièce), l'échec, l'échec et mat, le pat,
la règle des 50 coups et le matériel insuffisant.

Touches : R = nouvelle partie   M = menu   F = retourner l'échiquier
"""

import random
import sys
import pygame

pygame.init()

# ----------------------------------------------------------------------
# RÉGLAGES
# ----------------------------------------------------------------------
LARGEUR, HAUTEUR = 680, 760
CASE = 80                  # une case fait 80 x 80 pixels
X0, Y0 = 20, 70            # coin en haut à gauche de l'échiquier

FOND = (35, 35, 45)
CLAIR = (238, 238, 210)
FONCE = (118, 150, 86)
BLANC = (255, 255, 255)
GRIS = (160, 160, 180)

ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Échecs")
horloge = pygame.time.Clock()
police = pygame.font.SysFont(None, 36)
petite_police = pygame.font.SysFont(None, 24)
police_lettres = pygame.font.SysFont(None, 48)
grosse_police = pygame.font.SysFont(None, 110)


def trouver_police_pieces():
    """Cherche une police qui sait dessiner les pièces d'échecs (♔ ♕ ♖...)."""
    for nom in ("dejavusans", "freeserif", "symbola", "notosanssymbols2",
                "segoeuisymbol", "arialunicodems"):
        chemin = pygame.font.match_font(nom)
        if chemin:
            return pygame.font.Font(chemin, 64)
    return None


POLICE_PIECES = trouver_police_pieces()

# ----------------------------------------------------------------------
# LES PIÈCES
#   Chaque case de l'échiquier contient "" (vide) ou un texte de 2 lettres :
#   la couleur ("w" blanc, "b" noir) + le type
#   (K roi, Q dame, R tour, B fou, N cavalier, P pion). Exemple : "wK".
#   plateau[ligne][colonne] : la ligne 0 est en haut (côté des noirs).
# ----------------------------------------------------------------------
DIRS_TOUR = [(1, 0), (-1, 0), (0, 1), (0, -1)]
DIRS_FOU = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
DIRS_ROI = DIRS_TOUR + DIRS_FOU
SAUTS_CAVALIER = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]

VALEURS = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}


def plateau_depart():
    ordre = ["R", "N", "B", "Q", "K", "B", "N", "R"]
    plateau = [[""] * 8 for _ in range(8)]
    for c in range(8):
        plateau[0][c] = "b" + ordre[c]
        plateau[1][c] = "bP"
        plateau[6][c] = "wP"
        plateau[7][c] = "w" + ordre[c]
    return plateau


def case_attaquee(plateau, r, c, par):
    """Vrai si la case (r, c) est attaquée par une pièce de la couleur `par`."""
    # pions
    pr = r + (1 if par == "w" else -1)
    if 0 <= pr < 8:
        for dc in (-1, 1):
            pc = c + dc
            if 0 <= pc < 8 and plateau[pr][pc] == par + "P":
                return True
    # cavaliers
    for dr, dc in SAUTS_CAVALIER:
        r2, c2 = r + dr, c + dc
        if 0 <= r2 < 8 and 0 <= c2 < 8 and plateau[r2][c2] == par + "N":
            return True
    # roi
    for dr, dc in DIRS_ROI:
        r2, c2 = r + dr, c + dc
        if 0 <= r2 < 8 and 0 <= c2 < 8 and plateau[r2][c2] == par + "K":
            return True
    # tours et dames (en ligne droite)
    for dr, dc in DIRS_TOUR:
        r2, c2 = r + dr, c + dc
        while 0 <= r2 < 8 and 0 <= c2 < 8:
            piece = plateau[r2][c2]
            if piece:
                if piece[0] == par and piece[1] in "RQ":
                    return True
                break
            r2 += dr
            c2 += dc
    # fous et dames (en diagonale)
    for dr, dc in DIRS_FOU:
        r2, c2 = r + dr, c + dc
        while 0 <= r2 < 8 and 0 <= c2 < 8:
            piece = plateau[r2][c2]
            if piece:
                if piece[0] == par and piece[1] in "BQ":
                    return True
                break
            r2 += dr
            c2 += dc
    return False


def trouver_roi(plateau, couleur):
    for r in range(8):
        for c in range(8):
            if plateau[r][c] == couleur + "K":
                return r, c
    return None


def materiel_insuffisant(plateau):
    """Roi seul, ou roi + un seul fou/cavalier : impossible de faire mat."""
    pieces = [p[1] for ligne in plateau for p in ligne if p and p[1] != "K"]
    if not pieces:
        return True
    if len(pieces) == 1 and pieces[0] in "BN":
        return True
    return False


# ----------------------------------------------------------------------
# LA PARTIE (l'état du jeu + les règles)
#   Un coup est un tuple : (ligne départ, colonne départ, ligne arrivée,
#   colonne arrivée, promotion). La promotion vaut None ou "Q", "R", "B", "N".
# ----------------------------------------------------------------------
class Partie:
    def __init__(self):
        self.plateau = plateau_depart()
        self.trait = "w"                       # à qui de jouer
        self.roques = {"wK": True, "wQ": True, "bK": True, "bQ": True}
        self.en_passant = None                 # case de prise en passant possible
        self.coups_sans_prise = 0              # pour la règle des 50 coups

    def copie(self):
        p = Partie.__new__(Partie)
        p.plateau = [ligne[:] for ligne in self.plateau]
        p.trait = self.trait
        p.roques = self.roques.copy()
        p.en_passant = self.en_passant
        p.coups_sans_prise = self.coups_sans_prise
        return p

    # --- Génération des coups --------------------------------------------
    def coups_pseudo(self):
        """Les coups qui respectent le déplacement des pièces
        (sans vérifier si le roi reste en échec)."""
        b = self.plateau
        moi = self.trait
        adv = "b" if moi == "w" else "w"
        coups = []
        for r in range(8):
            for c in range(8):
                piece = b[r][c]
                if not piece or piece[0] != moi:
                    continue
                t = piece[1]
                if t == "P":
                    self._coups_pion(coups, r, c, moi)
                elif t == "N":
                    for dr, dc in SAUTS_CAVALIER:
                        r2, c2 = r + dr, c + dc
                        if 0 <= r2 < 8 and 0 <= c2 < 8 and (b[r2][c2] == "" or b[r2][c2][0] == adv):
                            coups.append((r, c, r2, c2, None))
                elif t in "BRQ":
                    if t == "B":
                        directions = DIRS_FOU
                    elif t == "R":
                        directions = DIRS_TOUR
                    else:
                        directions = DIRS_ROI
                    for dr, dc in directions:
                        r2, c2 = r + dr, c + dc
                        while 0 <= r2 < 8 and 0 <= c2 < 8:
                            cible = b[r2][c2]
                            if cible == "":
                                coups.append((r, c, r2, c2, None))
                            else:
                                if cible[0] == adv:
                                    coups.append((r, c, r2, c2, None))
                                break
                            r2 += dr
                            c2 += dc
                elif t == "K":
                    for dr, dc in DIRS_ROI:
                        r2, c2 = r + dr, c + dc
                        if 0 <= r2 < 8 and 0 <= c2 < 8 and (b[r2][c2] == "" or b[r2][c2][0] == adv):
                            coups.append((r, c, r2, c2, None))
                    self._coups_roque(coups, r, c, moi, adv)
        return coups

    def _coups_pion(self, coups, r, c, moi):
        b = self.plateau
        d = -1 if moi == "w" else 1                  # sens de marche
        depart = 6 if moi == "w" else 1
        derniere = 0 if moi == "w" else 7

        def ajouter(r2, c2):
            if r2 == derniere:                       # promotion : 4 choix
                for promo in "QRBN":
                    coups.append((r, c, r2, c2, promo))
            else:
                coups.append((r, c, r2, c2, None))

        r2 = r + d
        if not (0 <= r2 < 8):
            return
        # avancer d'une ou deux cases
        if b[r2][c] == "":
            ajouter(r2, c)
            if r == depart and b[r + 2 * d][c] == "":
                coups.append((r, c, r + 2 * d, c, None))
        # prendre en diagonale (ou prise en passant)
        for dc in (-1, 1):
            c2 = c + dc
            if 0 <= c2 < 8:
                cible = b[r2][c2]
                if cible != "" and cible[0] != moi:
                    ajouter(r2, c2)
                elif cible == "" and (r2, c2) == self.en_passant:
                    coups.append((r, c, r2, c2, None))

    def _coups_roque(self, coups, r, c, moi, adv):
        b = self.plateau
        rangee = 7 if moi == "w" else 0
        if (r, c) != (rangee, 4):
            return
        if not (self.roques[moi + "K"] or self.roques[moi + "Q"]):
            return
        if case_attaquee(b, rangee, 4, adv):         # pas de roque si on est en échec
            return
        # petit roque (côté roi)
        if (self.roques[moi + "K"] and b[rangee][7] == moi + "R"
                and b[rangee][5] == "" and b[rangee][6] == ""
                and not case_attaquee(b, rangee, 5, adv)
                and not case_attaquee(b, rangee, 6, adv)):
            coups.append((rangee, 4, rangee, 6, None))
        # grand roque (côté dame)
        if (self.roques[moi + "Q"] and b[rangee][0] == moi + "R"
                and b[rangee][1] == "" and b[rangee][2] == "" and b[rangee][3] == ""
                and not case_attaquee(b, rangee, 3, adv)
                and not case_attaquee(b, rangee, 2, adv)):
            coups.append((rangee, 4, rangee, 2, None))

    def coups_legaux(self):
        """Les coups autorisés : ceux qui ne laissent pas notre roi en échec."""
        legaux = []
        adv = "b" if self.trait == "w" else "w"
        for coup in self.coups_pseudo():
            suivante = self.jouer(coup)
            rr, rc = trouver_roi(suivante.plateau, self.trait)
            if not case_attaquee(suivante.plateau, rr, rc, adv):
                legaux.append(coup)
        return legaux

    # --- Jouer un coup ------------------------------------------------------
    def jouer(self, coup):
        """Renvoie la NOUVELLE partie après le coup (l'ancienne ne change pas)."""
        r1, c1, r2, c2, promo = coup
        p = self.copie()
        b = p.plateau
        piece = b[r1][c1]
        couleur, type_ = piece[0], piece[1]
        capture = b[r2][c2] != ""

        # prise en passant : le pion pris est à côté, pas sur la case d'arrivée
        if type_ == "P" and c1 != c2 and not capture and (r2, c2) == self.en_passant:
            b[r1][c2] = ""
            capture = True

        b[r2][c2] = piece
        b[r1][c1] = ""

        if promo:
            b[r2][c2] = couleur + promo

        # roque : on déplace aussi la tour
        if type_ == "K" and abs(c2 - c1) == 2:
            if c2 == 6:
                b[r1][5] = b[r1][7]
                b[r1][7] = ""
            else:
                b[r1][3] = b[r1][0]
                b[r1][0] = ""

        # droits de roque perdus si le roi ou une tour bouge (ou est prise)
        if type_ == "K":
            p.roques[couleur + "K"] = False
            p.roques[couleur + "Q"] = False
        for (rr, cc, cle) in ((7, 0, "wQ"), (7, 7, "wK"), (0, 0, "bQ"), (0, 7, "bK")):
            if (r1, c1) == (rr, cc) or (r2, c2) == (rr, cc):
                p.roques[cle] = False

        # un pion qui avance de 2 cases peut être pris en passant au coup suivant
        p.en_passant = None
        if type_ == "P" and abs(r2 - r1) == 2:
            p.en_passant = ((r1 + r2) // 2, c1)

        if type_ == "P" or capture:
            p.coups_sans_prise = 0
        else:
            p.coups_sans_prise += 1

        p.trait = "b" if couleur == "w" else "w"
        return p

    # --- État de la partie ------------------------------------------------------
    def en_echec(self):
        rr, rc = trouver_roi(self.plateau, self.trait)
        adv = "b" if self.trait == "w" else "w"
        return case_attaquee(self.plateau, rr, rc, adv)

    def statut(self, legaux):
        if not legaux:
            return "mat" if self.en_echec() else "pat"
        if self.coups_sans_prise >= 100:
            return "nulle50"
        if materiel_insuffisant(self.plateau):
            return "nulle_materiel"
        return "en_cours"


# ----------------------------------------------------------------------
# L'ORDINATEUR (il essaie plusieurs coups à l'avance et garde le meilleur)
# ----------------------------------------------------------------------
INFINI = 10 ** 9


def evaluer(plateau):
    """Note la position du point de vue des blancs (positif = les blancs sont mieux)."""
    score = 0
    for r in range(8):
        for c in range(8):
            piece = plateau[r][c]
            if not piece:
                continue
            couleur, t = piece[0], piece[1]
            valeur = VALEURS[t]
            distance_centre = max(abs(r - 3.5), abs(c - 3.5))      # de 0,5 à 3,5
            if t == "P":
                avance = (6 - r) if couleur == "w" else (r - 1)
                valeur += avance * 5 + (3.5 - distance_centre) * 4
            elif t in "NB":
                valeur += (3.5 - distance_centre) * 8
            elif t == "Q":
                valeur += (3.5 - distance_centre) * 2
            score += valeur if couleur == "w" else -valeur
    return score


def valeur_ordre(partie, coup):
    """Pour essayer les prises en premier (ça accélère la recherche)."""
    cible = partie.plateau[coup[2]][coup[3]]
    v = VALEURS[cible[1]] if cible else 0
    if coup[4]:
        v += 800
    return v


def negamax(partie, profondeur, alpha, beta):
    """Note la position pour le joueur dont c'est le tour."""
    if profondeur == 0:
        s = evaluer(partie.plateau)
        return s if partie.trait == "w" else -s
    legaux = partie.coups_legaux()
    if not legaux:
        if partie.en_echec():
            return -(100000 + profondeur)      # échec et mat (plus c'est rapide, pire c'est)
        return 0                               # pat
    legaux.sort(key=lambda m: valeur_ordre(partie, m), reverse=True)
    meilleur = -INFINI
    for coup in legaux:
        valeur = -negamax(partie.jouer(coup), profondeur - 1, -beta, -alpha)
        if valeur > meilleur:
            meilleur = valeur
        if valeur > alpha:
            alpha = valeur
        if alpha >= beta:
            break
    return meilleur


def choisir_coup(partie, profondeur):
    legaux = partie.coups_legaux()
    random.shuffle(legaux)                     # pour varier les parties
    legaux.sort(key=lambda m: valeur_ordre(partie, m), reverse=True)
    meilleur = None
    meilleure_valeur = -INFINI
    for coup in legaux:
        valeur = -negamax(partie.jouer(coup), profondeur - 1, -INFINI, -meilleure_valeur)
        if valeur > meilleure_valeur:
            meilleure_valeur = valeur
            meilleur = coup
    return meilleur


# ----------------------------------------------------------------------
# AFFICHAGE
# ----------------------------------------------------------------------
SYMBOLES = {"K": "♚", "Q": "♛", "R": "♜", "B": "♝", "N": "♞", "P": "♟"}
IMAGES = {}


def image_piece(piece):
    """Fabrique (une seule fois) l'image d'une pièce."""
    if piece in IMAGES:
        return IMAGES[piece]
    couleur, type_ = piece[0], piece[1]
    image = pygame.Surface((CASE, CASE), pygame.SRCALPHA)
    if couleur == "w":
        remplissage, contour, ecart = (255, 255, 255), (20, 20, 20), 2
    else:
        remplissage, contour, ecart = (25, 25, 25), (190, 190, 190), 1
    centre = (CASE // 2, CASE // 2)
    if POLICE_PIECES:
        symbole = SYMBOLES[type_]
        fond = POLICE_PIECES.render(symbole, True, contour)
        devant = POLICE_PIECES.render(symbole, True, remplissage)
        for dx, dy in ((-ecart, 0), (ecart, 0), (0, -ecart), (0, ecart),
                       (-ecart, -ecart), (ecart, ecart), (-ecart, ecart), (ecart, -ecart)):
            image.blit(fond, fond.get_rect(center=(centre[0] + dx, centre[1] + dy)))
        image.blit(devant, devant.get_rect(center=centre))
    else:
        # Pas de police avec les symboles d'échecs : on dessine un rond avec une lettre
        pygame.draw.circle(image, remplissage, centre, 30)
        pygame.draw.circle(image, contour, centre, 30, 3)
        lettre = police_lettres.render(type_, True, contour)
        image.blit(lettre, lettre.get_rect(center=centre))
    IMAGES[piece] = image
    return image


def ecrire(texte, police_utilisee, couleur, centre):
    image = police_utilisee.render(texte, True, couleur)
    ecran.blit(image, image.get_rect(center=centre))


BOUTONS_MENU = [pygame.Rect(120, 270 + i * 85, 440, 65) for i in range(4)]
TEXTES_MENU = ["1 : Deux joueurs",
               "2 : Ordinateur facile",
               "3 : Ordinateur moyen",
               "4 : Ordinateur difficile (plus lent)"]
NOMS_MODES = {None: "Deux joueurs", 1: "Ordinateur facile",
              3: "Ordinateur moyen", 4: "Ordinateur difficile"}


def rect_promotion(k):
    """Le k-ième bouton du choix de promotion (dame, tour, fou, cavalier)."""
    return pygame.Rect(X0 + 140 + k * 90, Y0 + 4 * CASE - 45, 90, 90)


# ----------------------------------------------------------------------
# LE JEU (menu, clics, dessin)
# ----------------------------------------------------------------------
class Jeu:
    def __init__(self):
        self.etat = "menu"          # "menu" ou "jeu"
        self.profondeur = None      # None = deux joueurs, sinon niveau de l'ordinateur
        self.retourne = False       # échiquier retourné ?
        self.nouvelle_partie()

    def nouvelle_partie(self):
        self.partie = Partie()
        self.legaux = self.partie.coups_legaux()
        self.statut = "en_cours"
        self.echec = False
        self.selection = None       # case de la pièce choisie
        self.dernier_coup = None
        self.promotion = None       # coups en attente du choix de la pièce

    def jouer_coup(self, coup):
        self.partie = self.partie.jouer(coup)
        self.dernier_coup = coup[:4]
        self.selection = None
        self.promotion = None
        self.legaux = self.partie.coups_legaux()
        self.statut = self.partie.statut(self.legaux)
        self.echec = self.partie.en_echec()

    def ordi_doit_jouer(self):
        return (self.etat == "jeu" and self.profondeur is not None
                and self.partie.trait == "b" and self.statut == "en_cours")

    # --- Conversion case <-> position à l'écran --------------------------------
    def pos_ecran(self, r, c):
        if self.retourne:
            r, c = 7 - r, 7 - c
        return X0 + c * CASE, Y0 + r * CASE

    def case_depuis_pos(self, pos):
        x, y = pos
        c = (x - X0) // CASE
        r = (y - Y0) // CASE
        if not (0 <= r < 8 and 0 <= c < 8) or x < X0 or y < Y0:
            return None
        if self.retourne:
            r, c = 7 - r, 7 - c
        return r, c

    # --- Événements -------------------------------------------------------------------
    def evenement(self, ev):
        if ev.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if self.etat == "menu":
            choix = None
            if ev.type == pygame.KEYDOWN:
                touches = {pygame.K_1: 1, pygame.K_KP1: 1, pygame.K_2: 2, pygame.K_KP2: 2,
                           pygame.K_3: 3, pygame.K_KP3: 3, pygame.K_4: 4, pygame.K_KP4: 4}
                choix = touches.get(ev.key)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, rect in enumerate(BOUTONS_MENU):
                    if rect.collidepoint(ev.pos):
                        choix = i + 1
            if choix:
                self.profondeur = {1: None, 2: 1, 3: 3, 4: 4}[choix]
                self.retourne = False
                self.nouvelle_partie()
                self.etat = "jeu"
            return

        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_r:
                self.nouvelle_partie()
            elif ev.key == pygame.K_m:
                self.etat = "menu"
            elif ev.key == pygame.K_f:
                self.retourne = not self.retourne
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.clic(ev.pos)

    def clic(self, pos):
        if self.statut != "en_cours":
            return
        if self.profondeur is not None and self.partie.trait == "b":
            return                                   # c'est le tour de l'ordinateur

        # Choix de la pièce pour la promotion
        if self.promotion:
            for k, lettre in enumerate("QRBN"):
                if rect_promotion(k).collidepoint(pos):
                    for coup in self.promotion:
                        if coup[4] == lettre:
                            self.jouer_coup(coup)
                            return
            self.promotion = None                    # clic ailleurs : on annule
            return

        case = self.case_depuis_pos(pos)
        if case is None:
            self.selection = None
            return
        r, c = case

        # Une pièce est déjà choisie : est-ce qu'on clique sur une case où elle peut aller ?
        if self.selection:
            sr, sc = self.selection
            coups = [m for m in self.legaux if (m[0], m[1], m[2], m[3]) == (sr, sc, r, c)]
            if len(coups) == 1:
                self.jouer_coup(coups[0])
                return
            if len(coups) > 1:                       # promotion : il faut choisir la pièce
                self.promotion = coups
                return

        # Sinon : on choisit une de nos pièces
        piece = self.partie.plateau[r][c]
        if piece and piece[0] == self.partie.trait:
            self.selection = (r, c)
        else:
            self.selection = None

    # --- Dessin --------------------------------------------------------------------------
    def texte_statut(self):
        trait = self.partie.trait
        contre_ordi = self.profondeur is not None
        if self.statut == "mat":
            if contre_ordi:
                return "Échec et mat ! Tu as gagné !" if trait == "b" else "Échec et mat ! L'ordinateur gagne"
            return "Échec et mat ! Les " + ("noirs" if trait == "w" else "blancs") + " gagnent"
        if self.statut == "pat":
            return "Pat : match nul"
        if self.statut == "nulle50":
            return "Match nul (règle des 50 coups)"
        if self.statut == "nulle_materiel":
            return "Match nul (matériel insuffisant)"
        if contre_ordi:
            texte = "À toi de jouer" if trait == "w" else "L'ordinateur réfléchit..."
        else:
            texte = "Aux blancs de jouer" if trait == "w" else "Aux noirs de jouer"
        if self.echec:
            texte += "  -  ÉCHEC !"
        return texte

    def dessiner_menu(self):
        ecrire("ÉCHECS", grosse_police, BLANC, (LARGEUR // 2, 140))
        ecrire("Choisis un mode de jeu", police, GRIS, (LARGEUR // 2, 225))
        for rect, texte in zip(BOUTONS_MENU, TEXTES_MENU):
            pygame.draw.rect(ecran, (70, 75, 105), rect, border_radius=10)
            ecrire(texte, police, BLANC, rect.center)

    def dessiner(self):
        ecran.fill(FOND)
        if self.etat == "menu":
            self.dessiner_menu()
            return

        ecrire(self.texte_statut(), police, BLANC, (LARGEUR // 2, 24))
        ecrire("Mode : " + NOMS_MODES[self.profondeur], petite_police, GRIS, (LARGEUR // 2, 50))

        # Les 64 cases
        for r in range(8):
            for c in range(8):
                x, y = self.pos_ecran(r, c)
                couleur = CLAIR if (r + c) % 2 == 0 else FONCE
                pygame.draw.rect(ecran, couleur, (x, y, CASE, CASE))

        # Surbrillances (dernier coup, échec, pièce choisie, coups possibles)
        calque = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        if self.dernier_coup:
            d = self.dernier_coup
            for (r, c) in ((d[0], d[1]), (d[2], d[3])):
                x, y = self.pos_ecran(r, c)
                pygame.draw.rect(calque, (255, 235, 0, 90), (x, y, CASE, CASE))
        if self.echec:
            rr, rc = trouver_roi(self.partie.plateau, self.partie.trait)
            x, y = self.pos_ecran(rr, rc)
            pygame.draw.rect(calque, (255, 0, 0, 140), (x, y, CASE, CASE))
        if self.selection:
            x, y = self.pos_ecran(*self.selection)
            pygame.draw.rect(calque, (0, 120, 255, 120), (x, y, CASE, CASE))
            deja = set()
            for m in self.legaux:
                if (m[0], m[1]) == self.selection and (m[2], m[3]) not in deja:
                    deja.add((m[2], m[3]))
                    x, y = self.pos_ecran(m[2], m[3])
                    centre = (x + CASE // 2, y + CASE // 2)
                    if self.partie.plateau[m[2]][m[3]] != "":
                        pygame.draw.circle(calque, (0, 0, 0, 90), centre, 38, 6)   # prise
                    else:
                        pygame.draw.circle(calque, (0, 0, 0, 80), centre, 12)      # déplacement
        ecran.blit(calque, (0, 0))

        # Les pièces
        for r in range(8):
            for c in range(8):
                piece = self.partie.plateau[r][c]
                if piece:
                    ecran.blit(image_piece(piece), self.pos_ecran(r, c))

        # Les coordonnées (a-h et 1-8)
        for k in range(8):
            lettre = chr(97 + 7 - k) if self.retourne else chr(97 + k)
            chiffre = k + 1 if self.retourne else 8 - k
            ecrire(lettre, petite_police, GRIS, (X0 + k * CASE + CASE // 2, Y0 + 8 * CASE + 14))
            ecrire(str(chiffre), petite_police, GRIS, (X0 // 2, Y0 + k * CASE + CASE // 2))

        # Choix de la pièce pour la promotion
        if self.promotion:
            panneau = pygame.Rect(X0 + 130, Y0 + 4 * CASE - 75, 380, 150)
            pygame.draw.rect(ecran, (50, 50, 70), panneau, border_radius=12)
            pygame.draw.rect(ecran, BLANC, panneau, 3, border_radius=12)
            ecrire("Promotion : choisis une pièce", petite_police, BLANC, (panneau.centerx, panneau.y + 18))
            for k, lettre in enumerate("QRBN"):
                rect = rect_promotion(k)
                pygame.draw.rect(ecran, (190, 190, 170), rect.inflate(-6, -6), border_radius=8)
                ecran.blit(image_piece(self.partie.trait + lettre), (rect.x + 5, rect.y + 5))

        ecrire("R : nouvelle partie     M : menu     F : retourner l'échiquier",
               petite_police, GRIS, (LARGEUR // 2, 745))


# ----------------------------------------------------------------------
# PROGRAMME PRINCIPAL
# ----------------------------------------------------------------------
def main():
    jeu = Jeu()
    while True:
        horloge.tick(30)
        for evenement in pygame.event.get():
            jeu.evenement(evenement)

        jeu.dessiner()
        pygame.display.flip()

        # L'ordinateur joue (l'écran vient d'être affiché avec "L'ordinateur réfléchit...")
        if jeu.ordi_doit_jouer():
            coup = choisir_coup(jeu.partie, jeu.profondeur)
            jeu.jouer_coup(coup)


if __name__ == "__main__":
    main()
