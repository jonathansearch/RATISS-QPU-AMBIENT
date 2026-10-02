#!/usr/bin/env python3
"""
Rendu PNG du PCB NV ambiant — pour affichage direct dans un README GitHub.

Pourquoi du PNG et pas du HTML/JS :
    GitHub ne rend que des images dans un README. Le JavaScript y est
    bloqué, les SVG animés aussi. Une image est donc la seule façon
    d'avoir un visuel qui s'affiche sans clic ni redirection.

Ce que le script fait :
    - décrit le banc NV (table optique, laser, chemin optique, objectif,
      diamant, antenne micro-onde, APD, rack) sous forme de boîtes 3D
    - les projette en isométrique
    - les trie par profondeur (peintre) et les dessine avec éclairage
    - ajoute les étiquettes et les faisceaux
    - écrit un PNG à fond transparent

Usage :
    python rendre_pcb.py

Sortie :
    pcb-nv-3d.png              vue principale, fond transparent
    pcb-nv-3d-eclate.png       vue éclatée
    pcb-nv-3d-1200.png         version large pour bannière
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ══════════════════════════════════════════════════════════════════
# PALETTE — reprise de l'emblème RATISS
# ══════════════════════════════════════════════════════════════════
TEAL      = (45, 212, 191)
TEAL_DARK = (14, 107, 102)
TEAL_DEEP = (6,  60,  58)
PAPER     = (238, 252, 249)
INK       = (4,  16,  15)

# Matériaux du banc
C_ALU     = (176, 186, 198)
C_ALU_D   = (120, 130, 144)
C_BLACK   = (26,  28,  34)
C_GOLD    = (216, 168, 74)
C_COPPER  = (184, 115, 51)
C_GLASS   = (150, 220, 235)
C_DIAMOND = (200, 240, 255)
C_PCB     = (16,  74,  56)
C_LASER   = (34,  197, 94)
C_APD     = (168, 85,  247)
C_MW      = (250, 146, 60)
C_SCREEN  = (34, 211, 238)
C_TABLE   = (52,  60,  72)


def shade(col: tuple[int, int, int], k: float) -> tuple[int, int, int]:
    """Éclaircit (k>1) ou assombrit (k<1) une couleur."""
    return tuple(int(max(0, min(255, c * k))) for c in col)


# Facteur de sur-échantillonnage du rendu : on dessine en 2× puis on
# réduit, ce qui donne un anti-aliasing propre sur les arêtes.
# Les coordonnées projetées sont donc 2× trop grandes pour l'image
# finale ; les étiquettes divisent par ce facteur.
SUR_ECHANTILLONNAGE = 2


# ══════════════════════════════════════════════════════════════════
# PROJECTION ISOMÉTRIQUE
# ══════════════════════════════════════════════════════════════════
class Iso:
    """Projection isométrique avec azimut et élévation réglables."""

    def __init__(self, azimut_deg=-38.0, elev_deg=26.0, echelle=1.0):
        a = math.radians(azimut_deg)
        e = math.radians(elev_deg)
        # Base de projection
        self.ex = np.array([math.cos(a), -math.sin(a), 0.0])
        self.ey = np.array([
            -math.sin(a) * math.sin(e),
            -math.cos(a) * math.sin(e),
            math.cos(e),
        ])
        # Axe de profondeur (pour le tri peintre)
        self.ez = np.array([
            math.sin(a) * math.cos(e),
            math.cos(a) * math.cos(e),
            math.sin(e),
        ])
        self.echelle = echelle
        self.origine = np.zeros(2)

    def proj(self, p) -> tuple[float, float]:
        p = np.asarray(p, dtype=float)
        x = float(p @ self.ex) * self.echelle + self.origine[0]
        y = -float(p @ self.ey) * self.echelle + self.origine[1]
        return x, y

    def profondeur(self, p) -> float:
        return float(np.asarray(p, dtype=float) @ self.ez)


# ══════════════════════════════════════════════════════════════════
# BOÎTE 3D
# ══════════════════════════════════════════════════════════════════
@dataclass
class Boite:
    """Parallélépipède axis-aligné, centre + dimensions."""
    centre: tuple[float, float, float]
    taille: tuple[float, float, float]
    couleur: tuple[int, int, int]
    nom: str = ""
    # Décalage pour la vue éclatée
    explode: tuple[float, float, float] = (0, 0, 0)
    # Un nom de groupe : les boîtes d'un groupe s'éclatent ensemble
    groupe: str = ""
    alpha: float = 1.0

    def sommets(self) -> np.ndarray:
        cx, cy, cz = self.centre
        dx, dy, dz = (t / 2 for t in self.taille)
        ex, ey, ez = self.explode
        return np.array([
            [cx - dx + ex, cy - dy + ey, cz - dz + ez],
            [cx + dx + ex, cy - dy + ey, cz - dz + ez],
            [cx + dx + ex, cy + dy + ey, cz - dz + ez],
            [cx - dx + ex, cy + dy + ey, cz - dz + ez],
            [cx - dx + ex, cy - dy + ey, cz + dz + ez],
            [cx + dx + ex, cy - dy + ey, cz + dz + ez],
            [cx + dx + ex, cy + dy + ey, cz + dz + ez],
            [cx - dx + ex, cy + dy + ey, cz + dz + ez],
        ])

    def centre_monde(self) -> np.ndarray:
        return np.array(self.centre, dtype=float) + np.array(self.explode, dtype=float)


# Faces d'une boîte : (indices des 4 sommets, normale, facteur d'éclairage)
FACES = [
    ((4, 5, 6, 7), np.array([0, 0, 1.0]), 1.00),   # dessus
    ((0, 1, 5, 4), np.array([0, -1.0, 0]), 0.72),  # avant
    ((1, 2, 6, 5), np.array([1.0, 0, 0]), 0.86),   # droite
    ((3, 2, 6, 7), np.array([0, 1.0, 0]), 0.60),   # arrière
    ((0, 3, 7, 4), np.array([-1.0, 0, 0]), 0.66),  # gauche
]


# ══════════════════════════════════════════════════════════════════
# LE BANC NV — géométrie complète
# ══════════════════════════════════════════════════════════════════
def construire_banc() -> list[Boite]:
    """
    Décrit le banc de mesure NV d'après docs/ASSEMBLY_BENCH.md.

    Repère : X vers la droite, Y vers l'arrière, Z vers le haut.
    La table optique est à Z=0. Le faisceau est à Z=1.5.

    La table est volontairement compacte (11 × 6) : sur un banc réel,
    les composants occupent l'essentiel de la surface. Une table trop
    grande dilue la scène et les objets deviennent illisibles.
    """
    B: list[Boite] = []
    Z_TABLE = 0.0
    Z_F = 1.4          # hauteur du faisceau

    # ─── Table optique ───────────────────────────────────────────
    B.append(Boite((0, 0, Z_TABLE - 0.16), (11.0, 6.2, 0.32),
                   C_TABLE, "Table optique", groupe="table"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.append(Boite((sx * 4.6, sy * 2.5, Z_TABLE - 1.15),
                           (0.8, 0.8, 1.7), C_BLACK, "", groupe="table"))

    # ─── Laser 532 nm ────────────────────────────────────────────
    B.append(Boite((-4.3, 0, Z_F), (2.0, 1.0, 0.85),
                   C_LASER, "Laser 532 nm", groupe="laser"))
    for i in range(6):
        B.append(Boite((-4.3 + (i - 2.5) * 0.26, 0, Z_F + 0.55),
                       (0.09, 0.8, 0.22), shade(C_LASER, 0.8), "", groupe="laser"))
    B.append(Boite((-3.2, 0, Z_F), (0.32, 0.24, 0.24), C_ALU, "", groupe="laser"))
    B.append(Boite((-4.3, 0, Z_F - 1.0), (0.36, 0.36, 1.2), C_ALU_D, "", groupe="laser"))

    # ─── Chemin optique (faisceau à Z_F) ─────────────────────────
    B.append(Boite((-2.4, 0, Z_F), (0.10, 0.85, 0.85),
                   C_GLASS, "Miroir", groupe="optique"))
    B.append(Boite((-2.4, 0, Z_F - 1.0), (0.2, 0.2, 1.1), C_ALU_D, "", groupe="optique"))

    B.append(Boite((-1.6, 0, Z_F), (0.12, 0.6, 0.6),
                   C_GLASS, "Filtre 532", groupe="optique"))

    # Dichroïque 550 nm : la pièce maîtresse, inclinée
    B.append(Boite((-0.85, 0, Z_F), (0.09, 1.0, 1.0),
                   C_TEAL_LAME, "Dichroïque 550 nm", groupe="optique"))
    B.append(Boite((-0.85, 0, Z_F - 1.05), (0.22, 0.22, 1.1), C_ALU_D, "", groupe="optique"))

    B.append(Boite((-0.1, 0, Z_F), (0.12, 0.6, 0.6),
                   C_GLASS, "Filtre 650 nm", groupe="optique"))

    # ─── Objectif ×50, pointé vers le bas ────────────────────────
    B.append(Boite((-0.85, 0, Z_F - 0.95), (0.8, 0.8, 1.2),
                   C_ALU, "Objectif ×50", groupe="objectif"))
    B.append(Boite((-0.85, 0, Z_F - 1.62), (0.58, 0.58, 0.16),
                   C_GLASS, "", groupe="objectif"))

    # ─── Échantillon : platine XYZ + diamant ─────────────────────
    B.append(Boite((-0.85, 0, 0.5), (1.7, 1.7, 0.32),
                   C_ALU_D, "Platine XYZ", groupe="echantillon"))
    B.append(Boite((-0.85, 0, 0.74), (1.2, 1.2, 0.2),
                   shade(C_ALU, 0.95), "", groupe="echantillon"))
    B.append(Boite((-0.85, 0, 0.88), (0.75, 0.75, 0.12),
                   C_PCB, "", groupe="echantillon"))
    B.append(Boite((-0.85, 0, 1.03), (0.4, 0.4, 0.4),
                   C_DIAMOND, "Diamant NV", groupe="echantillon"))

    # ─── Antenne micro-onde + aimants ────────────────────────────
    B.append(Boite((-0.85, 0, 1.28), (1.0, 1.35, 0.10),
                   C_PCB, "", groupe="mw"))
    B.append(Boite((-0.85, 0, 1.40), (0.07, 1.05, 0.07),
                   C_MW, "Antenne µ-onde", groupe="mw"))
    for sx in (-1, 1):
        B.append(Boite((-0.85 + sx * 1.15, 0, 1.15), (0.5, 0.65, 0.65),
                       shade(C_ALU_D, 0.7), "", groupe="mw"))

    # ─── APD ─────────────────────────────────────────────────────
    B.append(Boite((1.3, 0, Z_F), (1.5, 1.2, 1.2),
                   C_APD, "APD", groupe="apd"))
    B.append(Boite((1.3, 0, Z_F + 0.8), (1.05, 0.95, 0.4),
                   shade(C_APD, 0.7), "", groupe="apd"))
    B.append(Boite((1.3, 0, Z_F - 1.05), (0.3, 0.3, 1.1), C_ALU_D, "", groupe="apd"))

    # ─── Lentille de focalisation vers l'APD ─────────────────────
    B.append(Boite((0.55, 0, Z_F), (0.14, 0.55, 0.55),
                   C_GLASS, "", groupe="optique"))

    # ─── Rack électronique (arrière gauche) ──────────────────────
    B.append(Boite((-3.4, -2.1, 1.4), (2.4, 1.3, 2.8),
                   C_BLACK, "Rack", groupe="rack"))
    for i in range(5):
        B.append(Boite((-3.4, -1.42, 2.45 - i * 0.52), (2.1, 0.06, 0.4),
                       shade(C_ALU, 0.85), "", groupe="rack"))
    for i in range(5):
        col = [C_LASER, C_SCREEN, C_GOLD, C_APD, C_MW][i]
        B.append(Boite((-4.25, -1.38, 2.45 - i * 0.52), (0.13, 0.05, 0.13),
                       col, "", groupe="rack"))

    # ─── Écran de contrôle (arrière droite) ──────────────────────
    B.append(Boite((2.8, -2.0, 2.4), (2.0, 0.10, 1.4),
                   C_SCREEN, "Écran", groupe="ecran"))
    B.append(Boite((2.8, -2.0, 1.4), (0.25, 0.25, 1.1), C_ALU_D, "", groupe="ecran"))

    # ─── Parois de l'enceinte de protection ──────────────────────
    # Très fines et translucides : elles suggèrent le confinement
    # sans masquer le banc.
    B.append(Boite((0, 3.1, 1.6), (11.0, 0.04, 3.2),
                   C_TEAL_PAROI, "", groupe="enceinte", alpha=0.22))
    B.append(Boite((-5.5, 0, 1.6), (0.04, 6.2, 3.2),
                   C_TEAL_PAROI, "", groupe="enceinte", alpha=0.22))

    return B


C_TEAL_LAME = (94, 234, 212)
C_TEAL_PAROI = (30, 90, 88)


# ══════════════════════════════════════════════════════════════════
# RENDU
# ══════════════════════════════════════════════════════════════════
def rendre(
    boites: list[Boite],
    largeur: int,
    hauteur: int,
    iso: Iso,
    fond: tuple[int, int, int, int] | None = None,
    halo: bool = True,
    marge: float = 0.10,
) -> Image.Image:
    """Dessine les boîtes en isométrique, du fond vers l'avant.

    Étapes :
      1. on projette d'abord avec l'échelle 1 pour connaître l'étendue réelle
      2. on en déduit l'échelle et l'origine pour remplir l'image
      3. on redessine avec ces valeurs, du fond vers l'avant
    """

    # Sur-échantillonnage ×2 puis réduction : anti-aliasing propre
    SS = SUR_ECHANTILLONNAGE
    LW, LH = largeur * SS, hauteur * SS

    # ── 1. Étendue réelle à l'échelle 1 ─────────────────────────
    iso.echelle = 1.0
    iso.origine = np.zeros(2)
    pts = np.vstack([iso.proj(v) for b in boites for v in b.sommets()])
    minx, miny = pts.min(axis=0)
    maxx, maxy = pts.max(axis=0)
    etendue_x = max(maxx - minx, 1e-6)
    etendue_y = max(maxy - miny, 1e-6)

    # ── 2. Échelle et origine ───────────────────────────────────
    # Marge latérale plus large que la marge verticale : les colonnes
    # d'étiquettes se logent à gauche et à droite du banc.
    dispo_x = LW * (1 - 2 * marge)
    # En vertical, on réserve de la place pour la légende en bas :
    # le banc est décalé vers le haut du cadre.
    dispo_y = LH * (1 - 2 * marge) * 0.72
    iso.echelle = min(dispo_x / etendue_x, dispo_y / etendue_y)
    iso.origine = np.array([
        LW / 2 - (minx + etendue_x / 2) * iso.echelle,
        LH * 0.40 - (miny + etendue_y / 2) * iso.echelle,
    ])

    # ── 3. Rendu ────────────────────────────────────────────────
    # Important : PIL en mode "RGBA" REMPLACE les pixels, il ne les
    # mélange pas. On dessine donc chaque couche translucide sur une
    # image séparée, puis on compose avec alpha_composite.
    img = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))

    if fond is not None:
        img.paste(Image.new("RGBA", (LW, LH), fond), (0, 0))

    # Halo doux derrière le banc, sur sa propre couche
    if halo:
        couche = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
        dh = ImageDraw.Draw(couche, "RGBA")
        centre = np.vstack([iso.proj(b.centre_monde()) for b in boites]).mean(axis=0)
        for frac, alpha in ((1.00, 22), (0.70, 26), (0.44, 30)):
            rx = LW * 0.30 * frac
            ry = LH * 0.24 * frac
            dh.ellipse([centre[0] - rx, centre[1] - ry,
                        centre[0] + rx, centre[1] + ry],
                       fill=(*TEAL_DEEP, alpha))
        img = Image.alpha_composite(img, couche)
        d = ImageDraw.Draw(img, "RGBA")
    else:
        d = ImageDraw.Draw(img, "RGBA")

    # Tri peintre : les boîtes lointaines d'abord
    def cle(b: Boite) -> float:
        return iso.profondeur(b.centre_monde())

    # Les boîtes translucides vont sur une couche à part, composée à la fin
    opaques = [b for b in boites if b.alpha >= 0.99]
    translucides = [b for b in boites if b.alpha < 0.99]

    for b in sorted(opaques, key=cle):
        som = b.sommets()
        proj = [iso.proj(v) for v in som]
        for idx, normale, lum in sorted(FACES, key=lambda f: f[2]):
            if float(normale @ iso.ez) <= 0.01:
                continue
            poly = [proj[i] for i in idx]
            col = shade(b.couleur, lum)
            d.polygon(poly, fill=(*col, 255), outline=(*shade(col, 0.55), 255))
        haut = [proj[i] for i in (4, 5, 6, 7)]
        d.line(haut + [haut[0]], fill=(*shade(b.couleur, 1.30), 220),
               width=max(1, SS // 2))

    # Couche translucide (l'enceinte)
    if translucides:
        couche = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
        dt = ImageDraw.Draw(couche, "RGBA")
        for b in sorted(translucides, key=cle):
            som = b.sommets()
            proj = [iso.proj(v) for v in som]
            for idx, normale, lum in sorted(FACES, key=lambda f: f[2]):
                if float(normale @ iso.ez) <= 0.01:
                    continue
                poly = [proj[i] for i in idx]
                col = shade(b.couleur, lum)
                dt.polygon(poly, fill=(*col, int(255 * b.alpha)),
                           outline=(*shade(col, 1.2), int(220 * b.alpha)))
        img = Image.alpha_composite(img, couche)

    return img.resize((largeur, hauteur), Image.LANCZOS)


# ══════════════════════════════════════════════════════════════════
# ÉTIQUETTES
# ══════════════════════════════════════════════════════════════════
def charger_police(taille: int, gras: bool = False):
    """Cherche une police système ; replie sur la police par défaut."""
    noms = (
        ["seguisb.ttf", "segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"]
        if gras else
        ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"]
    )
    for n in noms:
        for base in (r"C:\Windows\Fonts", "/usr/share/fonts/truetype/dejavu",
                     "/System/Library/Fonts"):
            p = Path(base) / n
            if p.exists():
                try:
                    return ImageFont.truetype(str(p), taille)
                except Exception:
                    pass
    return ImageFont.load_default()


def ajouter_etiquettes(
    img: Image.Image,
    iso: Iso,
    entrees: list[tuple[str, tuple[float, float, float], str]],
    taille_police: int = 15,
    facteur: float = 1.0,
) -> Image.Image:
    """
    Numérote les objets sur la vue et place la légende en bas.

    Pourquoi des numéros plutôt que des lignes de rappel : sur une vue
    isométrique chargée, les lignes traversent l'image et deviennent
    illisibles. Un numéro sur l'objet + une légende rangée en bas est
    la convention des schémas techniques, et ça reste lisible.

    `facteur` : le rapport entre la taille finale de l'image et celle
    pour laquelle `iso` a été calibré. La fonction `rendre` calibre la
    projection sur une image sur-échantillonnée, puis la réduit ; sans
    ce facteur, les pastilles tombent à côté des objets.
    """
    d = ImageDraw.Draw(img, "RGBA")
    f_num = charger_police(max(11, taille_police - 2), gras=True)
    f_leg = charger_police(taille_police, gras=False)
    f_titre = charger_police(taille_police + 1, gras=True)

    M = 20
    r_num = 11          # rayon de la pastille numérotée

    # ── 1. Pastilles numérotées sur les objets ───────────────────
    positions = []
    for i, (texte, cible, couleur_hex) in enumerate(entrees, 1):
        x_ss, y_ss = iso.proj(cible)
        x, y = x_ss * facteur, y_ss * facteur
        col = tuple(int(couleur_hex[i2:i2 + 2], 16) for i2 in (1, 3, 5))
        # Pastille pleine, avec un liseré clair pour ressortir sur le fond
        d.ellipse([x - r_num, y - r_num, x + r_num, y + r_num],
                  fill=(*col, 255), outline=(*PAPER, 235), width=2)
        txt = str(i)
        bb = d.textbbox((0, 0), txt, font=f_num)
        d.text((x - (bb[2] - bb[0]) / 2 - bb[0],
                y - (bb[3] - bb[1]) / 2 - bb[1]), txt, font=f_num, fill=(6, 18, 17, 255))
        positions.append((i, texte, col))

    # ── 2. Légende en bas ────────────────────────────────────────
    # Largeur de chaque entrée : on mesure, puis on répartit en colonnes
    mes = []
    for i, texte, col in positions:
        bb = d.textbbox((0, 0), f"{i}. {texte}", font=f_leg)
        mes.append((i, texte, col, bb[2] - bb[0], bb[3] - bb[1]))
    larg_max = max(m[3] for m in mes)
    haut_ligne = max(m[4] for m in mes) + 12

    # Nombre de colonnes selon la largeur disponible
    dispo = img.width - 2 * M
    n_col = max(1, min(3, dispo // (larg_max + 46)))
    n_par_col = math.ceil(len(mes) / n_col)

    hauteur_legende = n_par_col * haut_ligne + 52
    y_base = img.height - hauteur_legende - M

    # Fond de la légende : bandeau sombre translucide
    bandeau = Image.new("RGBA", img.size, (0, 0, 0, 0))
    db = ImageDraw.Draw(bandeau, "RGBA")
    db.rounded_rectangle(
        [M, y_base - 14, img.width - M, img.height - M + 8],
        radius=10, fill=(4, 20, 19, 232), outline=(*TEAL_DARK, 150), width=1)
    img = Image.alpha_composite(img, bandeau)
    d = ImageDraw.Draw(img, "RGBA")

    d.text((M + 16, y_base + 4), "LÉGENDE", font=f_titre, fill=(*TEAL, 235))

    y_txt = y_base + 34
    col_w = dispo // n_col
    for idx, (i, texte, col, tw, th) in enumerate(mes):
        c = idx // n_par_col
        r = idx % n_par_col
        px = M + 16 + c * col_w
        py = y_txt + r * haut_ligne
        # Pastille du numéro
        d.ellipse([px, py + 3, px + 15, py + 18], fill=(*col, 255))
        nb = d.textbbox((0, 0), str(i), font=f_num)
        d.text((px + 7.5 - (nb[2] - nb[0]) / 2 - nb[0],
                py + 10.5 - (nb[3] - nb[1]) / 2 - nb[1]),
               str(i), font=f_num, fill=(6, 18, 17, 255))
        d.text((px + 23, py), texte, font=f_leg, fill=(*PAPER, 242))

    return img


# ══════════════════════════════════════════════════════════════════
# SCÈNES
# ══════════════════════════════════════════════════════════════════
def scene_principale(largeur=1400, hauteur=840, eclate=False) -> Image.Image:
    boites = construire_banc()

    if eclate:
        # Vue éclatée : chaque groupe monte ET s'écarte latéralement.
        # Une simple élévation verticale ne suffit pas : les groupes
        # occupent les mêmes X/Y et se chevaucheraient en colonne.
        deplacements = {
            "table":       (0.0,  0.0,  0.0),
            "laser":       (-3.6, 0.0,  1.6),
            "optique":     (-1.5, 0.0,  4.0),
            "objectif":    (0.6,  0.0,  6.4),
            "echantillon": (2.6,  0.0,  8.8),
            "mw":          (4.6,  0.0,  11.2),
            "apd":         (6.6,  0.0,  6.4),
            "rack":        (-5.6, -1.0, 8.0),
            "ecran":       (1.6,  -1.6, 8.0),
            "enceinte":    (0.0,  0.0,  14.0),
        }
        for b in boites:
            b.explode = deplacements.get(b.groupe, (0, 0, 0))

    # Marge modérée : le banc remplit le cadre, la légende se loge en bas
    iso = Iso(azimut_deg=-58, elev_deg=30, echelle=1.0)
    img = rendre(boites, largeur, hauteur, iso,
                 fond=(3, 14, 14, 255), halo=True, marge=0.09)

    if eclate:
        entrees = [
            ("Enceinte de protection",   (0, 3.1, 15.6),      "#2dd4bf"),
            ("Antenne micro-onde",       (4.6, 0, 12.6),      "#fa923c"),
            ("Diamant NV + platine",     (2.6, 0, 10.2),      "#c8f0ff"),
            ("Objectif ×50 NA 0.7",      (0.6, 0, 7.6),       "#b0bac6"),
            ("Dichroïque 550 nm",        (-1.5, 0, 5.4),      "#5eead4"),
            ("Laser 532 nm",             (-3.6, 0, 3.0),      "#22c55e"),
            ("APD — photons uniques",    (6.6, 0, 7.4),       "#a855f7"),
            ("Rack µ-onde + séquenceur", (-5.6, -1.0, 9.2),   "#ffc247"),
            ("Écran de contrôle",        (1.6, -1.6, 9.2),    "#22d3ee"),
            ("Table optique amortie",    (0, 2.6, -0.16),     "#78808c"),
        ]
    else:
        entrees = [
            ("Rack µ-onde + séquenceur", (-3.4, -1.42, 2.0), "#ffc247"),
            ("Écran de contrôle",        (2.8, -2.0, 2.9),   "#22d3ee"),
            ("Laser 532 nm",             (-4.3, 0.6, 1.6),   "#22c55e"),
            ("Miroir de renvoi",         (-2.4, 0.7, 1.4),   "#96dceb"),
            ("Dichroïque 550 nm",        (-0.85, 1.0, 1.4),  "#5eead4"),
            ("Objectif ×50 NA 0.7",      (-0.85, 0, 0.1),    "#b0bac6"),
            ("Antenne micro-onde",       (-0.85, 0, 1.45),   "#fa923c"),
            ("Diamant NV",               (-0.85, 0, 1.05),   "#c8f0ff"),
            ("APD — photons uniques",    (1.3, 0.6, 1.4),    "#a855f7"),
            ("Table optique amortie",    (-3.6, 2.6, -0.16), "#78808c"),
        ]

    # `rendre` calibre `iso` sur une image 2× plus grande puis la réduit :
    # les étiquettes doivent donc appliquer le facteur inverse.
    img = ajouter_etiquettes(img, iso, entrees, taille_police=15,
                             facteur=1.0 / SUR_ECHANTILLONNAGE)
    return img


# ══════════════════════════════════════════════════════════════════
# PROGRAMME
# ══════════════════════════════════════════════════════════════════
def main():
    """
    Écrit les PNG dans un dossier de sortie.

    Note sur le dossier : selon l'environnement, le processus Python peut
    être autorisé à écrire dans le workspace, ou seulement dans le dossier
    temporaire. On essaie le workspace d'abord, et on se replie sur temp
    en imprimant le chemin réel pour que l'appelant puisse copier.
    """
    import os
    import tempfile

    if __name__ == "__main__" and "__file__" in globals():
        base = Path(__file__).resolve().parent
    else:
        base = Path.cwd()

    # On teste l'écriture réelle plutôt que de supposer
    def ecrivable(d: Path) -> bool:
        try:
            d.mkdir(parents=True, exist_ok=True)
            t = d / "_test.tmp"
            t.write_text("x", encoding="utf-8")
            t.unlink()
            return True
        except Exception:
            return False

    if ecrivable(base):
        sortie = base
    else:
        sortie = Path(tempfile.gettempdir()) / "ratiss-pcb"
        sortie.mkdir(parents=True, exist_ok=True)
        print("  (ecriture impossible dans le workspace : sortie dans le temp)")

    print("Rendu du banc NV — RATISS-QPU-AMBIENT")
    print(f"Dossier de sortie : {sortie}\n")

    scenes = [
        ("pcb-nv-3d.png",        1400, 840, False),
        ("pcb-nv-3d-1200.png",   1200, 720, False),
        ("pcb-nv-3d-eclate.png", 1400, 840, True),
    ]

    for nom, w, h, ecl in scenes:
        print(f"  {nom:26} {w}x{h} …", end=" ", flush=True)
        img = scene_principale(w, h, eclate=ecl)
        chemin = sortie / nom
        img.save(chemin, "PNG", optimize=True)
        ko = chemin.stat().st_size / 1024
        print(f"{ko:.0f} Ko")

    print("\nFichiers ecrits dans :", sortie)


if __name__ == "__main__":
    main()
