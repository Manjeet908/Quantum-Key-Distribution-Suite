"""
B92 Quantum Key Distribution Protocol (Bennett, 1992).
Two-state non-orthogonal encoding (|0> and |+>) with conclusive/inconclusive detection.
"""
from dataclasses import dataclass
from typing import List, Optional, Any
import numpy as np
from qiskit import QuantumCircuit
from core.qiskit_engine import QiskitEngine
from attacks.intercept_resend import InterceptResendAttack, InterceptResult
from attacks.noise_channel import QuantumNoiseChannel
from postprocessing.sifting import sift_b92, SiftingResult
from postprocessing.privacy_amp import PrivacyAmplifier, DistillationResult

@dataclass
class B92Result:
    """Full execution snapshot of B92 protocol."""
    num_qubits: int
    alice_bits: List[int]
    alice_states: List[str]            # "|0>" for bit 0, "|+>" for bit 1
    bob_bases: List[int]               # 0 = Measure for |1>, 1 = Measure for |->
    bob_raw_measurements: List[int]
    bob_conclusive: List[bool]
    bob_inferred_bits: List[int]
    circuit: QuantumCircuit
    intercept_result: Optional[InterceptResult]
    sifting_result: SiftingResult
    distillation_result: DistillationResult
    noise_level: float
    attack_name: str
    security_status: str

class B92Protocol:
    """Simulates B92 protocol end-to-end on Qiskit AerSimulator."""

    def __init__(self, engine: Optional[QiskitEngine] = None, seed: Optional[int] = None):
        self.engine = engine or QiskitEngine(seed=seed)
        self.rng = np.random.default_rng(seed)

    def run(
        self,
        num_qubits: int = 24,
        attack: Optional[Any] = None,
        noise_level: float = 0.0,
        bit_flip_rate: float = 0.0
    ) -> B92Result:
        """
        Executes B92 protocol:
        1. Alice sends |0> for bit 0, |+> for bit 1.
        2. Channel / Eve interaction.
        3. Bob tests for non-orthogonal state:
           - Basis 0: tests orthogonal to |0> (measures in standard basis; outcome 1 => Alice sent 1)
           - Basis 1: tests orthogonal to |+> (measures in X basis; outcome 1 => Alice sent 0)
        4. Bob flags conclusive events (outcome == 1).
        5. Sifting and QBER analysis (4.8% threshold).
        """
        from qiskit import QuantumRegister, ClassicalRegister

        alice_bits = [int(b) for b in self.rng.integers(0, 2, size=num_qubits)]
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
        # Step 1: Alice Prepares States (|0> or |+>)
        # ----------------------------------------------------
        alice_states = []
        for i in range(num_qubits):
            if alice_bits[i] == 1:
                qc.h(qr[i])   # Bit 1: prepare |+>
                alice_states.append("|+>")
            else:
                alice_states.append("|0>")  # Bit 0: prepare |0>
        qc.barrier(label="Alice Prep")

        # ----------------------------------------------------
        # Step 2: Channel & Eve Interaction
        # ----------------------------------------------------
        intercepted_flags = []
        eve_bases = []
        noise_channel = QuantumNoiseChannel(depolarizing_rate=noise_level, bit_flip_rate=bit_flip_rate)

        for i in range(num_qubits):
            if eve_present and cr_eve is not None:
                intercepted, e_basis = attack.apply_to_qubit(qc, qr[i], cr_eve[i], self.rng)
                intercepted_flags.append(intercepted)
                eve_bases.append(e_basis)
            else:
                intercepted_flags.append(False)
                eve_bases.append(0)

            noise_channel.apply_to_circuit(qc, qr[i], self.rng)

        if eve_present or noise_level > 0:
            qc.barrier(label="Channel")

        # ----------------------------------------------------
        # Step 3: Bob's Measurement
        # ----------------------------------------------------
        for i in range(num_qubits):
            if bob_bases[i] == 1:
                qc.h(qr[i])
            qc.measure(qr[i], cr_bob[i])

        # ----------------------------------------------------
        # Step 4: Execute Circuit
        # ----------------------------------------------------
        bob_raw, eve_raw = self.engine.sample_registers(qc)

        # ----------------------------------------------------
        # Step 5: Inconclusive vs Conclusive Processing
        # ----------------------------------------------------
        bob_conclusive = []
        bob_inferred = []
        for i in range(num_qubits):
            measured_val = bob_raw[i]
            if measured_val == 1:
                bob_conclusive.append(True)
                # If Bob tested Basis 0 and measured 1: Alice must have sent 1
                # If Bob tested Basis 1 and measured 1: Alice must have sent 0
                inferred = 1 if bob_bases[i] == 0 else 0
                bob_inferred.append(inferred)
            else:
                bob_conclusive.append(False)
                bob_inferred.append(-1)  # Inconclusive / discard

        # ----------------------------------------------------
        # Step 6: Sifting & Security Analysis (4.8% cutoff)
        # ----------------------------------------------------
        sift_res = sift_b92(alice_bits, bob_conclusive, bob_inferred, security_threshold=0.048)

        int_res = None
        if eve_present:
            int_res = InterceptResult(
                intercepted=intercepted_flags,
                eve_bases=eve_bases,
                eve_bits=eve_raw if eve_raw else [None] * num_qubits,
                interception_rate=sum(intercepted_flags) / num_qubits,
                total_qubits=num_qubits,
                qubits_intercepted_count=sum(intercepted_flags)
            )

        # Step 6: Privacy Amplification based strictly on observable QBER
        distill_res = PrivacyAmplifier.distill_secret_key(
            sift_res.alice_sifted,
            sift_res.bob_sifted,
            sift_res.qber,
            eve_info_fraction=0.0,
            security_threshold=0.048
        )

        if sift_res.qber > 0.048:
            status = "COMPROMISED"
        elif sift_res.qber > 0.02:
            status = "WARNING"
        else:
            status = "SECURE"

        attack_label = f"Intercept-Resend ({attack.intercept_prob*100:.0f}%)" if eve_present else "None"

        return B92Result(
            num_qubits=num_qubits,
            alice_bits=alice_bits,
            alice_states=alice_states,
            bob_bases=bob_bases,
            bob_raw_measurements=bob_raw,
            bob_conclusive=bob_conclusive,
            bob_inferred_bits=bob_inferred,
            circuit=qc,
            intercept_result=int_res,
            sifting_result=sift_res,
            distillation_result=distill_res,
            noise_level=noise_level,
            attack_name=attack_label,
            security_status=status
        )
