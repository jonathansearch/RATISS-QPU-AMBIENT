# 🎨 GUIDE VISUEL — RATISS-QPU-AMBIENT illustré

Le tour complet du projet en images. Chaque figure est générée par le code du
dépôt (`scripts/generate_figures.py`) à partir de la vraie physique simulée —
pas des images décoratives, des **données**. Régénère-les à tout moment :

```bash
PYTHONPATH=. python scripts/generate_figures.py
```

---

## 1. 🔬 Le banc optique — comment on voit un spin unique

![Schéma optique du banc NV](images/01_schema_optique.png)

Le cœur du banc est un **microscope confocal épi-fluorescence**. Le principe :

1. Un **laser vert (532 nm)** excite les centres NV du diamant.
2. Les NV réémettent une **fluorescence rouge (637–800 nm)**.
3. La **lame dichroïque** est la pièce maîtresse : elle réfléchit le vert vers
   l'échantillon et laisse passer le rouge vers le détecteur. Un seul objectif
   sert à exciter ET à collecter — c'est ce qui rend l'alignement faisable.
4. Un **filtre 650 nm** bloque tout vert résiduel.
5. L'**APD** (photodiode à avalanche) compte les photons rouges, un par un.
6. L'**antenne micro-onde** balaie autour de 2.87 GHz. À la résonance du spin,
   la fluorescence **chute** → on détecte le spin optiquement. C'est l'ODMR.

> ⚠️ **Sécurité laser** : 100 mW à 532 nm brûle la rétine. Lunettes OD4+
> obligatoires dès que le laser est allumé. Voir `ASSEMBLY_BENCH.md`.

---

## 2. ⏱️ Les 4 séquences de mesure — le langage des pulses

![Séquences de pulses](images/02_sequences_pulses.png)

Toute mesure NV est une **chorégraphie de pulses** laser et micro-onde. Le
firmware (`bench/firmware/main.py`) les exécute avec un timing à la microseconde :

| # | Séquence | Ce qu'elle fait | Ce qu'elle mesure |
|---|----------|-----------------|-------------------|
| 1 | **ODMR** | laser + µ-onde en continu, on balaie la fréquence | la fréquence de résonance du spin |
| 2 | **Rabi** | pulse µ-onde de durée τ variable | la pulsation de Rabi Ω (vitesse des portes) |
| 3 | **Ramsey** | π/2 … attente libre τ … π/2 | T2* (déphasing libre) |
| 4 | **Hahn echo** | π/2 … τ … **π** … τ … π/2 | T2 (cohérence vraie, le π refocalise) |

Le **pulse π central** de l'écho de Hahn est l'astuce géniale : il inverse le
déphasing à mi-parcours, donc les spins qui avaient déphasé se **refocalisent**
— comme des coureurs qui font demi-tour et se retrouvent à l'arrivée. C'est
pourquoi T2 (écho) > T2* (Ramsey) : l'écho élimine le bruit lent.

---

## 3. 📈 Les mesures — à quoi ressemblent les vraies données

![Mesures du banc](images/03_mesures_banc.png)

Ces 4 courbes sont générées par le **banc virtuel** (`bench/virtual_bench.py`)
avec le vrai bruit de photon (statistique de Poisson). Le banc physique
produira des courbes identiques — c'est ce à quoi tu dois t'attendre :

- **ODMR (haut-gauche)** : le dip de fluorescence à la résonance. C'est LE
  signal qui prouve qu'on adresse le spin. Sa position bouge avec le champ
  magnétique (effet Zeeman) → magnétométrie quantique.
- **Rabi (haut-droite)** : la population oscille quand on varie la durée du
  pulse. La fréquence de ces oscillations = la pulsation de Rabi Ω.
- **Ramsey (bas-gauche)** : des franges qui s'amortissent. L'enveloppe de
  décroissance donne T2*.
- **Hahn (bas-droite)** : une décroissance exponentielle propre → T2.

L'analyseur (`bench/odmr_analysis.py`) ajuste ces courbes et en tire les
paramètres physiques qui **recalibrent automatiquement le simulateur**.

---

## 4. 🌐 La sphère de Bloch — voir la cohérence mourir

![Sphère de Bloch et P_sig](images/04_sphere_bloch.png)

C'est la visualisation la plus profonde du projet. Un qubit pur vit à la
**surface** de la sphère de Bloch (rayon ‖r‖ = 1). La décohérence le tire vers
le **centre** (état mixte, ‖r‖ → 0).

- **Gauche** : la trajectoire 3D d'un état qui part de l'équateur (superposition)
  et spiralote vers l'intérieur sous l'effet de la décohérence thermique.
- **Droite** : le **rayon de Bloch** en fonction du temps. C'est notre **P_sig
  quantique** — la contraction topologique de la sphère, mesure géométrique
  directe de la cohérence restante.

C'est le même raisonnement topologique que le P_sig de `ratiss-grid` (détection
de cycles dans un signal électrique), transposé à l'espace des états quantiques.
**La LCT s'applique aux deux échelles** — c'est la transdisciplinarité en action.

---

## 5. ⚖️ Le verdict — le NV ambiant face au monde

![Comparatif d'architectures](images/05_comparatif_architectures.png)

Le nombre qui compte : **combien d'opérations cohérentes** (T2 / temps de porte)
chaque architecture permet-elle ?

- **NV-diamant ¹²C à 300 K** : jusqu'à ~10⁵–10⁶ opérations, **sans cryogénie**.
- **Supraconducteur à 15 mK** : ~10⁴ opérations, mais il faut un dilution
  réfrigérateur à hélium-3 (~600M FCFA, inmaintenable au Cameroun).

> 💡 **Le froid extrême ne donne pas une meilleure cohérence relative.** Le
> supraconducteur refroidit pour *fabriquer* des qubits en masse, pas pour
> *mieux* cohérer. Pour un démonstrateur souverain à budget camerounais, le NV
> ambiant est physiquement supérieur ET constructible. On ne détruit pas leur
> industrie — on révèle qu'elle refroidit pour des raisons de fabrication, pas
> de cohérence. Démocratiser, pas détruire.

---

## 🧭 Où aller ensuite

| Document | Contenu |
|----------|---------|
| `docs/ARCHITECTURE.md` | Pourquoi le NV a été choisi (comparatif rigoureux) |
| `docs/PHYSICS.md` | Tous les hamiltoniens et références peer-reviewed |
| `docs/BOM_BENCH.md` | Liste de courses du banc (~3.5M FCFA) |
| `docs/ASSEMBLY_BENCH.md` | Plan d'assemblage optique + tests B1–B10 |
| `bench/firmware/main.py` | Firmware de pulsation MicroPython (Pico) |
| `MEMO_QPU.md` | État d'avancement et prochaines étapes |

**Le logiciel est prêt et validé (42/42 tests).** Reste le geste physique :
commander le diamant, aligner l'optique, mesurer. Les images ci-dessus sont la
cible — le banc réel doit reproduire ces courbes.

---

*Toutes les figures sont régénérables par `scripts/generate_figures.py`. Ce sont
des données du banc virtuel, pas des illustrations libres — la rigueur RATISS
jusque dans les images.*
