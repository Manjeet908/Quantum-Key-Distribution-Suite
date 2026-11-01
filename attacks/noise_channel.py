import numpy as np
from qiskit import QuantumCircuit

class QuantumNoiseChannel:
    """Configurable physical channel noise model for quantum communication."""
    
    def __init__(self, depolarizing_rate: float = 0.0, bit_flip_rate: float = 0.0, channel_loss: float = 0.0):
        self.depolarizing_rate = float(np.clip(depolarizing_rate, 0.0, 0.5))
        self.bit_flip_rate = float(np.clip(bit_flip_rate, 0.0, 0.5))
        self.channel_loss = float(np.clip(channel_loss, 0.0, 0.9))

    def apply_to_circuit(self, circuit: QuantumCircuit, qubit_idx: int, rng: np.random.Generator) -> bool:
        """
        Applies stochastic noise directly into the circuit at the given qubit.
        Returns False if the photon was lost in transit due to channel loss, True otherwise.
        """
        # 1. Photon loss check
        if self.channel_loss > 0.0 and rng.random() < self.channel_loss:
            return False  # Photon lost
        
        # 2. Bit flip / Phase flip
        if self.bit_flip_rate > 0.0 and rng.random() < self.bit_flip_rate:
            circuit.x(qubit_idx)
            
        # 3. Depolarizing noise (random Pauli X, Y, or Z)
        if self.depolarizing_rate > 0.0 and rng.random() < self.depolarizing_rate:
            pauli_choice = rng.choice(['X', 'Y', 'Z'])
            if pauli_choice == 'X':
                circuit.x(qubit_idx)
            elif pauli_choice == 'Y':
                circuit.y(qubit_idx)
            elif pauli_choice == 'Z':
                circuit.z(qubit_idx)
                
        return True
