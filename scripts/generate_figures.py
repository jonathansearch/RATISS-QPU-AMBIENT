"""Génère toutes les figures de la documentation RATISS-QPU-AMBIENT.

Produit des images PNG réelles (matplotlib) dans docs/images/ :
1. Schéma optique du banc (chemin laser → diamant → APD)
2. Les 4 séquences de pulses (ODMR, Rabi, Ramsey, Hahn echo) en chronogrammes
3. Courbes de mesure simulées : ODMR (dip), Rabi (oscillations), Ramsey (franges),
   Hahn (écho) — issues du banc virtuel
4. Sphère de Bloch + trajectoire de décohérence (P_sig)
5. Comparatif d'architectures (opérations cohérentes)

Usage : python scripts/generate_figures.py
Les images sont ensuite référencées dans docs/GUIDE_VISUEL.md.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")  # pas d'affichage — génération de fichiers
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

from ratiss_qpu.nv_center import NVCenter
from bench.virtual_bench import VirtualBench

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "images")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 110,
    "font.size": 11,
    "axes.grid": True,
    "grid.alpha": 0.3,
})

# Palette RATIS Labs
RATIS_DARK = "#0b1f3a"
RATIS_GREEN = "#1f9d55"
RATIS_GOLD = "#e0a800"
RATIS_RED = "#c0392b"


def save(fig, name, facecolor="white"):
    path = os.path.join(OUT, name)
    fig.savefig(path, bbox_inches="tight", facecolor=facecolor)
    plt.close(fig)
    print("généré :", name)


# ---------------------------------------------------------------- optique ---
def fig_schema_optique():
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    ax.set_title("Schéma optique du banc NV (microscope confocal épi-fluorescence)",
                 fontsize=13, fontweight="bold")

    def box(x, y, w, h, text, color):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor="black",
                               linewidth=1.5, zorder=2))
        ax.text(x + w/2, y + h/2, text, ha="center", va="center",
                fontsize=9, zorder=3, fontweight="bold")

    box(0.2, 3.0, 1.6, 0.8, "Laser\n532 nm\n(vert)", "#bfe6bf")
    box(4.2, 2.8, 0.5, 1.2, "Lame\ndichroïque\n550 nm", "#ffe08a")
    box(4.0, 1.2, 0.9, 0.7, "Objectif\n×50", "#cfe0ff")
    box(3.6, 0.2, 1.7, 0.6, "Diamant CVD\n+ centres NV", "#ffb3b3")
    box(6.5, 2.9, 1.4, 0.8, "Filtre\n650 nm", "#ffd9b3")
    box(8.4, 2.9, 1.3, 0.8, "APD\n(compteur\nde photons)", "#e0b3ff")
    box(5.6, 0.2, 1.4, 0.6, "Antenne\nµ-onde 2.87 GHz", "#d3f4e0")

    ax.annotate("", xy=(4.2, 3.4), xytext=(1.8, 3.4),
                arrowprops=dict(arrowstyle="->", color="green", lw=2.5))
    ax.text(2.9, 3.6, "excitation 532 nm", color="green", fontsize=9, ha="center")
    ax.annotate("", xy=(4.45, 1.9), xytext=(4.45, 2.8),
                arrowprops=dict(arrowstyle="->", color="green", lw=2.5))
    ax.annotate("", xy=(6.5, 3.3), xytext=(4.7, 3.3),
                arrowprops=dict(arrowstyle="->", color="red", lw=2.5))
    ax.text(5.6, 4.0, "fluorescence 637–800 nm", color="red", fontsize=9, ha="center")
    ax.annotate("", xy=(8.4, 3.3), xytext=(7.9, 3.3),
                arrowprops=dict(arrowstyle="->", color="red", lw=2.5))
    ax.annotate("", xy=(5.3, 0.6), xytext=(5.6, 0.5),
                arrowprops=dict(arrowstyle="->", color="purple", lw=2, linestyle="--"))
    ax.text(7.6, 0.4, "La lame dichroïque réfléchit le VERT vers le diamant\n"
                      "et laisse passer le ROUGE vers le détecteur.",
            fontsize=9, style="italic", ha="left",
            bbox=dict(boxstyle="round", facecolor="#fffbe6", edgecolor="#ccc"))
    save(fig, "01_schema_optique.png")


# ------------------------------------------------------------- séquences ---
def _draw_sequence(ax, events, title):
    colors = {"laser": "green", "mw": "purple", "apd": "red"}
    ypos = {"laser": 2, "mw": 1, "apd": 0}
    labels = {"laser": "Laser", "mw": "µ-onde", "apd": "Porte APD"}
    tmax = max(t1 for _, t1, _, _ in events) * 1.05
    for t0, t1, ch, lab in events:
        ax.fill_between([t0, t1], ypos[ch], ypos[ch] + 0.7,
                        color=colors[ch], alpha=0.7)
        if lab:
            ax.text((t0+t1)/2, ypos[ch]+0.35, lab, ha="center", va="center",
                    fontsize=8, color="white", fontweight="bold")
    for ch, y in ypos.items():
        ax.text(-0.01*tmax, y+0.35, labels[ch], ha="right", va="center",
                fontsize=9, fontweight="bold")
    ax.set_ylim(-0.3, 3.1); ax.set_yticks([])
    ax.set_xlabel("temps →")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlim(-0.02*tmax, tmax)


def fig_sequences():
    fig, axs = plt.subplots(4, 1, figsize=(11, 10))
    fig.suptitle("Les 4 séquences de mesure du banc NV (chronogrammes de pulses)",
                 fontsize=13, fontweight="bold", y=0.995)

    _draw_sequence(axs[0], [(0, 10, "laser", ""), (0, 10, "mw", "ON"),
                            (0, 10, "apd", "comptage")],
                   "1. ODMR continu — on balaie la FRÉQUENCE µ-onde, le dip localise la résonance")

    _draw_sequence(axs[1], [(0, 3, "laser", "init"), (3, 3.6, "mw", "τ"),
                            (3.6, 4.0, "laser", ""), (3.6, 4.0, "apd", "")],
                   "2. Rabi — pulse µ-onde de durée τ variable → oscillations (mesure Ω)")

    _draw_sequence(axs[2], [(0, 3, "laser", "init"), (3, 3.3, "mw", "π/2"),
                            (3.3, 5.3, "mw", ""), (5.3, 5.6, "mw", "π/2"),
                            (5.6, 6.0, "laser", ""), (5.6, 6.0, "apd", "")],
                   "3. Ramsey — π/2 … τ libre … π/2 → franges (mesure T2*)")
    axs[2].annotate("évolution libre τ", xy=(4.3, 1.35), ha="center", fontsize=8,
                    style="italic", color="purple")

    _draw_sequence(axs[3], [(0, 3, "laser", "init"), (3, 3.3, "mw", "π/2"),
                            (4.8, 5.3, "mw", "π"), (6.8, 7.1, "mw", "π/2"),
                            (7.1, 7.5, "laser", ""), (7.1, 7.5, "apd", "")],
                   "4. Hahn echo — π/2 … τ … π … τ … π/2 → écho (mesure T2)")
    axs[3].annotate("τ", xy=(4.0, 1.35), ha="center", fontsize=9, color="purple")
    axs[3].annotate("τ", xy=(6.0, 1.35), ha="center", fontsize=9, color="purple")
    axs[3].annotate("le pulse π\nrefocalise", xy=(5.05, 1.75), ha="center",
                    fontsize=7, color="darkred")

    fig.tight_layout(rect=[0, 0, 1, 0.98])
    save(fig, "02_sequences_pulses.png")


# ---------------------------------------------------------------- mesures ---
def fig_mesures():
    nv = NVCenter(b_tesla=0.05, rabi_hz=2.0e6)
    b = VirtualBench(nv=nv, fluorescence_ms0=8e6, contrast=0.3, repetitions=2000, seed=1)

    fig, axs = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle("Mesures du banc NV (données du banc virtuel — bruit de photon réaliste)",
                 fontsize=13, fontweight="bold")

    f, c = b.sweep_odmr(1.40e9, 1.54e9, 100)
    axs[0, 0].plot((f-1.47e9)/1e6, c, "o-", ms=3, color="darkred")
    axs[0, 0].set_title("ODMR — dip à la résonance (Zeeman 1.47 GHz)")
    axs[0, 0].set_xlabel("fréquence − 1.47 GHz (MHz)"); axs[0, 0].set_ylabel("photons")

    t, c = b.sweep_rabi(3.0e-6, 100)
    axs[0, 1].plot(t*1e6, c, "o-", ms=3, color="purple")
    axs[0, 1].set_title("Rabi — oscillations (Ω ≈ 2 MHz)")
    axs[0, 1].set_xlabel("durée pulse µ-onde (µs)"); axs[0, 1].set_ylabel("photons")

    t, c = b.sweep_ramsey(15e-6, 120, t2star_s=3e-6, detuning_hz=1.0e6)
    axs[1, 0].plot(t*1e6, c, "o-", ms=3, color="teal")
    axs[1, 0].set_title("Ramsey — franges amorties (T2* ≈ 3 µs)")
    axs[1, 0].set_xlabel("temps libre τ (µs)"); axs[1, 0].set_ylabel("photons")

    t, c = b.sweep_hahn(200e-6, 100, t2_s=50e-6)
    axs[1, 1].plot(t*1e6, c, "o-", ms=3, color="darkgreen")
    axs[1, 1].set_title("Hahn echo — décroissance exponentielle (T2 ≈ 50 µs)")
    axs[1, 1].set_xlabel("temps τ (µs)"); axs[1, 1].set_ylabel("photons")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    save(fig, "03_mesures_banc.png")


# ---------------------------------------------------------------- Bloch ---
def fig_bloch():
    from ratiss_qpu.coherence import DecoherenceModel, bloch_trajectory
    from ratiss_qpu.qstate import bloch_state, X

    fig = plt.figure(figsize=(12, 5.5))

    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    u, v = np.mgrid[0:2*np.pi:40j, 0:np.pi:20j]
    x, y, z = np.cos(u)*np.sin(v), np.sin(u)*np.sin(v), np.cos(v)
    ax1.plot_wireframe(x, y, z, color="lightblue", alpha=0.25, linewidth=0.4)

    model = DecoherenceModel(t1_300k_s=1e-3, t2_300k_s=0.5e-3)
    s = bloch_state(np.pi/2, 0.0)
    rho0 = np.outer(s, s.conj())
    traj = bloch_trajectory(rho0, 0.5*np.pi*X, 8e-4, model, 300.0, n_points=150)
    ax1.plot(traj[:, 0], traj[:, 1], traj[:, 2], color="red", lw=2.5,
             label="trajectoire sous décohérence")
    ax1.scatter(*traj[0], color="green", s=60, label="état initial (pur, surface)")
    ax1.scatter(*traj[-1], color="black", s=60, label="état final (mixte, centre)")
    ax1.set_title("Sphère de Bloch — la décohérence\ntire l'état vers le centre (P_sig)")
    ax1.legend(fontsize=7, loc="upper left")
    ax1.set_box_aspect((1, 1, 1))

    ax2 = fig.add_subplot(1, 2, 2)
    radii = np.linalg.norm(traj, axis=1)
    ts = np.linspace(0, 8e-4, len(radii))
    ax2.plot(ts*1e6, radii, color="red", lw=2.5)
    ax2.axhline(1.0, color="green", linestyle="--", label="état pur (cohérent)")
    ax2.axhline(0.0, color="black", linestyle="--", label="état mixte (décohéré)")
    ax2.fill_between(ts*1e6, radii, 1.0, color="orange", alpha=0.2,
                     label="cohérence perdue")
    ax2.set_xlabel("temps (µs)"); ax2.set_ylabel("rayon de Bloch ‖r‖")
    ax2.set_title("P_sig quantique = contraction du rayon de Bloch")
    ax2.set_ylim(-0.05, 1.05); ax2.legend(fontsize=8)

    fig.tight_layout()
    save(fig, "04_sphere_bloch.png")


# ---------------------------------------------------------- architectures ---
def fig_architectures():
    from ratiss_qpu.benchmark import compare_architectures
    rows = compare_architectures()
    names = [r[0] for r in rows]
    ops = [r[3] for r in rows]
    temps = [r[4] for r in rows]
    colors = ["#d62728" if "NV" in n else "#1f77b4" for n in names]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(range(len(names)), ops, color=colors, alpha=0.8)
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=10)
    ax.set_xscale("log")
    ax.set_xlabel("Opérations cohérentes possibles (T2 / t_porte) — échelle log")
    ax.set_title("Comparatif d'architectures QPU — le NV ambiant (rouge) "
                 "rivalise avec le supraconducteur", fontsize=12, fontweight="bold")
    for i, (op, tp) in enumerate(zip(ops, temps)):
        ax.text(op, i, f"  {op:.0e} ops @ {tp:.0f}K", va="center", fontsize=9)
    ax.invert_yaxis()
    ax.text(0.02, 0.02,
            "Le supraconducteur (15 mK) ne fait PAS mieux que le NV ¹²C à 300 K.\n"
            "Le froid extrême est un contournement, pas une supériorité.",
            transform=ax.transAxes, fontsize=9, style="italic",
            bbox=dict(boxstyle="round", facecolor="#fffbe6", edgecolor="#ccc"))
    fig.tight_layout()
    save(fig, "05_comparatif_architectures.png")


# ================================================== 6. PLAN MÉCANIQUE BANC
def fig_plan_mecanique():
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.5); ax.axis("off")
    ax.set_title("PLAN DE CONCEPTION MÉCANIQUE — Table optique du banc NV\n"
                 "Layout sur plaque à trous (vue de dessus) — cage système + périmètre laser",
                 fontsize=12.5, fontweight="bold", color=RATIS_DARK)

    # Table optique
    ax.add_patch(Rectangle((0.5, 0.6), 11, 6.0, facecolor="#e8ecf1",
                           edgecolor=RATIS_DARK, linewidth=2.5, zorder=1))
    # grille de trous M6
    for gx in np.arange(1.0, 11.5, 0.6):
        for gy in np.arange(1.0, 6.4, 0.6):
            ax.plot(gx, gy, ".", color="#b9c2cc", ms=3, zorder=1)
    ax.text(6.0, 6.35, "Plaque optique à trous M6 (pas 25 mm) — sur pieds amortisseurs",
            ha="center", fontsize=9, style="italic", color=RATIS_DARK)

    def cbox(x, y, w, h, text, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                    facecolor=fc, edgecolor=RATIS_DARK,
                                    linewidth=1.5, zorder=3))
        ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=8,
                zorder=4, fontweight="bold")

    # Chemin optique : laser (gauche) → dichroïque → objectif/diamant (centre-bas)
    cbox(0.9, 4.4, 1.8, 1.2, "LASER 532 nm\n100 mW\n+ shutter", "#bfe6bf")
    cbox(3.4, 4.5, 1.0, 1.0, "Lame\ndichroïque\n550 nm", "#ffe08a")
    cbox(3.3, 2.4, 1.2, 1.2, "Objectif\n×50 NA 0.7\n(cage)", "#cfe0ff")
    cbox(3.0, 0.9, 1.8, 1.1, "Diamant CVD\nsur platine XYZ\n+ antenne µ-onde", "#ffb3b3")
    cbox(5.2, 4.5, 1.4, 1.0, "Filtre\n650 nm\n+ lentille tube", "#ffd9b3")
    cbox(7.4, 4.4, 1.8, 1.2, "APD\n(compteur\nphotons)", "#e0b3ff")
    cbox(7.4, 1.0, 2.0, 1.2, "Synthétiseur\nµ-onde 2.87 GHz\n+ ampli", "#d3f4e0")
    cbox(0.9, 1.0, 1.8, 1.2, "Pico RP2040\n(séquenceur\nde pulses)", "#fff3b0")

    # Flèches optiques
    ax.annotate("", xy=(3.4, 5.0), xytext=(2.7, 5.0),
                arrowprops=dict(arrowstyle="->", color="green", lw=2.5))
    ax.annotate("", xy=(3.9, 3.6), xytext=(3.9, 4.5),
                arrowprops=dict(arrowstyle="->", color="green", lw=2.5))
    ax.annotate("", xy=(5.2, 5.0), xytext=(4.4, 5.0),
                arrowprops=dict(arrowstyle="->", color="red", lw=2.5))
    ax.annotate("", xy=(7.4, 5.0), xytext=(6.6, 5.0),
                arrowprops=dict(arrowstyle="->", color="red", lw=2.5))
    # µ-onde vers diamant
    ax.annotate("", xy=(4.8, 1.5), xytext=(7.4, 1.6),
                arrowprops=dict(arrowstyle="->", color="purple", lw=2, linestyle="--"))
    # Pico contrôle
    ax.annotate("", xy=(3.0, 1.6), xytext=(2.7, 1.6),
                arrowprops=dict(arrowstyle="->", color=RATIS_GOLD, lw=1.5))

    ax.text(0.7, 0.15,
            "RÈGLES : tous les composants optiques à la même hauteur de faisceau (cage système) · "
            "diamant sur platine XYZ micrométrique · antenne µ-onde au plus près du diamant · "
            "laser en bout de table, faisceau confiné, lunettes OD4+ · câbles µ-onde courts (50 Ω).",
            fontsize=8.2, style="italic",
            bbox=dict(boxstyle="round", facecolor="#fffbe6", edgecolor=RATIS_GOLD))
    save(fig, "06_plan_mecanique.png")


# ================================================== 7. APPAREIL MONTÉ (banc)
def fig_appareil_monte():
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.set_xlim(0, 11); ax.set_ylim(0, 8); ax.axis("off")
    ax.set_title("RATISS-QPU-AMBIENT — Le banc de mesure NV une fois monté",
                 fontsize=13, fontweight="bold", color=RATIS_DARK)

    # Enceinte noire (boîte de protection laser)
    ax.add_patch(FancyBboxPatch((1.0, 1.2), 7.5, 5.6, boxstyle="round,pad=0.05",
                                facecolor="#1a1a1a", edgecolor="black",
                                linewidth=2.5, zorder=1))
    ax.text(4.75, 6.35, "Enceinte de protection laser (classe 1 fermée)",
            ha="center", fontsize=9, color="#ccc", style="italic")

    # Intérieur : colonne optique (microscope)
    ax.add_patch(Rectangle((2.0, 2.0), 1.0, 3.6, facecolor="#3a3a3a",
                           edgecolor="#666", zorder=2))  # colonne
    ax.add_patch(Rectangle((1.7, 5.0), 1.6, 0.7, facecolor="#4a4a4a",
                           edgecolor="#888", zorder=3))  # tourelle objectif
    ax.add_patch(Circle((2.5, 4.85), 0.28, facecolor="#2a5a8a",
                        edgecolor="#9ad", zorder=4))  # objectif
    # platine diamant
    ax.add_patch(Rectangle((1.8, 2.4), 1.4, 0.5, facecolor="#5a5a5a",
                           edgecolor="#999", zorder=3))
    ax.add_patch(Circle((2.5, 2.95), 0.22, facecolor="#ff7070",
                        edgecolor="#ffb0b0", zorder=4))  # diamant
    ax.text(2.5, 1.75, "Microscope confocal\n+ diamant NV", ha="center",
            fontsize=8, color="#ddd")

    # Laser
    ax.add_patch(Rectangle((4.2, 4.6), 1.8, 0.9, facecolor="#0d3d0d",
                           edgecolor="#3f3", zorder=3))
    ax.text(5.1, 5.05, "LASER 532 nm", ha="center", va="center", color="#7f7",
            fontsize=9, fontweight="bold", zorder=4)
    ax.annotate("", xy=(3.3, 5.35), xytext=(4.2, 5.05),
                arrowprops=dict(arrowstyle="->", color="#5f5", lw=2))

    # APD
    ax.add_patch(Rectangle((4.2, 2.2), 1.6, 1.0, facecolor="#3d0d3d",
                           edgecolor="#c5c", zorder=3))
    ax.text(5.0, 2.7, "APD", ha="center", va="center", color="#e8e",
            fontsize=10, fontweight="bold", zorder=4)

    # Électronique de contrôle (rack à droite)
    ax.add_patch(Rectangle((6.4, 2.0), 1.8, 3.4, facecolor="#22303f",
                           edgecolor="#4a6a8a", zorder=3))
    for i, lab in enumerate(["Synth µ-onde", "Pico RP2040", "Alim laser"]):
        ax.add_patch(Rectangle((6.55, 4.7 - i*1.0), 1.5, 0.7, facecolor="#0a1526",
                               edgecolor="#5a7a9a", zorder=4))
        ax.text(7.3, 5.05 - i*1.0, lab, ha="center", va="center", color="#9ad",
                fontsize=7.5, zorder=5)

    # Écran de contrôle
    ax.add_patch(Rectangle((8.8, 3.4), 1.9, 1.6, facecolor="#001a00",
                           edgecolor="lime", linewidth=2, zorder=3))
    ax.text(9.75, 4.55, "ODMR", ha="center", color="lime", fontsize=9,
            fontweight="bold", family="monospace", zorder=4)
    xs = np.linspace(8.95, 10.55, 60)
    dip = 0.4 - 0.28*np.exp(-((xs-9.75)/0.14)**2)
    ax.plot(xs, 3.7 + dip, color="lime", lw=1.5, zorder=4)
    ax.text(9.75, 3.15, "dip @ 2.87 GHz", ha="center", color="lime",
            fontsize=7, family="monospace", zorder=4)

    ax.text(5.5, 0.5, "Banc optique confocal épi-fluorescence — QPU à température ambiante",
            ha="center", fontsize=10, style="italic", color=RATIS_DARK)
    save(fig, "07_appareil_monte.png")


# ================================================== 8. VISUALISATION QPU
def fig_qpu_scientifique():
    """Visualisation ultra-détaillée du QPU NV — style reportage scientifique.

    Montre le diamant, le réseau cristallin, le centre NV, les niveaux d'énergie
    et la sphère de Bloch — l'anatomie complète du qubit à température ambiante.
    """
    fig = plt.figure(figsize=(14, 9))
    fig.patch.set_facecolor(RATIS_DARK)
    fig.suptitle("ANATOMIE D'UN QUBIT À TEMPÉRATURE AMBIANTE — Le centre NV du diamant",
                 fontsize=14, fontweight="bold", color="white", y=0.98)

    # --- Panneau 1 : le réseau cristallin + centre NV ---
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    ax1.set_facecolor(RATIS_DARK)
    rng = np.random.default_rng(2)
    # réseau diamant (carbone) : grille simple stylisée
    pts = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                pts.append((i, j, k))
    pts = np.array(pts, dtype=float)
    ax1.scatter(pts[:, 0], pts[:, 1], pts[:, 2], s=40, color="#4aa3df",
                alpha=0.5, label="Carbone ¹²C")
    # centre NV : lacune + azote
    nv = np.array([1.0, 1.0, 1.0])
    ax1.scatter(*nv, s=200, color=RATIS_GOLD, edgecolor="white", zorder=5,
                label="Centre NV (N + lacune)")
    ax1.scatter(1.0, 1.5, 1.0, s=120, color=RATIS_RED, zorder=5, label="Azote ¹⁴N")
    ax1.plot([1.0, 1.0], [1.0, 1.5], [1.0, 1.0], color="white", lw=1.5)
    ax1.set_title("Réseau diamant + centre NV", color="white", fontsize=10)
    ax1.legend(fontsize=6, loc="upper left", facecolor=RATIS_DARK,
               labelcolor="white")
    ax1.set_axis_off()

    # --- Panneau 2 : diagramme de niveaux d'énergie ---
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.set_facecolor(RATIS_DARK)
    ax2.set_title("Niveaux d'énergie du NV⁻ (spin S=1)", color="white", fontsize=10)
    # niveaux
    ax2.hlines(0.0, 0.1, 0.45, color="#4aa3df", lw=3)          # ms=0
    ax2.hlines(0.35, 0.55, 0.9, color=RATIS_RED, lw=3)         # ms=±1
    ax2.hlines(2.0, 0.1, 0.9, color=RATIS_GREEN, lw=3)         # état excité
    ax2.text(0.05, 0.0, "ms=0", color="#4aa3df", fontsize=9, va="center")
    ax2.text(0.92, 0.35, "ms=±1", color=RATIS_RED, fontsize=9, va="center")
    ax2.text(0.5, 2.1, "état excité ³E", color=RATIS_GREEN, fontsize=9, ha="center")
    # transitions
    ax2.annotate("", xy=(0.3, 2.0), xytext=(0.3, 0.0),
                 arrowprops=dict(arrowstyle="->", color="green", lw=2))
    ax2.text(0.32, 1.0, "pompage 532 nm", color="green", fontsize=7)
    ax2.annotate("", xy=(0.7, 0.0), xytext=(0.7, 2.0),
                 arrowprops=dict(arrowstyle="->", color="red", lw=2))
    ax2.text(0.72, 1.0, "fluorescence 637 nm", color="red", fontsize=7)
    ax2.annotate("", xy=(0.5, 0.35), xytext=(0.28, 0.0),
                 arrowprops=dict(arrowstyle="<->", color=RATIS_GOLD, lw=2))
    ax2.text(0.42, 0.15, "µ-onde 2.87 GHz\n(ODMR)", color=RATIS_GOLD, fontsize=7)
    ax2.set_xlim(0, 1.2); ax2.set_ylim(-0.3, 2.4)
    ax2.axis("off")

    # --- Panneau 3 : sphère de Bloch (qubit) ---
    ax3 = fig.add_subplot(2, 2, 3, projection="3d")
    ax3.set_facecolor(RATIS_DARK)
    u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:15j]
    x = np.cos(u)*np.sin(v); y = np.sin(u)*np.sin(v); z = np.cos(v)
    ax3.plot_wireframe(x, y, z, color="#3a5a80", alpha=0.3, linewidth=0.4)
    # vecteur d'état en superposition
    ax3.quiver(0, 0, 0, 0.7, 0.7, 0.0, color=RATIS_GOLD, lw=3,
               arrow_length_ratio=0.15)
    ax3.scatter(0, 0, 1, color="#4aa3df", s=50); ax3.text(0, 0, 1.15, "|0⟩",
                color="#4aa3df", fontsize=10, ha="center")
    ax3.scatter(0, 0, -1, color=RATIS_RED, s=50); ax3.text(0, 0, -1.25, "|1⟩",
                color=RATIS_RED, fontsize=10, ha="center")
    ax3.text(0.9, 0.9, 0, "|ψ⟩ = α|0⟩+β|1⟩", color=RATIS_GOLD, fontsize=8)
    ax3.set_title("Le qubit sur la sphère de Bloch", color="white", fontsize=10)
    ax3.set_axis_off()

    # --- Panneau 4 : la mesure ODMR (le signal) ---
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.set_facecolor(RATIS_DARK)
    f = np.linspace(2.75, 2.99, 300)
    signal = 1.0 - 0.25*np.exp(-((f-2.87)/0.008)**2)
    signal += 0.01*rng.standard_normal(len(f))
    ax4.plot(f, signal, color=RATIS_GREEN, lw=2)
    ax4.axvline(2.87, color=RATIS_GOLD, linestyle="--", lw=1.5)
    ax4.text(2.87, 0.82, " 2.87 GHz\n résonance", color=RATIS_GOLD, fontsize=8)
    ax4.set_title("Le signal ODMR — lire le spin par la lumière",
                  color="white", fontsize=10)
    ax4.set_xlabel("fréquence µ-onde (GHz)", color="white")
    ax4.set_ylabel("fluorescence (u.a.)", color="white")
    ax4.tick_params(colors="white")
    for spine in ax4.spines.values():
        spine.set_color("white")
    ax4.grid(alpha=0.2, color="white")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    save(fig, "08_qpu_scientifique.png", facecolor=RATIS_DARK)


# ================================================== 9. LOGO RATIS LABS
def fig_logo():
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    fig.patch.set_facecolor(RATIS_DARK)
    ax.set_facecolor(RATIS_DARK)

    for angle, col in [(0, RATIS_GREEN), (60, RATIS_GOLD), (120, "#4aa3df")]:
        th = np.linspace(0, 2*np.pi, 200)
        x = 3.2*np.cos(th); y = 1.2*np.sin(th)
        a = np.radians(angle)
        xr = x*np.cos(a) - y*np.sin(a); yr = x*np.sin(a) + y*np.cos(a)
        ax.plot(5+xr, 5.6+yr, color=col, lw=3, alpha=0.9)
    ax.add_patch(Circle((5, 5.6), 0.7, facecolor=RATIS_GOLD,
                        edgecolor="white", linewidth=2, zorder=5))
    ax.text(5, 3.4, "RATIS LABS", ha="center", va="center", fontsize=34,
            fontweight="bold", color="white", family="sans-serif")
    ax.text(5, 2.7, "Souveraineté technologique · Cameroun",
            ha="center", va="center", fontsize=12, color=RATIS_GOLD, style="italic")
    save(fig, "09_logo_ratis_labs.png", facecolor=RATIS_DARK)


if __name__ == "__main__":
    print("Génération des figures de documentation...")
    fig_schema_optique()
    fig_sequences()
    fig_mesures()
    fig_bloch()
    fig_architectures()
    fig_plan_mecanique()
    fig_appareil_monte()
    fig_qpu_scientifique()
    fig_logo()
    print("Toutes les figures sont dans docs/images/")
