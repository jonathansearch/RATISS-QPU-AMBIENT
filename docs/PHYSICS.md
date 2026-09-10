# 📐 PHYSICS — Références et hamiltoniens RATISS-QPU-AMBIENT

Chaque affirmation physique du dépôt est sourcée ici. Règle : pas de chiffre
sans référence peer-reviewed. C'est ce qui sépare un simulateur rigoureux d'un
papier qui survend.

## 1. Hamiltonien du centre NV− (état fondamental, S=1)

Le centre NV− a un état fondamental triplet de spin S=1. Hamiltonien complet :

    H/h = D·Sz² + γ_e·B·S + S·A·I + Q·Iz² + γ_n·B·I

avec :
- **D = 2.87 GHz** : splitting à champ nul (zéro-field splitting) entre ms=0 et ms=±1.
- **γ_e = 28.0 GHz/T** : rapport gyromagnétique électronique.
- **A** : tenseur hyperfin (couplage au spin nucléaire ¹⁴N ou ¹⁵N).
- **Q = −4.95 MHz** : quadrupole nucléaire (¹⁴N).
- **γ_n** : gyromagnétique nucléaire.

Pour le qubit, on se restreint au sous-espace {ms=0, ms=−1}, couplé par micro-onde.
Sous RWA à résonance : H_rot = (Ω/2)·Sx → rotations de Rabi.

**Références :**
- Doherty, M. W. et al., "The nitrogen-vacancy colour centre in diamond",
  *Physics Reports* 528:1–45 (2013). [Revue de référence complète]
- Rondin, L. et al., "Magnetometry with nitrogen-vacancy defects in diamond",
  *Rep. Prog. Phys.* 77:056503 (2014).

## 2. Temps de cohérence (T1, T2) à température ambiante

| Paramètre | Diamant naturel | Diamant ¹²C purifié | Référence |
|---|:---:|:---:|:---:|
| T1 @ 300 K | ~1–10 ms | ~1–10 ms | Jarmola et al., PRL 108:197601 (2012) |
| T2 @ 300 K | ~0.5–1 ms | ~0.1–1 s (sous DD) | Balasubramanian et al., Nat. Mater. 8:383 (2009) |
| T2* @ 300 K | ~µs | ~100 µs | Bar-Gill et al., Nat. Commun. 4:1743 (2013) |

DD = découplage dynamique (séquences de pulses qui rallongent T2 effectif).
Le record absolu approche la seconde en ¹²C ultra-pur.

**Physique :** T1 est limité par la relaxation spin-réseau (processus Raman à
2 phonons). T2 est limité par le bain de spins nucléaires ¹³C (1.1 % naturel) —
d'où le gain spectaculaire de la purification isotopique ¹²C.

## 3. Décohérence — équation de Lindblad

La dynamique markovienne de la matrice densité ρ :

    dρ/dt = −i[H,ρ] + γ1·D[σ₋]ρ + γφ·D[σz]ρ

où D[L]ρ = LρL† − ½{L†L,ρ} est le dissipateur de Lindblad, et :

    1/T2 = 1/(2T1) + 1/Tφ

**Référence :** Lindblad, G., "On the generators of quantum dynamical semigroups",
*Commun. Math. Phys.* 48:119 (1976). Gorini-Kossakowski-Sudarshan (1976).

## 4. Dépendance en température (transdisciplinarité thermo × quantique)

- **T1(T)** : processus Raman 2-phonons. Faible dépendance en dessous de ~100 K,
  puis chute thermiquement activée. Modèle local ≈ (T/300)^−2 autour de 300 K
  (ordre de grandeur, à recalibrer sur banc). Jarmola et al. (2012) Fig. 3.
- **Tφ(T)** : dominé par le bain ¹³C (quasi-indépendant de T) — c'est pourquoi
  la purification isotopique compte plus que le refroidissement pour le NV.
  C'est LE fait physique qui rend l'ambiant viable.

## 5. Photonique LiNbO₃ (TFLN) — pour comparaison

- Pas de décohérence thermique du photon ; la limite est la perte optique.
- Modulateurs électro-optiques ultra-rapides : Hu et al., "Integrated
  electro-optics on thin-film lithium niobate", *Nat. Rev. Phys.* 7:237 (2025).
- Architecture GKP/fusion à température ambiante (sauf détecteurs SNSPD ~1 K) :
  Bourassa et al., "Scaling and networking a modular photonic quantum
  computer", *Nature* (2024).

## 6. Supraconducteur (référence de comparaison)

- T2 ~ 100–500 µs à ~15 mK. Nécessite dilution réfrigérateur + hélium-3.
- Ratio T2/t_porte ≈ 10⁴ — **inférieur** au NV ¹²C à 300 K (jusqu'à 10⁶).
- C'est le fait central : le froid extrême ne donne PAS une meilleure cohérence
  relative que le NV ambiant. Il donne juste une scalabilité de fabrication.

## 7. Validation croisée IBM Quantum

Notre simulateur est validé sur hardware réel : état de Bell |Φ+⟩ exécuté sur
ibm_marrakesh (156 qubits supraconducteurs). Résultat : fidélité 98.4 % avec
notre simulateur idéal. Voir `results/bell_cross_validation.json`.

**Ce que ça prouve :** notre chaîne logicielle et notre algèbre quantique sont
correctes face à du vrai hardware.
**Ce que ça ne prouve pas :** la cohérence de notre NV physique (à mesurer sur
banc, phase suivante). IBM = supraconducteur, physique différente.
