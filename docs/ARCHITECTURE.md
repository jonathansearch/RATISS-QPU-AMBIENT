# 🏗️ ARCHITECTURE — Comparatif physique rigoureux des QPU à température ambiante

Analyse transdisciplinaire (physique quantique, science des matériaux,
thermodynamique, optique, micro-ondes). Chaque chiffre est sourcé. Objectif :
choisir l'architecture ambiante la plus **constructible et cohérente** pour le
Cameroun. Voir `docs/PHYSICS.md` pour les hamiltoniens complets.

## 🌡️ Le problème fondamental : la décohérence thermique

Un qubit perd sa cohérence par interaction avec l'environnement thermique
(phonons, fluctuations de champ). Le taux suit une loi de type Arrhenius /
phononique : plus il fait chaud, plus ça décohère vite. C'est POURQUOI l'industrie
refroidit. Mais c'est une fuite en avant coûteuse — la bonne question est :

> **Quelle plateforme physique a une cohérence LONGUE *à cause de* sa structure
> de matériau, indépendamment du refroidissement ?**

Réponse : celles dont l'état quantique est **protégé par le matériau hôte**.

## ⚛️ Architecture A — Centre NV dans le diamant (NOTRE CHOIX)

**Physique.** Le centre NV− est un défaut ponctuel du diamant (azote + lacune).
Son état fondamental est un triplet de spin S=1 (ms = 0, ±1). Le qubit est encodé
dans {|0⟩, |−1⟩} ou {|0⟩, |+1⟩}.

**Pourquoi la cohérence est longue à 300 K :**
- Le diamant a une **bande interdite de 5.5 eV** → très peu de porteurs thermiques
  libres pour coupler au spin.
- Réseau covalent C–C **ultra-rigide** → phonons de haute énergie, faible densité
  d'états aux fréquences de transition du spin.
- Diamant isotopiquement purifié **¹²C (spin nucléaire 0)** → supprime le bain
  de spins nucléaires de ¹³C, principale source de déphasing.

**Chiffres sourcés (docs/PHYSICS.md) :**
- T2 à 300 K : **~1 ms** (diamant naturel) jusqu'à **~1 s** (¹²C > 99.99 %) sous
  découplage dynamique. Réf : Bar-Gill et al., Nat. Commun. 2013 ; Balasubramanian
  et al., Nat. Mater. 2009.
- T1 à 300 K : **~1–10 ms** (relaxation spin-réseau). Jarmola et al., PRL 2012.
- Temps de porte micro-onde : **~1 µs** (pulsations de Rabi ~MHz).
- Lecture : ODMR (Optically Detected Magnetic Resonance) — photoluminescence
  dépendante du spin, lisible à température ambiante avec un simple laser 532 nm.

**Figure de mérite : T2/t_porte ≈ 10³ à 10⁶ opérations cohérentes.** Meilleure
valeur ambiante connue.

**Défaut honnête :** couplage entre qubits NV distants difficile (interaction
dipolaire ~nm, ou médiée par photon ~lente). Scalabilité = défi réel. Pour un
**démonstrateur à quelques qubits + capteur quantique**, c'est parfait.

## 💡 Architecture B — Photonique LiNbO₃ (TFLN)

**Physique.** Le qubit est encodé dans l'état d'un photon (polarisation, chemin,
ou mode temporel). Les photons n'interagissent quasiment pas avec le bain
thermique → **pas de décohérence thermique au sens propre**. La "décohérence"
devient la **perte de photons** (absorption, diffusion) et la **déphasing de
phase** dans les guides.

**Avantages :**
- Opérations à température ambiante, très rapides (~ps), faibles pertes dans
  TFLN (modulateurs électro-optiques ultra-rapides, Hu et al., Nat. Rev. Phys. 2025).
- C'est l'architecture de Quandela, PsiQuantum, ORCA, Q.ANT.

**Le talon caché :** l'architecture complète (GKP / fusion-based, Bourassa et al.,
Nature 2024) exige des **détecteurs PNR** à résolution de nombre de photons, qui
sont des **SNSPD à ~1 K**. → Cryogénie, mais **localisée au détecteur seul**, pas
à tout le QPU. Pour certaines classes (boson sampling), des **APD de seuil** à
température ambiante suffisent.

**Verdict :** excellente mais BOM optique très exigeante en précision (stabilisation
de phase interférométrique). Deuxième priorité après NV.

## ❄️ Architecture C — Supraconducteur (référence, REJETÉE pour nous)

T2 ~100–500 µs à **15 mK**. Nécessite dilution réfrigérateur (~1 M€), hélium-3,
infrastructure lourde. **Inconstructible et inmaintenable au Cameroun.** On la cite
uniquement comme référence de comparaison : son ratio T2/t_porte (~10⁴) est
**inférieur** au NV à température ambiante. Le froid n'est pas une supériorité
physique, c'est un contournement coûteux.

## 🧲 Architecture D — Ions piégés (mention)

Excellente cohérence (secondes) et fidélité de portes à 2 qubits (99.9 %+), à
température ambiante **MAIS** exige un **ultra-vide** (10⁻¹¹ mbar) et un laser de
refroidissement de haute précision. UHV = pompe ionique + maintenance lourde.
Possible mais plus délicat que NV pour un premier démonstrateur.

## 🏆 DÉCISION D'ARCHITECTURE

| Critère | NV-diamant | Photonique TFLN | Supraconducteur | Ions |
|---|:---:|:---:|:---:|:---:|
| Température | 300 K ✅ | 300 K (sauf détecteur) | 15 mK ❌ | 300 K + UHV |
| Ops cohérentes | 10³–10⁶ ✅ | limité par pertes | ~10⁴ | élevé |
| Constructible local | ✅ banc optique | ⚠️ précision | ❌ | ⚠️ UHV |
| Maintenable local | ✅ | ⚠️ | ❌ | ⚠️ |
| BOM (ordre) | ~3–6 M FCFA | ~8–15 M FCFA | ~600 M FCFA+ | ~30 M FCFA+ |

> **Choix Priorité 1 : NV-diamant**, banc ODMR + simulateur de cohérence.
> C'est la seule architecture à la fois physiquement supérieure en ambiant,
> constructible sur un budget camerounais, et maintenable localement.

## 🔗 Le pont avec la LCT (signature RATISS)

La perte de cohérence est un **processus géométrique** : dans l'espace de Bloch,
l'état pur (surface de la sphère) s'effondre vers le centre (état mixte) sous
l'effet de la décohérence. On détecte cette **contraction topologique** par un
P_sig adapté — même esprit que le watchdog électrique de ratiss-grid. Voir
`ratiss_qpu/coherence.py` et `docs/PHYSICS.md`.
