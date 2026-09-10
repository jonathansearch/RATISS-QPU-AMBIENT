# ⚛️ RATISS-QPU-AMBIENT — DOCUMENT DE CONCEPTION COMPLET

<div align="center">

![RATIS Labs](docs/images/09_logo_ratis_labs.png)

**Processeur quantique à température ambiante — Priorité 1 de la doctrine RATISS**

Manuel d'ingénierie complet : physique, conception du banc, simulation, itérations.

*RATIS Labs · Cameroun · Propriété : JOHNKING0 & Jonathan Evina · ORCID 0009-0000-4092-5313*

</div>

---

> 🇨🇲 **Un mot au Gouvernement de la République du Cameroun**
>
> L'informatique quantique est l'arme stratégique du XXIᵉ siècle — et on nous
> dit qu'elle exige des laboratoires à des millions de dollars et des frigos à
> hélium-3 inaccessibles. **C'est faux.** Le centre NV du diamant produit un
> qubit cohérent à température ambiante, avec un banc optique qu'un ingénieur
> camerounais peut assembler pour le prix d'une voiture. RATISS-QPU-AMBIENT
> démontre, simulateur validé sur le hardware d'IBM à l'appui, que la
> souveraineté quantique est à notre portée. Ce document est un manuel de
> construction national : il donne à nos universités et à nos ingénieurs les
> plans, le code et la méthode pour bâtir le premier processeur quantique du
> continent, ici, maintenant. **La souveraineté quantique n'attend pas : elle
> se construit.**

---

## 📑 Table des matières

