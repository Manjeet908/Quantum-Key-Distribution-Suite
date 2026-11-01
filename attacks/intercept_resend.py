"""
Intercept-Resend Eavesdropping Attack.
Eve measures the flying qubits in a randomly selected basis and resends
her measured state to Bob, inevitably disturbing non-orthogonal quantum states.
"""
from dataclasses import dataclass
from typing import List, Optional
import numpy as np
from qiskit import QuantumCircuit

@dataclass
class InterceptResult:
    """Detailed log of Eve's eavesdropping activity."""
    intercepted: List[bool]
    eve_bases: List[int]       # 0 = Z (rectilinear), 1 = X (diagonal)
    eve_bits: List[Optional[int]]
    interception_rate: float
    total_qubits: int
    qubits_intercepted_count: int

class InterceptResendAttack:
    """Simulates an Intercept-Resend attack on single-qubit transmissions."""
    
    def __init__(self, intercept_prob: float = 1.0):
        """
        Args:
            intercept_prob: Probability (0.0 to 1.0) that Eve intercepts an individual qubit.
        """
        self.intercept_prob = float(np.clip(intercept_prob, 0.0, 1.0))

    def apply_to_qubit(
        self,
        circuit: QuantumCircuit,
        qubit_idx: int,
        eve_clbit_idx: Optional[int],
        rng: np.random.Generator
    ) -> tuple[bool, int]:
        """
        Applies Eve's interception to a specific qubit in the circuit.
        Returns:
            (is_intercepted, eve_basis)
        """
        if rng.random() > self.intercept_prob:
            return False, 0
        
        # Eve picks a random basis: 0 = Z, 1 = X
        eve_basis = int(rng.integers(0, 2))
        
        # Rotate if X basis
        if eve_basis == 1:
            circuit.h(qubit_idx)
            
        # Eve measures the qubit to collapse it
        if eve_clbit_idx is not None:
            circuit.measure(qubit_idx, eve_clbit_idx)
            
        # Re-prepare / rotate back to transmit to Bob
        if eve_basis == 1:
            circuit.h(qubit_idx)
            
        return True, eve_basis
