"""
Sifting algorithms for BB84, B92, and E91 protocols.
Calculates basis reconciliation, inconclusive filtering, and QBER.
"""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SiftingResult:
    """Detailed summary of the sifting phase."""
    raw_key_length: int
    sifted_key_length: int
    sifting_ratio: float
    alice_sifted: List[int]
    bob_sifted: List[int]
    matching_indices: List[int]
    error_count: int
    qber: float                     # Quantum Bit Error Rate (0.0 to 1.0)
    security_threshold: float       # Protocol-specific cutoff (e.g. 0.11 for BB84)
    is_secure: bool

def sift_bb84(
    alice_bits: List[int],
    alice_bases: List[int],
    bob_bits: List[int],
    bob_bases: List[int],
    security_threshold: float = 0.11
) -> SiftingResult:
    """
    Standard BB84 sifting: retains bits where Alice's basis == Bob's basis.
    """
    raw_len = len(alice_bits)
    sifted_alice = []
    sifted_bob = []
    indices = []

    for i in range(raw_len):
        if alice_bases[i] == bob_bases[i]:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(bob_bits[i])
            indices.append(i)

    sifted_len = len(sifted_alice)
    errors = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
    qber = (errors / sifted_len) if sifted_len > 0 else 0.0
    is_sec = qber <= security_threshold and sifted_len > 0

    return SiftingResult(
        raw_key_length=raw_len,
        sifted_key_length=sifted_len,
        sifting_ratio=(sifted_len / raw_len) if raw_len > 0 else 0.0,
        alice_sifted=sifted_alice,
        bob_sifted=sifted_bob,
        matching_indices=indices,
        error_count=errors,
        qber=qber,
        security_threshold=security_threshold,
        is_secure=is_sec
    )

def sift_b92(
    alice_bits: List[int],
    bob_conclusive_flags: List[bool],
    bob_inferred_bits: List[int],
    security_threshold: float = 0.048
) -> SiftingResult:
    """
    B92 sifting: retains only events where Bob received a conclusive measurement result.
    """
    raw_len = len(alice_bits)
    sifted_alice = []
    sifted_bob = []
    indices = []

    for i in range(raw_len):
        if bob_conclusive_flags[i]:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(bob_inferred_bits[i])
            indices.append(i)

    sifted_len = len(sifted_alice)
    errors = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
    qber = (errors / sifted_len) if sifted_len > 0 else 0.0
    is_sec = qber <= security_threshold and sifted_len > 0

    return SiftingResult(
        raw_key_length=raw_len,
        sifted_key_length=sifted_len,
        sifting_ratio=(sifted_len / raw_len) if raw_len > 0 else 0.0,
        alice_sifted=sifted_alice,
        bob_sifted=sifted_bob,
        matching_indices=indices,
        error_count=errors,
        qber=qber,
        security_threshold=security_threshold,
        is_secure=is_sec
    )

def sift_e91(
    alice_bits: List[int],
    alice_bases: List[int],
    bob_bits: List[int],
    bob_bases: List[int],
    key_basis_pairs: List[tuple[int, int]] = [(1, 0), (2, 1)],
    security_threshold: float = 0.11
) -> SiftingResult:
    """
    E91 key sifting: retains bits where Alice and Bob measured in aligned key-generation bases.
    (e.g., Alice basis a_2 and Bob basis b_1 both align at pi/4, or a_3 and b_2 at pi/2).
    """
    raw_len = len(alice_bits)
    sifted_alice = []
    sifted_bob = []
    indices = []

    for i in range(raw_len):
        pair = (alice_bases[i], bob_bases[i])
        if pair in key_basis_pairs:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(bob_bits[i])
            indices.append(i)

    sifted_len = len(sifted_alice)
    errors = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
    qber = (errors / sifted_len) if sifted_len > 0 else 0.0
    is_sec = qber <= security_threshold and sifted_len > 0

    return SiftingResult(
        raw_key_length=raw_len,
        sifted_key_length=sifted_len,
        sifting_ratio=(sifted_len / raw_len) if raw_len > 0 else 0.0,
        alice_sifted=sifted_alice,
        bob_sifted=sifted_bob,
        matching_indices=indices,
        error_count=errors,
        qber=qber,
        security_threshold=security_threshold,
        is_secure=is_sec
    )
