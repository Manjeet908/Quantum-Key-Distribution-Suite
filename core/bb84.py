"""
BB84 Quantum Key Distribution Protocol (Bennett & Brassard, 1984).
4-state encoding in rectilinear (Z) and diagonal (X) bases.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import numpy as np
from qiskit import QuantumCircuit
from core.qiskit_engine import QiskitEngine
from attacks.intercept_resend import InterceptResendAttack, InterceptResult
from attacks.noise_channel import QuantumNoiseChannel
from postprocessing.sifting import sift_bb84, SiftingResult
from postprocessing.privacy_amp import PrivacyAmplifier, DistillationResult

@dataclass
class BB84Result:
    """Full execution snapshot of BB84 protocol."""
    num_qubits: int
    alice_bits: List[int]
    alice_bases: List[int]        # 0 = Z (|0>, |1>), 1 = X (|+>, |->)
    bob_bases: List[int]
    bob_measured_bits: List[int]
    circuit: QuantumCircuit
    intercept_result: Optional[InterceptResult]
    sifting_result: SiftingResult
    distillation_result: DistillationResult
    noise_level: float
    attack_name: str
    security_status: str          # "SECURE", "WARNING", "COMPROMISED"

class BB84Protocol:
    """Simulates BB84 protocol end-to-end on Qiskit AerSimulator."""

    def __init__(self, engine: Optional[QiskitEngine] = None, seed: Optional[int] = None):
        self.engine = engine or QiskitEngine(seed=seed)
        self.rng = np.random.default_rng(seed)

    def run(
        self,
        num_qubits: int = 24,
        attack: Optional[Any] = None,
        noise_level: float = 0.0,
        bit_flip_rate: float = 0.0
    ) -> BB84Result:
        """
        Executes BB84:
        1. Alice generates random bits and bases. 
        2. Alice prepares qubits.
        3. Channel transmission with optional Eve intercept and channel noise.
        4. Bob measures in random bases.
        5. Key sifting, QBER calculation, and privacy amplification.
        """
        from qiskit import QuantumRegister, ClassicalRegister

        alice_bits = [int(b) for b in self.rng.integers(0, 2, size=num_qubits)]
        alice_bases = [int(b) for b in self.rng.integers(0, 2, size=num_qubits)]
        bob_bases = [int(b) for b in self.rng.integers(0, 2, size=num_qubits)]

        is_intercept = isinstance(attack, InterceptResendAttack)
        eve_present = is_intercept and attack.intercept_prob > 0.0

        qr = QuantumRegister(num_qubits, "q")
        cr_bob = ClassicalRegister(num_qubits, "bob")
        if eve_present:
            cr_eve = ClassicalRegister(num_qubits, "eve")
            qc = QuantumCircuit(qr, cr_bob, cr_eve)
        else:
            cr_eve = None
            qc = QuantumCircuit(qr, cr_bob)

        # ----------------------------------------------------
        # Step 1: Alice Prepares Qubits
        # ----------------------------------------------------
        for i in range(num_qubits):
            bit = alice_bits[i]
            basis = alice_bases[i]
            if bit == 1:
                qc.x(qr[i])
            if basis == 1:  # X-basis
                qc.h(qr[i])
        qc.barrier(label="Alice Prep")

        # ----------------------------------------------------
        # Step 2: Quantum Channel (Eve Interception & Noise)
        # ----------------------------------------------------
        intercepted_flags = []
        eve_bases = []
        noise_channel = QuantumNoiseChannel(depolarizing_rate=noise_level, bit_flip_rate=bit_flip_rate)

        for i in range(num_qubits):
            # Eve Intercept-Resend
            if eve_present and cr_eve is not None:
                intercepted, e_basis = attack.apply_to_qubit(qc, qr[i], cr_eve[i], self.rng)
                intercepted_flags.append(intercepted)
                eve_bases.append(e_basis)
            else:
                intercepted_flags.append(False)
                eve_bases.append(0)
            
            # Channel Environmental Noise
            noise_channel.apply_to_circuit(qc, qr[i], self.rng)

        if eve_present or noise_level > 0:
            qc.barrier(label="Channel")

        # ----------------------------------------------------
        # Step 3: Bob's Measurement
        # ----------------------------------------------------
        for i in range(num_qubits):
            if bob_bases[i] == 1: # X-basis
                qc.h(qr[i])
            qc.measure(qr[i], cr_bob[i])

        # ----------------------------------------------------
        # Step 4: Circuit Simulation
        # ----------------------------------------------------
        bob_measured, eve_measured = self.engine.sample_registers(qc)

        # ----------------------------------------------------
        # Step 5: Sifting & Metrics
        # ----------------------------------------------------
        sift_res = sift_bb84(alice_bits, alice_bases, bob_measured, bob_bases, security_threshold=0.11)

        # Eve Intercept Result Logging
        int_res = None
        if eve_present:
            int_res = InterceptResult(
                intercepted=intercepted_flags,
                eve_bases=eve_bases,
                eve_bits=eve_measured if eve_measured else [None] * num_qubits,
                interception_rate=sum(intercepted_flags) / num_qubits,
                total_qubits=num_qubits,
                qubits_intercepted_count=sum(intercepted_flags)
            )

        # ----------------------------------------------------
        # Step 6: Privacy Amplification
        # Based strictly on observable QBER (Shor-Preskill / Devetak-Winter bound)
        # ----------------------------------------------------
        distill_res = PrivacyAmplifier.distill_secret_key(
            sift_res.alice_sifted,
            sift_res.bob_sifted,
            sift_res.qber,
            eve_info_fraction=0.0,
            security_threshold=0.11
        )

        # Security Status
        if sift_res.qber > 0.11:
            status = "COMPROMISED"
        elif sift_res.qber > 0.05:
            status = "WARNING"
        else:
            status = "SECURE"

        attack_label = "None"
        if eve_present:
            attack_label = f"Intercept-Resend ({attack.intercept_prob*100:.0f}%)"

        return BB84Result(
            num_qubits=num_qubits,
            alice_bits=alice_bits,
            alice_bases=alice_bases,
            bob_bases=bob_bases,
            bob_measured_bits=bob_measured,
            circuit=qc,
            intercept_result=int_res,
            sifting_result=sift_res,
            distillation_result=distill_res,
            noise_level=noise_level,
            attack_name=attack_label,
            security_status=status
        )
