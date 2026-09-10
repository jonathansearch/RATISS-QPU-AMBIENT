"""Tests internes RATISS-QPU-AMBIENT — validation physique.

Chaque test vérifie une VÉRITÉ PHYSIQUE, pas une convention de code :
- normalisation et unitarité (probabilités conservées)
- porte π inverse bien |0⟩ ↔ |1⟩
- Born : les probabilités de mesure suivent |amplitude|²
- Lindblad préserve la trace et la positivité (ρ reste une matrice densité)
- la décohérence détruit la cohérence (pureté décroît), jamais l'inverse
- T2 ≤ 2·T1 (borne physique absolue)
- la cohérence chute quand la température monte (sens physique correct)
- P_sig distingue un état cohérent d'un état décohéré
"""

from __future__ import annotations

import numpy as np
import pytest

from ratiss_qpu.qstate import (H, X, apply_gate, bloch_state, bloch_vector,
                               is_normalized, ket0, ket1, measure_z, purity)
from ratiss_qpu.nv_center import NVCenter
from ratiss_qpu.coherence import (DecoherenceModel, bloch_trajectory,
                                  evolve_open, psig_coherence)
from ratiss_qpu.benchmark import compare_architectures, figure_of_merit


class TestQuantumState:
    def test_ket0_normalized(self):
        assert is_normalized(ket0())

    def test_bloch_state_normalized_any_angle(self):
        for theta, phi in [(0.3, 1.1), (1.2, 2.5), (np.pi, 0.0)]:
            assert is_normalized(bloch_state(theta, phi))

    def test_hadamard_creates_superposition(self):
        s = apply_gate(ket0(), H)
        assert abs(abs(s[0]) ** 2 - 0.5) < 1e-9
        assert abs(abs(s[1]) ** 2 - 0.5) < 1e-9

    def test_non_unitary_gate_rejected(self):
        with pytest.raises(ValueError):
            apply_gate(ket0(), np.array([[1, 1], [0, 0]], dtype=complex))

    def test_born_probabilities(self):
        rng = np.random.default_rng(42)
        # état avec p(0)=0.75
        s = bloch_state(2.0 * np.arccos(np.sqrt(0.75)), 0.0)
        outcomes = [measure_z(s, rng)[0] for _ in range(4000)]
        freq0 = outcomes.count(0) / len(outcomes)
        assert abs(freq0 - 0.75) < 0.04   # fluctuation statistique ~1%

    def test_pure_state_has_purity_one(self):
        s = bloch_state(0.7, 0.9)
        assert abs(purity(np.outer(s, s.conj())) - 1.0) < 1e-9


class TestNVCenter:
    def test_zeeman_transition(self):
        nv = NVCenter(b_tesla=0.05)
        # D − γB = 2.87e9 − 28e9×0.05 = 1.47 GHz
        assert abs(nv.transition_hz - 1.47e9) / 1.47e9 < 1e-3

    def test_pi_pulse_flips_state(self):
        nv = NVCenter()
        s1 = apply_gate(ket0(), nv.pi_pulse())
        assert abs(abs(s1[1]) ** 2 - 1.0) < 1e-6   # |0⟩ → |1⟩

    def test_two_pi_pulses_return(self):
        nv = NVCenter()
        s = apply_gate(apply_gate(ket0(), nv.pi_pulse()), nv.pi_pulse())
        assert abs(abs(s[0]) ** 2 - 1.0) < 1e-6   # retour à |0⟩

    def test_rabi_period(self):
        nv = NVCenter(rabi_hz=1.0e6)
        # après une demi-période de Rabi (π), on a basculé
        s = nv.rabi_evolution(ket0(), nv.gate_time_s(np.pi))
        assert abs(abs(s[1]) ** 2 - 1.0) < 1e-6


