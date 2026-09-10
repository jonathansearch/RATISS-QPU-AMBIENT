"""Tests du banc NV — validation de la chaîne de mesure complète (banc virtuel).

Le test clé : on génère des données expérimentales bruitées avec le banc virtuel
(en y injectant des paramètres physiques CONNUS), puis on vérifie que l'analyseur
retrouve ces paramètres. C'est la validation de bout-en-bout de la chaîne de
mesure AVANT d'acheter le moindre composant — la preuve que notre logiciel
d'analyse est correct.

Doctrine : si le logiciel ne retrouve pas les bons paramètres sur des données
simulées parfaites, il ne le fera pas sur des données réelles. On valide ici.
"""

from __future__ import annotations

import numpy as np
import pytest

from bench.pulse_sequences import (hahn_echo_sequence, odmr_sequence,
                                   rabi_sequence, ramsey_sequence)
from bench.virtual_bench import VirtualBench
from bench.odmr_analysis import (BenchMeasurements, b_field_from_resonance,
                                 fit_hahn, fit_odmr, fit_rabi, fit_ramsey,
                                 recalibrate_model)
from ratiss_qpu.nv_center import NVCenter, D_ZERO_FIELD_HZ


class TestPulseSequences:
    def test_odmr_sweeps_frequency(self):
        assert odmr_sequence().sweep_param == "frequency"

    def test_rabi_has_variable_mw_pulse(self):
        seq = rabi_sequence(tau_s=0.5e-6, pi_time_s=0.5e-6)
        mw = [p for p in seq.pulses if p.channel == "mw"]
        assert len(mw) == 1 and abs(mw[0].duration_s - 0.5e-6) < 1e-12

    def test_ramsey_is_pi_half_free_pi_half(self):
        seq = ramsey_sequence(tau_s=1e-6, pi_half_time_s=0.25e-6)
        mw = [p for p in seq.pulses if p.channel == "mw"]
        assert [p.kind for p in mw] == ["pi_half", "pi_half"]

    def test_hahn_has_central_pi_pulse(self):
        seq = hahn_echo_sequence(1e-6, 0.25e-6, 0.5e-6)
        mw = [p for p in seq.pulses if p.channel == "mw"]
        assert [p.kind for p in mw] == ["pi_half", "pi", "pi_half"]


class TestVirtualBench:
    def test_odmr_dip_at_resonance(self):
        # La fluorescence est plus basse à la résonance qu'hors résonance
        b = VirtualBench(seed=0)
        res = b.resonance_hz()
        on = np.mean([b.odmr_point(res) for _ in range(200)])
        off = np.mean([b.odmr_point(res + 50e6) for _ in range(200)])
        assert on < off

    def test_resonance_matches_zeeman(self):
        nv = NVCenter(b_tesla=0.05)
        b = VirtualBench(nv=nv, seed=0)
        assert abs(b.resonance_hz() - 1.47e9) / 1.47e9 < 1e-3

    def test_photon_counts_are_nonnegative(self):
        b = VirtualBench(seed=1)
        assert all(c >= 0 for c in [b.odmr_point(2.87e9) for _ in range(50)])


class TestEndToEndAnalysis:
    """La validation de bout-en-bout : on injecte des paramètres connus, on
    vérifie que l'analyse les retrouve malgré le bruit de photon."""

    def test_recover_odmr_resonance(self):
        nv = NVCenter(b_tesla=0.05)   # résonance = 1.47 GHz
        b = VirtualBench(nv=nv, fluorescence_ms0=5e6, contrast=0.3, seed=2)
        freqs, counts = b.sweep_odmr(1.40e9, 1.54e9, 120)
        result = fit_odmr(freqs, counts)
        assert result["success"]
        # on doit retrouver la résonance à mieux que 1 %
        assert abs(result["resonance_hz"] - 1.47e9) / 1.47e9 < 0.01

    def test_recover_rabi_frequency(self):
        nv = NVCenter(rabi_hz=2.0e6)   # Ω = 2 MHz
        b = VirtualBench(nv=nv, fluorescence_ms0=5e6, contrast=0.3, seed=3)
        taus, counts = b.sweep_rabi(3.0e-6, 150)
        result = fit_rabi(taus, counts)
        assert result["success"]
        assert abs(result["rabi_hz"] - 2.0e6) / 2.0e6 < 0.15   # ±15 % (bruit)

    def test_recover_ramsey_t2star(self):
        b = VirtualBench(fluorescence_ms0=8e6, contrast=0.3, seed=4)
        t2star_true = 3.0e-6
        taus, counts = b.sweep_ramsey(15e-6, 150, t2star_s=t2star_true, detuning_hz=1.5e6)
        result = fit_ramsey(taus, counts)
        assert result["success"]
        # T2* retrouvé dans une fourchette raisonnable (le fit est dur sous bruit)
        assert 0.3 * t2star_true < result["t2star_s"] < 3.0 * t2star_true

    def test_recover_hahn_t2(self):
        b = VirtualBench(fluorescence_ms0=8e6, contrast=0.3, seed=5)
        t2_true = 50.0e-6
        taus, counts = b.sweep_hahn(200e-6, 120, t2_s=t2_true)
        result = fit_hahn(taus, counts)
        assert result["success"]
        assert 0.3 * t2_true < result["t2_s"] < 3.0 * t2_true


class TestRecalibration:
    def test_b_field_from_resonance(self):
        # f_res = 1.47 GHz → B = (2.87 − 1.47)/28 = 0.05 T
        b = b_field_from_resonance(1.47e9)
        assert abs(b - 0.05) < 1e-3

    def test_recalibrate_injects_measured_t2(self):
        meas = BenchMeasurements(t1_s=6e-3, t2_s=2e-3)
        model = recalibrate_model(meas)
        assert abs(model.t1_300k_s - 6e-3) < 1e-12
        assert abs(model.t2_300k_s - 2e-3) < 1e-12

    def test_recalibrate_never_invents_values(self):
        # Si rien n'est mesuré, on garde les défauts documentés (pas de magie)
        model = recalibrate_model(BenchMeasurements())
        assert model.t1_300k_s == 5.0e-3   # défaut Jarmola
        assert model.t2_300k_s == 1.0e-3   # défaut diamant naturel

    def test_recalibrated_model_respects_t2_bound(self):
        meas = BenchMeasurements(t1_s=5e-3, t2_s=8e-3)   # T2 > 2·T1 serait non-physique
        model = recalibrate_model(meas)
        # la borne physique T2 ≤ 2·T1 doit toujours tenir à 300 K
        assert model.t2_s(300.0) <= 2.0 * model.t1_s(300.0) + 1e-12


class TestFigureGeneration:
    def test_generate_figures_produces_valid_pngs(self, tmp_path):
        # Le script de figures doit produire 9 PNG valides (taille > 1 KB)
        import scripts.generate_figures as g
        g.OUT = str(tmp_path)
        g.fig_schema_optique()
        g.fig_sequences()
        g.fig_mesures()
        g.fig_bloch()
        g.fig_architectures()
        g.fig_plan_mecanique()
        g.fig_appareil_monte()
        g.fig_qpu_scientifique()
        g.fig_logo()
        for name in ["01_schema_optique.png", "02_sequences_pulses.png",
                     "03_mesures_banc.png", "04_sphere_bloch.png",
                     "05_comparatif_architectures.png", "06_plan_mecanique.png",
                     "07_appareil_monte.png", "08_qpu_scientifique.png",
                     "09_logo_ratis_labs.png"]:
            p = tmp_path / name
            assert p.exists() and p.stat().st_size > 1000
