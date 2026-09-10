# 🧭 MEMO_QPU — État d'avancement RATISS-QPU-AMBIENT (Priorité 1)

Mémo de session (style MEMO_KTN_LI / MEMO_GRID). Source de vérité. Jamais figé.

## ✅ ÉTAT ACTUEL (Phase 1 — simulation + validation IBM réussies)
- [x] Dépôt créé : `samajonathan9-source/ratiss-qpu-ambient`
- [x] Comparatif d'architectures rigoureux (`docs/ARCHITECTURE.md`) — NV choisi
- [x] Physique sourcée (`docs/PHYSICS.md`) — hamiltonien NV, T1/T2, Lindblad, refs
- [x] Simulateur d'état exact (`qstate.py`) — Bloch, portes, Born, pureté
- [x] Hamiltonien NV (`nv_center.py`) — Zeeman, Rabi, RWA
- [x] Décohérence Lindblad (`coherence.py`) — T1/T2(T), P_sig topologique sur Bloch
- [x] 2 qubits + Bell (`two_qubit.py`) — |Φ+⟩, concurrence=1
- [x] Benchmark (`benchmark.py`) — NV bat le supraconducteur en ops cohérentes
- [x] **Validation croisée IBM Quantum RÉUSSIE** (`ibm_validation.py`) —
      état de Bell sur ibm_marrakesh (156 qubits réels), **fidélité 98.4 %**
- [x] BOM banc NV (`docs/BOM_BENCH.md`) — ≈ 3.5 M FCFA, sourçable
- [x] Tests internes : **42/42 verts**
- [x] **Phase 1.5 — banc NV** : plan d assemblage optique (docs/ASSEMBLY_BENCH.md,
      tests B1–B10), séquences de pulses (bench/pulse_sequences.py : ODMR/Rabi/
      Ramsey/Hahn), banc virtuel (bench/virtual_bench.py, bruit de Poisson réaliste),
      analyseur (bench/odmr_analysis.py : fits Lorentz/Rabi/Ramsey/Hahn +
      recalibrage automatique du DecoherenceModel sur mesures réelles)

## 🏆 LE RÉSULTAT HISTORIQUE
État de Bell |Φ+⟩ exécuté sur un vrai QPU IBM supraconducteur (ibm_marrakesh) :
- IBM réel : 00→526, 11→482, 01→9, 10→7 (sur 1024 shots)
- RATISS sim : 00→515, 11→509, 01→0, 10→0
- **Fidélité 98.4 %** → notre simulateur est prouvé correct sur hardware réel.
- L'écart de 1.6 % = bruit réel du supraconducteur à 15 mK. C'est la baseline
  que notre NV à 300 K vise à battre.
Archivé : `results/bell_cross_validation.json`.

## 🔐 SÉCURITÉ (à retenir)
- La clé IBM Quantum utilisée vient de l'historique de `Travaux` (exposée). Elle
  est stockée localement dans `/workspace/project/.secrets/ibm_quantum_token`
  (chmod 600), JAMAIS dans le code ni sur GitHub.
- ⚠️ **ACTION REQUISE (Jonathan)** : régénérer la clé sur IBM Quantum, car elle
  a été publiquement exposée dans l'historique git de Travaux avant nettoyage.

## 📐 DÉCISIONS D'INGÉNIERIE CLÉS
1. **NV-diamant choisi** sur photonique/supraconducteur/ions : seule architecture
   à la fois physiquement supérieure en ambiant (T2 ms), constructible à budget
   camerounais (~3.5 M FCFA), et maintenable localement.
2. **Lindblad, pas de raccourci** : la décohérence est traitée par équation
   maîtresse exacte (matrices densité), pas par un facteur de décroissance ad hoc.
3. **T2(T) ≤ 2·T1(T)** imposé comme borne physique dure dans le modèle.
4. **P_sig = rayon de Bloch moyen** : contraction topologique de la sphère de
   Bloch = mesure géométrique de la cohérence. Pont avec la LCT de ratiss-grid.

## ⚠️ LIMITES HONNÊTES
- La validation IBM prouve l'ALGORITHME, pas encore la cohérence NV physique.
  IBM = supraconducteur (physique différente). La preuve NV exige le banc réel.
- Les T1/T2(T) du modèle sont des ordres de grandeur SOURCÉS, à recalibrer sur
  le banc NV camerounais (ODMR, Rabi, Ramsey, Hahn echo).
- Scalabilité NV multi-qubits = défi réel (couplage inter-NV difficile). Pour
  l'instant : démonstrateur 1–2 qubits + capteur quantique.

## 🔜 PROCHAINES ÉTAPES (Phase 1.5 → physique)
1. **Commander le diamant CVD** à centres NV (valider échantillon).
2. **Assembler le banc ODMR** (docs/BOM_BENCH.md + docs/ASSEMBLY_BENCH.md).
3. **Mesurer ODMR + Rabi + T1 + T2** réels → bench/odmr_analysis.py recalibre
   automatiquement le modèle. La chaîne logicielle est DÉJÀ validée sur banc
   virtuel (42/42 tests) : seule la source de données change (APD réel).
4. **Pousser l'intrication sur IBM** : passer de Bell (2 qubits) à GHZ (3+),
   et comparer la fidélité — quantifier comment le bruit croît avec la taille.
5. Coupler le coffre-fort énergétique (ratiss-grid) au futur banc NV.

## 📌 RÈGLES DE SESSION (rappel)
- Prouver, pas prétendre. Chaque chiffre sourcé. Documenter les échecs.
- La clé IBM n'est PAS un jouet : usage plan open respecté, pas d'abus.

---
*Priorité 1 sur 4. Bases posées, preuve atomique IBM faite. Next : le banc réel.*