class TestDecoherence:
    def test_trace_preserved(self):
        model = DecoherenceModel()
        rho0 = np.outer(bloch_state(0.5, 0.0), bloch_state(0.5, 0.0).conj())
        rho = evolve_open(rho0, np.zeros((2, 2)), 1e-4, model, 300.0)
        assert abs(np.trace(rho) - 1.0) < 1e-6

    def test_positivity_preserved(self):
        model = DecoherenceModel()
        rho0 = np.outer(ket0(), ket0().conj())
        rho = evolve_open(rho0, np.zeros((2, 2)), 1e-3, model, 300.0)
        eig = np.linalg.eigvalsh(rho)
        assert np.all(eig >= -1e-9)   # ρ reste positive semi-définie

    def test_coherence_decays_with_time(self):
        model = DecoherenceModel()
        s = bloch_state(np.pi / 2, 0.0)   # superposition équatoriale
        rho0 = np.outer(s, s.conj())
        p_early = purity(evolve_open(rho0, np.zeros((2, 2)), 1e-6, model, 300.0))
        p_late = purity(evolve_open(rho0, np.zeros((2, 2)), 5e-3, model, 300.0))
        assert p_late < p_early   # la cohérence ne peut que décroître

    def test_t2_bounded_by_2t1(self):
        model = DecoherenceModel()
        for t in [250, 300, 313, 350]:
            assert model.t2_s(t) <= 2.0 * model.t1_s(t) + 1e-12

    def test_hotter_less_coherent(self):
        # Sens physique : la chaleur détruit la cohérence (T2 décroît avec T)
        model = DecoherenceModel()
        assert model.t2_s(350.0) < model.t2_s(300.0)
        assert model.t1_s(350.0) < model.t1_s(300.0)


class TestTopologicalSignature:
    def test_psig_high_for_coherent(self):
        # état cohérent tournant près de la surface → P_sig proche de 1
        model = DecoherenceModel(t2_300k_s=10.0)   # très cohérent
        s = bloch_state(np.pi / 2, 0.0)
        rho0 = np.outer(s, s.conj())
        traj = bloch_trajectory(rho0, 0.5 * np.pi * X, 1e-4, model, 300.0)
        assert psig_coherence(traj) > 0.9

    def test_psig_lower_for_decohered(self):
        s = bloch_state(np.pi / 2, 0.0)
        rho0 = np.outer(s, s.conj())
        # décohérence rapide vs lente
        fast = DecoherenceModel(t1_300k_s=1e-4, t2_300k_s=5e-5)
        slow = DecoherenceModel(t1_300k_s=1.0, t2_300k_s=0.5)
        p_fast = psig_coherence(bloch_trajectory(rho0, np.zeros((2, 2)), 1e-3, fast, 300.0))
        p_slow = psig_coherence(bloch_trajectory(rho0, np.zeros((2, 2)), 1e-3, slow, 300.0))
        assert p_fast < p_slow


class TestBenchmark:
    def test_figure_of_merit(self):
        assert figure_of_merit(1e-3, 1e-6) == pytest.approx(1e3)

    def test_nv_beats_superconductor_on_ops(self):
        rows = dict((r[0], r[3]) for r in compare_architectures())
        # NV ¹²C purifié doit dépasser le supraconducteur en ops cohérentes
        assert rows["NV-diamant (12C purifié)"] > rows["Supraconducteur (réf.)"]


# =====================================================================
# Tests de la validation 2-qubits + IBM (Bell, concurrence, fidélité)
# =====================================================================
from ratiss_qpu.two_qubit import (bell_state, concurrence_pure,
                                  measure_probabilities, sample_2q, state_00)
from ratiss_qpu.ibm_validation import fidelity, run_on_simulator


class TestTwoQubit:
    def test_bell_state_probabilities(self):
        probs = measure_probabilities(bell_state())
        assert abs(probs["00"] - 0.5) < 1e-9
        assert abs(probs["11"] - 0.5) < 1e-9
        assert abs(probs["01"]) < 1e-9
        assert abs(probs["10"]) < 1e-9

    def test_bell_state_maximally_entangled(self):
        assert abs(concurrence_pure(bell_state()) - 1.0) < 1e-9

    def test_product_state_zero_concurrence(self):
        assert abs(concurrence_pure(state_00())) < 1e-9

    def test_bell_sampling_matches_ideal(self):
        rng = np.random.default_rng(1)
        counts = sample_2q(bell_state(), 4000, rng)
        total = sum(counts.values())
        bell_pop = (counts["00"] + counts["11"]) / total
        assert bell_pop > 0.95

    def test_simulator_distribution_bell(self):
        counts = run_on_simulator(shots=2000, seed=7)
        total = sum(counts.values())
        assert (counts["00"] + counts["11"]) / total > 0.95


class TestFidelity:
    def test_identical_distributions(self):
        a = {"00": 500, "11": 500}
        assert fidelity(a, a) == pytest.approx(1.0)

    def test_disjoint_distributions(self):
        a = {"00": 1000}
        b = {"11": 1000}
        assert fidelity(a, b) == pytest.approx(0.0)

    def test_similar_distributions_high_fidelity(self):
        a = {"00": 500, "11": 500, "01": 0, "10": 0}
        b = {"00": 510, "11": 480, "01": 5, "10": 5}
        assert fidelity(a, b) > 0.95
