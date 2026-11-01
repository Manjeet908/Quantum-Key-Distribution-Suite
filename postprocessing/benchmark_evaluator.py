"""
Benchmark Evaluator and Analytics Engine for QKD Protocols.
Provides empirical and closed-form theoretical analysis for BB84, B92, and E91:
- Sifting efficiency and key yield
- Quantum Bit Error Rate (QBER)
- B92 Conclusive Detection Rate (USD)
- E91 CHSH Bell Inequality Analysis
- Attack Detection (Power) and False Alarm Rates (ROC)
- Devetak-Winter Final Secret Key Distillation Rates
"""
import time
import math
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy.stats import binom

from core.bb84 import BB84Protocol
from core.b92 import B92Protocol
from core.e91 import E91Protocol
from attacks.intercept_resend import InterceptResendAttack


def binary_entropy(p: float) -> float:
    """Computes binary Shannon entropy h(p) = -p*log2(p) - (1-p)*log2(1-p)."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def secret_key_rate(sifted_yield: float, qber: float, f_ec: float = 1.16) -> float:
    """
    Computes Devetak-Winter / Shor-Preskill asymptotic secret key rate:
    R = max(0, Yield * [1 - h(QBER) - f_ec * h(QBER)])
    """
    if qber >= 0.5 or qber <= 0.0:
        h = 0.0 if qber <= 0.0 else 1.0
    else:
        h = binary_entropy(qber)
    fraction = 1.0 - (1.0 + f_ec) * h
    return max(0.0, sifted_yield * fraction)


def calculate_attack_detection_and_false_alarm(
    n_samples: int = 40,
    qber_threshold: float = 0.11,
    noise_level: float = 0.02,
    eve_rate: float = 0.5
) -> Dict[str, float]:
    """
    Statistical hypothesis testing for eavesdropping detection:
    H0: Channel noise only (error prob p0 = noise / 2)
    H1: Eavesdropper present (error prob p1 = p0 + (eve_rate/4)*(1-noise))
    """
    p0 = max(1e-5, min(0.49, noise_level / 2.0))
    p1 = max(1e-5, min(0.49, p0 + (eve_rate / 4.0) * (1.0 - noise_level)))
    k_thresh = max(1, int(math.ceil(n_samples * qber_threshold)))

    p_false_alarm = float(1.0 - binom.cdf(k_thresh - 1, n_samples, p0))
    p_detection = float(1.0 - binom.cdf(k_thresh - 1, n_samples, p1))

    return {
        "n_samples": n_samples,
        "k_thresh": k_thresh,
        "p0_noise_error": p0,
        "p1_attack_error": p1,
        "false_alarm_rate": p_false_alarm,
        "detection_rate": p_detection
    }


def get_analytical_curves() -> Dict[str, Any]:
    """
    Generates pre-calculated benchmark datasets for zero-input analytical display.
    """
    # 1. Noise Sweep (0% to 16% depolarizing noise)
    noise_vals = np.linspace(0.0, 0.16, 33)
    noise_records = []
    for eps in noise_vals:
        # Theoretical QBER based on physical quantum channel models:
        # BB84: Single flying photon through depolarizing channel (QBER = eps / 2)
        qber_bb84 = eps / 2.0
        # B92: Non-orthogonal USD with 25% conclusive yield (Noise magnified on conclusive bits)
        qber_b92 = (eps / 2.0) / (0.25 + eps / 4.0) if (0.25 + eps / 4.0) > 0 else eps * 2.0
        # E91: Dual-arm entangled pair distribution (photons sent to both Alice and Bob)
        # Joint error probability = 1 - (1 - eps/2)^2 = eps * (1.0 - eps/4.0)
        qber_e91 = eps * (1.0 - eps / 4.0)
        
        # Secret key rates
        skr_bb84 = secret_key_rate(0.50, qber_bb84) if qber_bb84 <= 0.11 else 0.0
        skr_b92 = secret_key_rate(0.25, qber_b92) if qber_b92 <= 0.048 else 0.0
        
        # E91 Bell parameter S
        s_val = 2.8284 * (1.0 - 2.0 * eps)
        skr_e91 = secret_key_rate(0.222, qber_e91) if (qber_e91 <= 0.11 and s_val > 2.0) else 0.0

        noise_records.append({
            "Noise (ε)": round(eps, 4),
            "BB84 QBER (%)": round(qber_bb84 * 100, 2),
            "B92 QBER (%)": round(qber_b92 * 100, 2),
            "E91 QBER (%)": round(qber_e91 * 100, 2),
            "BB84 Secret Key Rate": round(skr_bb84, 4),
            "B92 Secret Key Rate": round(skr_b92, 4),
            "E91 Secret Key Rate": round(skr_e91, 4),
            "E91 Bell |S|": round(max(0.0, s_val), 3)
        })
    df_noise = pd.DataFrame(noise_records)

    # 2. Attack Sweep (Eve intercept prob 0% to 100% at noise=0.02)
    eve_vals = np.linspace(0.0, 1.0, 21)
    attack_records = []
    for eve_p in eve_vals:
        # BB84: Eve measuring in random basis produces ~25% error on intercepted pulses
        qber_bb84 = 0.01 + 0.25 * eve_p * (1.0 - 0.02)
        # B92: Eve measurement skews unambiguous state projections, leading to higher distortion
        qber_b92 = 0.018 + 0.29 * eve_p
        # E91: Eve intercepts Bob's arm, collapsing entanglement
        qber_e91 = 0.012 + 0.245 * eve_p
        
        # E91 S parameter drops from 2.828 to <= 1.414 as entanglement breaks
        s_e91 = max(0.0, 2.8284 * (1.0 - eve_p) + 1.4142 * eve_p - 0.05)
        
        attack_records.append({
            "Eve Intercept (%)": round(eve_p * 100, 1),
            "BB84 QBER (%)": round(qber_bb84 * 100, 2),
            "B92 QBER (%)": round(qber_b92 * 100, 2),
            "E91 QBER (%)": round(qber_e91 * 100, 2),
            "E91 Bell |S|": round(s_e91, 3),
            "BB84 Status": "SECURE" if qber_bb84 <= 0.11 else "ABORTED",
            "B92 Status": "SECURE" if qber_b92 <= 0.048 else "ABORTED",
            "E91 Status": "SECURE" if (qber_e91 <= 0.11 and s_e91 > 2.0) else "ABORTED"
        })
    df_attack = pd.DataFrame(attack_records)

    # 3. ROC Curve: Detection Rate vs False Alarm Rate (for n=50 check bits)
    roc_records = []
    taus = np.linspace(0.01, 0.20, 40)
    for t in taus:
        # BB84 ROC
        res_bb84 = calculate_attack_detection_and_false_alarm(n_samples=50, qber_threshold=t, noise_level=0.03, eve_rate=0.4)
        # B92 ROC
        res_b92 = calculate_attack_detection_and_false_alarm(n_samples=50, qber_threshold=t, noise_level=0.02, eve_rate=0.4)
        roc_records.append({
            "Threshold": round(t, 3),
            "BB84 False Alarm Rate (P_FA)": round(res_bb84["false_alarm_rate"], 4),
            "BB84 Detection Rate (P_D)": round(res_bb84["detection_rate"], 4),
            "B92 False Alarm Rate (P_FA)": round(res_b92["false_alarm_rate"], 4),
            "B92 Detection Rate (P_D)": round(res_b92["detection_rate"], 4)
        })
    df_roc = pd.DataFrame(roc_records)

    # 4. Vertical Protocol Architecture Comparison Matrix
    comparison_matrix = pd.DataFrame([
        {
            "Feature / Metric": "Quantum States / Encodings",
            "BB84": "4 States (|0⟩, |1⟩, |+⟩, |−⟩)",
            "B92": "2 States Non-Orthogonal (|0⟩, |+⟩)",
            "E91": "Entangled EPR Pairs (|Φ+⟩)"
        },
        {
            "Feature / Metric": "Bases Count",
            "BB84": "2 (Rectilinear Z, Diagonal X)",
            "B92": "2 Unambiguous State Projections",
            "E91": "3 Alice / 3 Bob Rotated Angles"
        },
        {
            "Feature / Metric": "Sifting Mechanism",
            "BB84": "Public Basis Reconciliation",
            "B92": "Conclusive Detection Filtering",
            "E91": "Coincident Key Pairs (2/9) + Bell Test"
        },
        {
            "Feature / Metric": "Theoretical Sifting Yield",
            "BB84": "50.0%",
            "B92": "25.0%",
            "E91": "22.2% (Key generation)"
        },
        {
            "Feature / Metric": "Conclusive Detection Rate",
            "BB84": "100% of matched bases",
            "B92": "25% (USD outcome = 1)",
            "E91": "Coincidence detector gated"
        },
        {
            "Feature / Metric": "QBER Security Threshold",
            "BB84": "11.0%",
            "B92": "4.8%",
            "E91": "11.0% (and |S| > 2.0)"
        },
        {
            "Feature / Metric": "Security Foundation",
            "BB84": "No-Cloning & Heisenberg",
            "B92": "Non-orthogonal Indistinguishability",
            "E91": "CHSH Bell Theorem (Device-Ind.)"
        }
    ])

    return {
        "df_noise": df_noise,
        "df_attack": df_attack,
        "df_roc": df_roc,
        "df_matrix": comparison_matrix
    }


def run_live_benchmark(
    num_qubits: int = 36,
    noise_level: float = 0.02,
    eve_intensity: float = 0.0
) -> Dict[str, Any]:
    """
    Executes BB84, B92, and E91 simultaneously on AerSimulator MPS backend
    under identical noise and attack settings for direct side-by-side comparison.
    """
    attack_obj = InterceptResendAttack(intercept_prob=eve_intensity) if eve_intensity > 0.0 else None

    # Run BB84
    t0 = time.perf_counter()
    bb84_runner = BB84Protocol()
    bb84_res = bb84_runner.run(num_qubits=num_qubits, attack=attack_obj, noise_level=noise_level)
    bb84_time = (time.perf_counter() - t0) * 1000.0

    # Run B92
    t0 = time.perf_counter()
    b92_runner = B92Protocol()
    b92_res = b92_runner.run(num_qubits=num_qubits, attack=attack_obj, noise_level=noise_level)
    b92_time = (time.perf_counter() - t0) * 1000.0

    # Run E91
    t0 = time.perf_counter()
    e91_runner = E91Protocol()
    e91_res = e91_runner.run(num_pairs=num_qubits, attack=attack_obj, noise_level=noise_level)
    e91_time = (time.perf_counter() - t0) * 1000.0

    # Compile Summary Data Table
    summary_data = [
        {
            "Protocol": "BB84",
            "Transmitted Qubits/Pairs": bb84_res.num_qubits,
            "Sifted Key (bits)": bb84_res.sifting_result.sifted_key_length,
            "Sifting Yield (%)": round(bb84_res.sifting_result.sifting_ratio * 100, 1),
            "Errors": bb84_res.sifting_result.error_count,
            "QBER (%)": round(bb84_res.sifting_result.qber * 100, 1),
            "Security Threshold": "11.0%",
            "Bell Test |S|": "N/A",
            "Final Secret Key (bits)": len(bb84_res.distillation_result.final_secret_key),
            "Key Rate (bits/qubit)": round(len(bb84_res.distillation_result.final_secret_key) / bb84_res.num_qubits, 3),
            "Security Verdict": bb84_res.security_status,
            "Execution Time (ms)": round(bb84_time, 1)
        },
        {
            "Protocol": "B92",
            "Transmitted Qubits/Pairs": b92_res.num_qubits,
            "Sifted Key (bits)": b92_res.sifting_result.sifted_key_length,
            "Sifting Yield (%)": round(b92_res.sifting_result.sifting_ratio * 100, 1),
            "Errors": b92_res.sifting_result.error_count,
            "QBER (%)": round(b92_res.sifting_result.qber * 100, 1),
            "Security Threshold": "4.8%",
            "Bell Test |S|": "N/A",
            "Final Secret Key (bits)": len(b92_res.distillation_result.final_secret_key),
            "Key Rate (bits/qubit)": round(len(b92_res.distillation_result.final_secret_key) / b92_res.num_qubits, 3),
            "Security Verdict": b92_res.security_status,
            "Execution Time (ms)": round(b92_time, 1)
        },
        {
            "Protocol": "E91",
            "Transmitted Qubits/Pairs": e91_res.num_pairs,
            "Sifted Key (bits)": e91_res.sifting_result.sifted_key_length,
            "Sifting Yield (%)": round(e91_res.sifting_result.sifting_ratio * 100, 1),
            "Errors": e91_res.sifting_result.error_count,
            "QBER (%)": round(e91_res.sifting_result.qber * 100, 1),
            "Security Threshold": "11.0% & |S|>2.0",
            "Bell Test |S|": f"{e91_res.chsh_result.s_value:.3f}",
            "Final Secret Key (bits)": len(e91_res.distillation_result.final_secret_key),
            "Key Rate (bits/qubit)": round(len(e91_res.distillation_result.final_secret_key) / e91_res.num_pairs, 3),
            "Security Verdict": e91_res.security_status,
            "Execution Time (ms)": round(e91_time, 1)
        }
    ]

    return {
        "summary_df": pd.DataFrame(summary_data),
        "bb84_res": bb84_res,
        "b92_res": b92_res,
        "e91_res": e91_res
    }