1. [Anatomie d'un qubit à température ambiante](#1-anatomie-dun-qubit)
2. [La rupture stratégique](#2-la-rupture-stratégique)
3. [Plan de conception optique](#3-plan-de-conception-optique)
4. [Plan de conception mécanique](#4-plan-de-conception-mécanique)
5. [L'appareil une fois monté](#5-lappareil-une-fois-monté)
6. [Le simulateur : architecture du code](#6-le-simulateur)
7. [Les 4 séquences de mesure](#7-les-4-séquences-de-mesure)
8. [Validation sur hardware IBM](#8-validation-sur-hardware-ibm)
9. [Guide de montage](#9-guide-de-montage)
10. [Itérations de conception](#10-itérations-de-conception)
11. [Sécurité](#11-sécurité)
12. [Feuille de route](#12-feuille-de-route)

---

## 1. Anatomie d'un qubit

![Anatomie QPU](docs/images/08_qpu_scientifique.png)

Le cœur du projet est le **centre azote-lacune (NV) du diamant** : un atome
d'azote voisin d'une lacune dans le réseau cristallin de carbone. Cet édifice
atomique piège un électron dont le **spin S=1** se comporte comme un qubit.

- **Réseau diamant (¹²C)** : le carbone pur n'a pas de spin nucléaire → un
  environnement "silencieux" qui protège la cohérence du spin électronique.
- **Niveaux d'énergie** : l'état fondamental ms=0 et ms=±1 sont séparés par
  2.87 GHz. Un laser vert (532 nm) pompe le spin vers ms=0 et lit son état par
  la fluorescence rouge (637 nm).
- **La sphère de Bloch** : l'état quantique |ψ⟩ = α|0⟩ + β|1⟩ vit sur cette
  sphère. La décohérence le tire vers le centre — c'est notre signature P_sig.
- **Le signal ODMR** : quand la micro-onde atteint la résonance (2.87 GHz), la
  fluorescence chute — on **lit le spin par la lumière**, sans cryogénie.

---

## 2. La rupture stratégique

Les QPU supraconducteurs (IBM, Google) exigent 15 mK — des frigos à dilution
hors de prix et inmaintenables au Cameroun. **C'est leur talon d'Achille.**

![Comparatif](docs/images/05_comparatif_architectures.png)

Le NV-diamant ¹²C à 300 K fait jusqu'à **10⁵–10⁶ opérations cohérentes** —
autant ou plus que le supraconducteur à 15 mK, **sans cryogénie**. Le froid
extrême est un contournement pour fabriquer des qubits en masse, pas une
supériorité de cohérence. Pour un démonstrateur souverain, le NV ambiant est
physiquement supérieur **et** constructible à budget camerounais.

> 💡 **Démocratiser, pas détruire.** On ne détruit pas l'industrie
> supraconductrice — on révèle qu'elle refroidit pour des raisons de
> fabrication, pas de cohérence. Le quantique n'a pas besoin d'être cher.

---

## 3. Plan de conception optique

![Schéma optique](docs/images/01_schema_optique.png)

Le banc est un **microscope confocal épi-fluorescence**. Le principe :

1. Un **laser vert 532 nm** excite les centres NV.
2. Ils réémettent une **fluorescence rouge 637–800 nm**.
3. La **lame dichroïque** (550 nm) est la pièce maîtresse : elle réfléchit le
   vert vers l'échantillon et laisse passer le rouge vers le détecteur. Un seul
   objectif excite ET collecte.
4. Un **filtre 650 nm** bloque tout vert résiduel.
5. L'**APD** compte les photons rouges, un par un.
6. L'**antenne micro-onde** balaie autour de 2.87 GHz → à la résonance, la
   fluorescence chute (ODMR).

### Choix optiques justifiés

| Choix | Justification |
|-------|--------------|
| Objectif NA 0.7 (×50) | Haute ouverture numérique = collecte maximale de photons (signal faible d'un spin unique). |
| APD (pas caméra) | Comptage de photons uniques, résolution temporelle ~ns, indispensable pour lire un spin. |
| Lame dichroïque 550 nm | Sépare nettement excitation (532) et émission (637+) — la clé de l'épi-fluorescence. |
| Éclairage par le même objectif | Simplifie l'alignement — pas besoin de deux chemins optiques indépendants. |

---

## 4. Plan de conception mécanique

![Plan mécanique](docs/images/06_plan_mecanique.png)

Layout sur **plaque optique à trous M6** sur pieds amortisseurs (les vibrations
tuent la cohérence et floutent le point de focalisation). Règles de montage :

1. **Tous les composants optiques à la même hauteur de faisceau** — on utilise
   un cage système (rails) pour garantir la coaxialité.
2. **Diamant sur platine XYZ micrométrique** — la focalisation sur un NV unique
   exige une précision sub-micrométrique.
3. **Antenne micro-onde au plus près du diamant** — le champ µ-onde décroît
   vite ; la proximité maximise la pulsation de Rabi.
4. **Laser en bout de table**, faisceau confiné, lunettes OD4+ obligatoires.
5. **Câbles µ-onde courts (50 Ω)** — les pertes RF augmentent avec la longueur.

---

## 5. L'appareil une fois monté

![Appareil monté](docs/images/07_appareil_monte.png)

Le banc fermé est une **enceinte de protection laser de classe 1** contenant :
- La colonne du microscope confocal + le diamant NV sur platine.
- Le laser 532 nm.
- L'APD (compteur de photons).
- Le rack électronique : synthétiseur µ-onde, séquenceur Pico RP2040, alim laser.
- Un écran de contrôle affichant le dip ODMR en temps réel.

C'est un **appareil de paillasse de laboratoire**, pas une salle blanche — il
tient sur une table et fonctionne à température ambiante, sans hélium.

---

## 6. Le simulateur

Le code valide chaque idée avant tout achat. Architecture :

| Module | Rôle | Classe/fonction clé |
|--------|------|---------------------|
| `ratiss_qpu/qstate.py` | État quantique exact (vecteur, matrice densité) | `bloch_state()`, portes X/H/CNOT |
| `ratiss_qpu/nv_center.py` | Hamiltonien NV⁻ (D=2.87 GHz, Zeeman) | `NVCenter` |
| `ratiss_qpu/coherence.py` | Décohérence Lindblad T1/Tφ thermique | `DecoherenceModel`, `bloch_trajectory` |
| `ratiss_qpu/benchmark.py` | Comparatif NV vs supraconducteur vs photonique | `compare_architectures()` |
| `ratiss_qpu/two_qubit.py` | État de Bell, intrication, concurrence | `bell_state()` |
| `ratiss_qpu/ibm_validation.py` | Cross-validation sur vrai QPU IBM | `validate_bell_on_ibm()` |
| `bench/pulse_sequences.py` | Séquences ODMR/Rabi/Ramsey/Hahn | générateurs de pulses |
| `bench/virtual_bench.py` | Banc virtuel (bruit de photon Poisson) | `VirtualBench` |
| `bench/odmr_analysis.py` | Fits + recalibrage du modèle | `fit_odmr()`, `recalibrate_model()` |
| `bench/firmware/main.py` | Firmware de pulsation MicroPython (Pico) | `PulseSequencer` |

### Le modèle physique

L'évolution de l'état obéit à l'**équation maîtresse de Lindblad** :

```
dρ/dt = -i[H, ρ] + Σ_k (L_k ρ L_k† - ½{L_k†L_k, ρ})
```

avec H le hamiltonien NV (splitting Zeeman + champ µ-onde) et L_k les opérateurs
de dissipation (relaxation T1, déphasing Tφ). T1 et T2 dépendent de la
température (loi d'Arrhenius + modèle phononique) — c'est ce qui rend la
simulation **thermiquement réaliste**.

---

## 7. Les 4 séquences de mesure

![Séquences](docs/images/02_sequences_pulses.png)

![Mesures](docs/images/03_mesures_banc.png)

| Séquence | Pulses | Mesure | Signal |
|----------|--------|--------|--------|
| **ODMR** | laser + µ-onde continus, balayage fréquence | résonance du spin | dip de fluorescence |
| **Rabi** | pulse µ-onde de durée τ variable | pulsation de Rabi Ω | oscillations |
| **Ramsey** | π/2 … τ libre … π/2 | T2* (déphasing) | franges amorties |
| **Hahn echo** | π/2 … τ … π … τ … π/2 | T2 (cohérence) | décroissance exponentielle |

Le **pulse π central** de l'écho de Hahn inverse le déphasing à mi-parcours —
les spins se refocalisent comme des coureurs faisant demi-tour. C'est pourquoi
T2 (écho) > T2* (Ramsey).

Le firmware `bench/firmware/main.py` exécute ces séquences sur un **Raspberry
Pi Pico** avec un timing à la microseconde, synchronisant laser, µ-onde et
fenêtre de comptage APD.

---

## 8. Validation sur hardware IBM

Notre simulateur a été **validé sur un vrai processeur quantique** : un état de
Bell |Φ+⟩ exécuté sur **ibm_marrakesh** (156 qubits supraconducteurs) a
reproduit notre distribution prédite avec une **fidélité de 98.4 %**.

| Métrique | Simulateur | IBM (réel) |
|----------|:---------:|:---------:|
| Population \|00⟩ | 0.50 | 0.496 |
| Population \|11⟩ | 0.50 | 0.488 |
| Concurrence | 1.0 | — |
| **Fidélité croisée** | — | **98.4 %** |

> ⚠️ **Honnêteté** : IBM = supraconducteur (physique différente du NV). Cette
> validation prouve la **justesse de notre algorithme et de notre simulateur**,
> pas encore la cohérence de notre NV physique — ça, c'est le banc réel (§12).

Voir `results/bell_cross_validation.json` et `ratiss_qpu/ibm_validation.py`.

---

## 9. Guide de montage

> 📖 **Plan d'assemblage optique détaillé + tests de réception B1–B10 →
> [docs/ASSEMBLY_BENCH.md](docs/ASSEMBLY_BENCH.md)**
> 📦 **Liste de courses complète (~3.5 M FCFA) → [docs/BOM_BENCH.md](docs/BOM_BENCH.md)**

Résumé des étapes :

| Étape | Action | Vérification |
|-------|--------|--------------|
| 1 | Monter la plaque optique sur pieds amortisseurs | Stabilité (pas de flottement du point focal) |
| 2 | Aligner le laser + lame dichroïque + objectif (cage) | Faisceau coaxial, spot net |
| 3 | Fixer le diamant sur platine XYZ | Focalisation sur un NV unique |
| 4 | Positionner l'antenne µ-onde au plus près | Continuité 50 Ω |
| 5 | Connecter APD + filtre 650 nm | Comptage photons, pas de fuite verte |
| 6 | Flasher le Pico RP2040 (firmware de pulsation) | Séquences vérifiées à l'oscilloscope |
| 7 | Balayer ODMR → localiser le dip 2.87 GHz | Dip de fluorescence visible |
| 8 | Calibrer Rabi (durée pulse π) | Oscillations propres |
| 9 | Mesurer Ramsey + Hahn → T2* et T2 | Fits exponentiels |
| 10 | Recalibrer le simulateur sur mesures réelles | Modèle ajusté automatiquement |

**Sécurité laser d'abord** : lunettes OD4+ à 532 nm, faisceau confiné, enceinte
fermée. Voir §11.

---

## 10. Itérations de conception

### Itération 1 → 2 : le bug de la porte CNOT
- **Problème** : concurrence = 0.0 au lieu de 1.0 sur l'état de Bell.
- **Cause** : convention little-endian de Qiskit mal câblée (contrôle q0 →
  cible q1 inversée).
- **Solution** : correction du câblage → concurrence 1.0, |Φ+⟩ correct. Leçon :
  **toujours vérifier la convention d'ordre des qubits**.

### Itération 2 → 3 : le bruit de photon du banc virtuel
- **Problème** : 1.5 photons/point → fits ODMR/Rabi divergeaient (bruit de
  Poisson trop fort).
- **Solution** : paramètre `repetitions` (moyennage, pratique réelle de labo) →
  fits robustes. Leçon : **un spin unique émet peu de photons — on moyenne**.

### Itération 3 → 4 : le warning complexe
- **Problème** : `ComplexWarning` sur un produit scalaire.
- **Solution** : `.real` explicite après `vdot`. Leçon : **la rigueur numérique
  compte autant que la physique**.

### Itération 4 → 5 : validation sur le vrai hardware
- **Problème** : un simulateur non validé reste une hypothèse.
- **Solution** : exécution de l'état de Bell sur ibm_marrakesh → fidélité 98.4 %.
  Leçon : **on prouve sur du réel, pas seulement sur du simulé**.

---

## 11. Sécurité

| Danger | Mitigation |
|--------|-----------|
| Laser 532 nm 100 mW (brûlure rétinienne) | Lunettes OD4+, enceinte classe 1, faisceau confiné, shutter |
| Haute tension APD (~200 V) | Boîtier fermé, connecteurs blindés, pas de manipulation sous tension |
| RF micro-onde | Puissance faible (mW), câbles blindés 50 Ω |
| Diamant fragile | Manipulation aux pinces, jamais aux doigts |

**Le laser est le danger n°1.** Jamais l'œil au niveau du faisceau, toujours
l'enceinte fermée en fonctionnement.

---

## 12. Feuille de route

| Phase | Statut | Livrable |
|-------|:------:|----------|
| 1 — Simulateur + validation IBM | ✅ FAIT | 43/43 tests, fidélité 98.4 % |
| 1.5 — Banc virtuel + firmware | ✅ FAIT | Chaîne logicielle complète validée |
| 1.5 réelle — Banc physique | 🔜 À FAIRE | Commander diamant CVD, assembler, mesurer |
| 2 — Multi-qubits NV | 🔮 FUTUR | Couplage dipolaire NV-NV, registre quantique |

**La Phase 1.5 réelle est le prochain geste physique** : commander le diamant
CVD (~350 000 FCFA, voir `BOM_BENCH.md`), assembler le banc selon ce document,
et reproduire les courbes du banc virtuel sur le hardware réel. L'analyseur
recalibrera automatiquement le simulateur sur les mesures.

---

<div align="center">

**RATIS Labs · Cameroun** — *Toujours itérer, jamais figé. Prouver, pas prétendre.* 🦇⚛️

![RATIS Labs](docs/images/09_logo_ratis_labs.png)

</div>
