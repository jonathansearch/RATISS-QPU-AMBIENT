# 🔬 BOM_BENCH — Banc de mesure NV constructible (ODMR)

Bill of Materials pour un banc de magnétométrie/manipulation de centres NV à
température ambiante — la phase physique de Priorité 1. Tout est sourçable
Chine/Dubaï/local. C'est un **banc de recherche** : il prouve la cohérence NV
réelle (T1, T2, ODMR, oscillations de Rabi) avant tout QPU multi-qubits.

## 🎯 Ce que le banc mesure (les preuves à produire)
1. **Spectre ODMR** : dip de photoluminescence à la résonance micro-onde →
   prouve qu'on adresse le spin NV.
2. **Oscillations de Rabi** : balayage de la durée de pulse → mesure Ω et t_porte.
3. **T1** : relaxation (séquence init–wait–read).
4. **T2\*** : franges de Ramsey ; **T2** : écho de Hahn.
Ces 4 mesures recalibrent `DecoherenceModel` sur données RÉELLES camerounaises.

## 💰 Bill of Materials

| # | Composant | Référence type | Qté | PU (FCFA) | Total (FCFA) | Source |
|---|-----------|----------------|:---:|:---:|:---:|--------|
| 1 | Diamant CVD avec centres NV | diamant CVD, [N] ~1–10 ppm, ou ¹²C enrichi | 1 | 350 000 | 350 000 | Chine (Element Six / Alibaba) |
| 2 | Laser vert 532 nm, 100 mW | DPSS 532 nm, mode TEM00 | 1 | 180 000 | 180 000 | Chine |
| 3 | Objectif de microscope ×50 NA 0.7 | Olympus/Mitutoyo ou clone | 1 | 220 000 | 220 000 | Dubaï/occasion |
| 4 | Filtre passe-long 650 nm + filtre notch 532 | Thorlabs/Edmund ou clone | 1 jeu | 90 000 | 90 000 | Chine/Dubaï |
| 5 | Photodiode à avalanche (APD) ou caméra | Excelitas SPCM ou APD module | 1 | 400 000 | 400 000 | Dubaï |
| 6 | Générateur micro-onde 2–4 GHz | synthétiseur RF (ou Adalm-Pluto SDR) | 1 | 300 000 | 300 000 | Chine (SDR) |
| 7 | Amplificateur micro-onde + commutateur RF | amp 2–4 GHz, switch | 1 | 120 000 | 120 000 | Chine |
| 8 | Antenne micro-onde (fil/coil sur substrat) | fil de cuivre 20 µm sur PCB | 1 | 30 000 | 30 000 | local |
| 9 | Électro-aimant / aimants permanents NdFeB | paire d'aimants N52 + supports | 1 | 45 000 | 45 000 | local/Chine |
| 10 | Contrôleur de pulsation (FPGA ou Arduino Due/Raspberry Pi Pico) | génération de séquences µs | 1 | 60 000 | 60 000 | local/Dubaï |
| 11 | Table optique anti-vibration + montures | plaque alvéolaire, montures kinematic | 1 | 380 000 | 380 000 | Dubaï/local |
| 12 | Électronique d'acquisition (compteur/DAQ) | carte DAQ ou Red Pitaya | 1 | 250 000 | 250 000 | Dubaï |
| 13 | Optique divers (miroirs, lames, lentilles, fibre) | kit optomécanique | 1 | 150 000 | 150 000 | Chine/Dubaï |
| 14 | Blindage, coffret, câblage, connectique | sur mesure | 1 | 90 000 | 90 000 | local |

## 💰 TOTAL

| Poste | Montant |
|---|:---:|
| Sous-total composants | ≈ 2 665 000 FCFA |
| Main d'œuvre assemblage + alignement optique | ~400 000 |
| Imprévu (15 % — l'optique pardonne peu) | ~400 000 |
| **TOTAL BANC NV** | **≈ 3 500 000 FCFA** |

> C'est le prix d'un banc de recherche NV complet, à température ambiante,
> constructible au Cameroun. À comparer aux ~600 M FCFA+ d'un dilution
> réfrigérateur pour supraconducteur (inmaintenable localement).

## ⚠️ Points critiques d'assemblage
- **Alignement optique** : le point le plus délicat. Laser 532 nm → objectif →
  diamant → collecte fluorescence > 650 nm sur APD. Prévoir du temps d'alignement.
- **Stabilité vibratoire** : la table anti-vibration n'est PAS optionnelle —
  les franges de Ramsey exigent une stabilité sub-micrométrique.
- **Champ magnétique stable** : les aimants NdFeB + contrôle fin pour balayer
  la résonance Zeeman (effet décrit dans nv_center.py).
- **Tout se calibre** : chaque mesure (ODMR, Rabi, T1, T2) recalibre le
  simulateur. C'est le lien mesure↔modèle de la charte RATISS.

## 🔗 Lien avec le simulateur
Les T1/T2 mesurés sur ce banc remplacent les ordres de grandeur de
`DecoherenceModel`. Le banc transforme le simulateur de "documenté" en
"calibré sur le réel camerounais". C'est l'étape qui fait passer la Priorité 1
de la preuve logicielle à la preuve matérielle.
