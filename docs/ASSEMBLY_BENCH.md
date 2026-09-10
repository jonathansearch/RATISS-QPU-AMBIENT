# 🔧 ASSEMBLY_BENCH — Plan d'assemblage du banc NV (ODMR)

Document exécutable pour assembler le banc de mesure de centres NV à température
ambiante. C'est un microscope confocal à fluorescence couplé à un pilotage
micro-onde. **La précision optique est le défi n°1** — lire entièrement avant de
commencer. Sécurité laser : le 532 nm à 100 mW BRÛLE la rétine. Lunettes de
protection OD4+ à 532 nm OBLIGATOIRES dès que le laser est allumé.

## 🎯 Fonction du banc (ce qu'on construit)

Un **microscope confocal NV** :
1. Un laser vert (532 nm) excite les centres NV du diamant.
2. Les NV réémettent une fluorescence rouge (637–800 nm).
3. Un filtre sépare la fluorescence du laser.
4. Un détecteur (APD) compte les photons rouges.
5. Une antenne micro-onde balaie la fréquence autour de 2.87 GHz.
6. Quand la micro-onde est à la résonance du spin, la fluorescence CHUTE
   (c'est l'ODMR) → on détecte le spin optiquement.

## 🔬 Schéma optique (chemin de la lumière)

```
[Laser 532 nm] → [filtre de nettoyage] → [lame dichroïque 550 nm]
                                              | (réfléchit 532, transmet >600)
                                              v
                                    [Objectif ×50 NA 0.7]
                                              |
                                              v
                                    [Diamant CVD + NV]  ← antenne µ-onde (fil)
                                              |
                        fluorescence rouge 637–800 nm
                                              |
                                    [Objectif] (retour, même chemin)
                                              |
                                    [Lame dichroïque] (transmet le rouge)
                                              |
                                    [Filtre passe-long 650 nm] (bloque 532 résiduel)
                                              |
                                    [Lentille de focalisation] → [APD]
```

La lame dichroïque est la clé : elle envoie le vert vers l'échantillon et laisse
passer le rouge vers le détecteur. Un seul objectif sert à exciter ET collecter
(géométrie "épi-fluorescence" — la plus simple à aligner).

## 📐 Ordre de montage (NE PAS changer l'ordre)

### Étape 1 — La table et la stabilité (AVANT toute optique)
- Poser la plaque anti-vibration. Toute vibration > 1 µm tue les franges de Ramsey.
- Fixer les rails/montures. Travailler dans une pièce sans courant d'air.

### Étape 2 — Le chemin d'excitation (laser → échantillon)
1. Monter le laser sur monture fixe. **Jamais allumé sans lunettes.**
2. Aligner le faisceau à hauteur constante (une "règle de hauteur" : le faisceau
   doit passer à la même hauteur partout — utiliser deux iris).
3. Placer la lame dichroïque à 45°, puis l'objectif.
4. Vérifier que le laser arrive au centre de l'objectif (faisceau collimaté).

### Étape 3 — L'échantillon et le pilotage micro-onde
1. Fixer le diamant CVD sur le substrat avec l'antenne micro-onde (fil de cuivre
   20 µm à ~50 µm de la zone observée).
2. Connecter l'antenne : générateur RF → ampli → switch → antenne.
3. Placer les aimants NdFeB pour le champ statique Zeeman.

### Étape 4 — Le chemin de détection (échantillon → APD)
1. Derrière la lame dichroïque, placer le filtre passe-long 650 nm.
2. Lentille de focalisation → APD.
3. **Aligner sur la fluorescence** : allumer le laser (lunettes !), trouver le
   point fluorescent du diamant, maximiser le signal sur l'APD en ajustant la
   lentille. Le signal est FAIBLE (photons uniques) — travailler dans le noir.

### Étape 5 — L'acquisition et la pulsation
1. Connecter APD → DAQ/compteur → ordinateur.
2. Le contrôleur de pulsation (Pico/Arduino) génère les séquences de pulses
   micro-onde (switch RF) synchronisées avec les fenêtres de comptage APD.

## ✅ Procédure de réception (tests avant de dire "ça marche")

| Étape | Test | Critère d'acceptation |
|---|---|---|
| B1 | Sécurité laser | lunettes OD4+ portées, faisceau confiné, pas de réflexion libre |
| B2 | Faisceau aligné | laser centré dans l'objectif, hauteur constante ±2 mm |
| B3 | Fluorescence détectée | signal APD au-dessus du bruit de fond quand laser ON sur le diamant |
| B4 | Signal/bruit | comptage fluorescence / comptage fond > 5 |
| B5 | Dip ODMR visible | chute de fluorescence de ≥ 1 % à une fréquence ~2.87 GHz |
| B6 | ODMR suit le champ | le dip bouge quand on déplace l'aimant (effet Zeeman) |
| B7 | Oscillations de Rabi | la fluorescence oscille avec la durée du pulse µ-onde |
| B8 | T1 mesuré | décroissance de la population en fonction du délai |
| B9 | Ramsey / T2* | franges de Ramsey visibles, décroissance mesurée |
| B10 | Hahn / T2 | écho visible, T2 > T2* (le découplage rallonge la cohérence) |

> Le test B5 (dip ODMR) est LE moment de vérité : s'il apparaît, on adresse le
> spin NV optiquement. Tout le reste découle de là.

## ⚠️ Pièges d'assemblage (appris des labos)
- **Pas de dip ODMR ?** → vérifier dans l'ordre : fluorescence d'abord (B3),
  puis la fréquence micro-onde (2.87 GHz ± 50 MHz), puis la puissance RF,
  puis l'antenne (distance au diamant).
- **Signal faible ?** → l'alignement de la lentille de collection sur l'APD est
  le coupable n°1. Réaligner sur la fluorescence, pas sur le laser.
- **Franges de Ramsey bruitées ?** → vibration ou champ magnétique instable.
  Refaire la table, stabiliser les aimants.
- **Bruit de fond élevé ?** → lumière parasite. Le banc doit être dans le noir
  (boîte ou rideau). Les APD sont sensibles à la lumière ambiante.

## 🔗 Ce banc s'intègre à la chaîne RATISS
Une fois B5–B10 validés, les mesures réelles (T1, T2, Ω) remplacent les ordres
de grandeur du `DecoherenceModel`. Le banc **calibre le simulateur**. C'est la
boucle mesure↔modèle qui fait la rigueur RATISS.
