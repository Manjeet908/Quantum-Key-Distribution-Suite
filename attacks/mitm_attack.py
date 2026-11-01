"""
Man-in-the-Middle (MitM) Attack Simulation and Classical Channel Authentication.
"""
from dataclasses import dataclass
from typing import List, Optional, Any, Tuple
import hmac
import hashlib
import json

class ClassicalAuthenticator:
    """
    Simulates classical public channel authentication (e.g. Wegman-Carter MACs / HMAC).
    Alice and Bob share an authentic pre-shared authentication secret.
    Eve possesses an unauthorized key, so any classical messages she modifies or
    proxies will fail authentication validation.
    """
    ALICE_BOB_SECRET = "ALICE_BOB_PRESHARED_AUTHENTICATION_KEY_V1"
    EVE_FORGED_SECRET = "EVE_ADVERSARIAL_KEY_UNAUTHORIZED"

    @staticmethod
    def sign_message(payload: str, secret: str = ALICE_BOB_SECRET) -> str:
        """Computes a 16-hex-character HMAC-SHA256 authentication tag."""
        return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:16]

    @staticmethod
    def verify_message(payload: str, tag: str, secret: str = ALICE_BOB_SECRET) -> bool:
        """Verifies if the received authentication tag matches the expected HMAC."""
        expected_tag = ClassicalAuthenticator.sign_message(payload, secret)
        return hmac.compare_digest(expected_tag, tag)


@dataclass
class MitmResult:
    """Encapsulates the full execution state of a Man-in-the-Middle attack."""
    protocol_name: str                 # "BB84", "B92", or "E91"
    num_qubits: int
    use_authentication: bool
    auth_passed: bool                  # False if MitM was caught via signature mismatch
    security_status: str               # "MITM_SUCCESSFUL (COMPROMISED)" or "MITM_DETECTED (ABORTED)"
    auth_message: str

    # Leg 1: Alice <-> Eve (Eve acts as Bob)
    alice_eve_result: Optional[Any]
    alice_key: List[int]
    alice_hex: str
    eve_alice_key: List[int]
    eve_alice_hex: str

    # Leg 2: Eve <-> Bob (Eve acts as Alice)
    eve_bob_result: Optional[Any]
    bob_key: List[int]
    bob_hex: str
    eve_bob_key: List[int]
    eve_bob_hex: str

    # Direct Alice vs Bob Key Comparison
    alice_bob_keys_match: bool
    key_agreement_rate: float          # Bit match rate between Alice and Bob keys
    mismatch_count: int
    comparison_length: int
    security_verdict: str

    # Classical Packet Inspection Data (Structured Basis Payloads & HMAC Verification)
    authentic_packet: Optional[dict] = None
    forged_packet: Optional[dict] = None
    authentic_payload_str: str = ""
    forged_payload_str: str = ""
    authentic_tag: str = ""
    forged_tag: str = ""
    expected_tag: str = ""


class MitmAttackSimulator:
    """
    Orchestrates the Man-in-the-Middle attack across BB84, B92, and E91 protocols.
    """

    @staticmethod
    def run(
        protocol_name: str,
        num_qubits: int = 24,
        use_authentication: bool = False,
        noise_level: float = 0.0,
        seed: Optional[int] = None
    ) -> MitmResult:
        """
        Executes the dual-leg QKD MitM simulation:
        1. Checks classical channel authentication. If active, detects Eve's tampering and aborts.
        2. Simulates Leg 1: Alice <-> Eve session (Alice believes she's pairing with Bob).
        3. Simulates Leg 2: Eve <-> Bob session (Bob believes he's pairing with Alice).
        4. Compares generated keys across Alice, Eve, and Bob.
        """
        clean_name = "BB84" if "BB84" in protocol_name else ("B92" if "B92" in protocol_name else "E91")

        # ------------------------------------------------------------------
        # Step 1: Execute Quantum Simulations on AerSimulator for Both Legs
        # Leg 1: Alice <-> Eve (Eve acts as Bob)
        # Leg 2: Eve <-> Bob (Eve acts as Alice)
        # ------------------------------------------------------------------
        seed_leg1 = seed
        seed_leg2 = (seed + 9999) if seed is not None else None

        if clean_name == "BB84":
            from core.bb84 import BB84Protocol
            runner1 = BB84Protocol(seed=seed_leg1)
            leg1_res = runner1.run(num_qubits=num_qubits, attack=None, noise_level=noise_level)

            runner2 = BB84Protocol(seed=seed_leg2)
            leg2_res = runner2.run(num_qubits=num_qubits, attack=None, noise_level=noise_level)

        elif clean_name == "B92":
            from core.b92 import B92Protocol
            runner1 = B92Protocol(seed=seed_leg1)
            leg1_res = runner1.run(num_qubits=num_qubits, attack=None, noise_level=noise_level)

            runner2 = B92Protocol(seed=seed_leg2)
            leg2_res = runner2.run(num_qubits=num_qubits, attack=None, noise_level=noise_level)

        else:  # E91
            from core.e91 import E91Protocol
            runner1 = E91Protocol(seed=seed_leg1)
            leg1_res = runner1.run(num_pairs=num_qubits, attack=None, noise_level=noise_level)

            runner2 = E91Protocol(seed=seed_leg2)
            leg2_res = runner2.run(num_pairs=num_qubits, attack=None, noise_level=noise_level)

        # ------------------------------------------------------------------
        # Step 2: Classical Channel Basis Announcement Packets & HMAC Verification
        # ------------------------------------------------------------------
        # In real QKD, the message sent over the classical public channel is the
        # actual array of chosen measurement/preparation bases.
        # Eve intercepts Alice's basis packet and substitutes it with her own
        # bases (so Bob measures/sifts against Eve's chosen bases).
        if clean_name == "BB84":
            authentic_packet = {
                "header": "QKD_CLASSICAL_BASIS_ANNOUNCEMENT",
                "protocol": "BB84",
                "sender": "Alice",
                "recipient": "Bob",
                "num_qubits": num_qubits,
                "declared_bases": leg1_res.alice_bases,
                "basis_encoding": {"0": "Z (|0⟩,|1⟩)", "1": "X (|+⟩,|-⟩)"}
            }
            forged_packet = {
                "header": "QKD_CLASSICAL_BASIS_ANNOUNCEMENT",
                "protocol": "BB84",
                "sender": "Alice (Intercepted & Proxied by Eve)",
                "recipient": "Bob",
                "num_qubits": num_qubits,
                "declared_bases": leg2_res.alice_bases,
                "basis_encoding": {"0": "Z (|0⟩,|1⟩)", "1": "X (|+⟩,|-⟩)"}
            }
        elif clean_name == "B92":
            conc_bob = [i for i, c in enumerate(leg2_res.bob_conclusive) if c]
            conc_eve = [i for i, c in enumerate(leg1_res.bob_conclusive) if c]
            authentic_packet = {
                "header": "QKD_CONCLUSIVE_DETECTION_ANNOUNCEMENT",
                "protocol": "B92",
                "sender": "Bob",
                "recipient": "Alice",
                "num_qubits": num_qubits,
                "conclusive_indices": conc_bob,
                "num_conclusive": len(conc_bob)
            }
            forged_packet = {
                "header": "QKD_CONCLUSIVE_DETECTION_ANNOUNCEMENT",
                "protocol": "B92",
                "sender": "Bob (Intercepted & Proxied by Eve)",
                "recipient": "Alice",
                "num_qubits": num_qubits,
                "conclusive_indices": conc_eve,
                "num_conclusive": len(conc_eve)
            }
        else:  # E91
            authentic_packet = {
                "header": "QKD_ANALYZER_ORIENTATION_ANNOUNCEMENT",
                "protocol": "E91",
                "sender": "Alice",
                "recipient": "Bob",
                "num_pairs": num_qubits,
                "analyzer_angles": leg1_res.alice_bases,
                "angle_encoding": {"0": "a1 (0°)", "1": "a2 (45°)", "2": "a3 (90°)"}
            }
            forged_packet = {
                "header": "QKD_ANALYZER_ORIENTATION_ANNOUNCEMENT",
                "protocol": "E91",
                "sender": "Alice (Intercepted & Proxied by Eve)",
                "recipient": "Bob",
                "num_pairs": num_qubits,
                "analyzer_angles": leg2_res.alice_bases,
                "angle_encoding": {"0": "a1 (0°)", "1": "a2 (45°)", "2": "a3 (90°)"}
            }

        # Serialized JSON representations with compact arrays and proper Unicode
        import re
        def _format_packet_json(data):
            raw = json.dumps(data, indent=2, ensure_ascii=False)
            return re.sub(
                r'\[([\s\d,]+)\]',
                lambda m: '[' + ', '.join([x.strip() for x in m.group(1).replace('\n', ' ').split(',') if x.strip()]) + ']',
                raw
            )

        authentic_payload_str = _format_packet_json(authentic_packet)
        forged_payload_str = _format_packet_json(forged_packet)

        # Canonical strings for cryptographic hashing (compact, sorted keys)
        auth_signing_str = json.dumps(authentic_packet, sort_keys=True)
        forged_signing_str = json.dumps(forged_packet, sort_keys=True)

        # Compute HMAC-SHA256 authentication tags
        authentic_tag = ClassicalAuthenticator.sign_message(
            auth_signing_str, ClassicalAuthenticator.ALICE_BOB_SECRET
        )
        forged_tag = ClassicalAuthenticator.sign_message(
            forged_signing_str, ClassicalAuthenticator.EVE_FORGED_SECRET
        )
        expected_tag = ClassicalAuthenticator.sign_message(
            forged_signing_str, ClassicalAuthenticator.ALICE_BOB_SECRET
        )

        if use_authentication:
            # Verification: Bob verifies the incoming forged packet against ALICE_BOB_SECRET
            auth_passed = ClassicalAuthenticator.verify_message(
                forged_signing_str,
                forged_tag,
                ClassicalAuthenticator.ALICE_BOB_SECRET
            )
            # auth_passed is False! (forged_tag != expected_tag)

            from postprocessing.sifting import SiftingResult
            from postprocessing.privacy_amp import DistillationResult
            abort_msg = "ABORTED: Classical channel authentication signature mismatch! Eve tampering detected."

            # Sifting is prevented/aborted: without authenticated basis exchange,
            # neither Alice, Bob, nor Eve can determine matching bases or distill sifted keys.
            aborted_sifting_leg1 = SiftingResult(
                raw_key_length=leg1_res.sifting_result.raw_key_length,
                sifted_key_length=0,
                sifting_ratio=0.0,
                alice_sifted=[],
                bob_sifted=[],
                matching_indices=[],
                error_count=0,
                qber=0.0,
                security_threshold=leg1_res.sifting_result.security_threshold,
                is_secure=False
            )
            leg1_res.sifting_result = aborted_sifting_leg1

            leg1_res.distillation_result = DistillationResult(
                raw_sifted_length=0,
                corrected_key=[],
                final_secret_key=[],
                final_hex_key="",
                compression_ratio=0.0,
                is_aborted=True,
                status_message=abort_msg
            )
            leg1_res.security_status = "COMPROMISED"

            aborted_sifting_leg2 = SiftingResult(
                raw_key_length=leg2_res.sifting_result.raw_key_length,
                sifted_key_length=0,
                sifting_ratio=0.0,
                alice_sifted=[],
                bob_sifted=[],
                matching_indices=[],
                error_count=0,
                qber=0.0,
                security_threshold=leg2_res.sifting_result.security_threshold,
                is_secure=False
            )
            leg2_res.sifting_result = aborted_sifting_leg2

            leg2_res.distillation_result = DistillationResult(
                raw_sifted_length=0,
                corrected_key=[],
                final_secret_key=[],
                final_hex_key="",
                compression_ratio=0.0,
                is_aborted=True,
                status_message=abort_msg
            )
            leg2_res.security_status = "COMPROMISED"

            auth_message = (
                "🚨 Classical Message Authentication Failed! "
                "HMAC signature mismatch detected during public sifting announcement. "
                "Eve intercepted or modified classical messages. Basis reconciliation blocked and key generation immediately ABORTED."
            )
            security_status = "MITM_DETECTED (ABORTED)"
            security_verdict = (
                f"🛡️ **MITM ATTACK THWARTED ({clean_name}):** Classical channel authentication was active. "
                "When Eve attempted to intercept and proxy the classical sifting announcements, "
                "cryptographic signature verification failed. Alice and Bob rejected the unauthenticated basis announcements at Stage 3, "
                "blocking basis reconciliation and releasing 0 sifted or secret bits to Eve."
            )

            alice_key = []
            alice_hex = ""
            eve_alice_key = []
            eve_alice_hex = ""
            bob_key = []
            bob_hex = ""
            eve_bob_key = []
            eve_bob_hex = ""
            keys_match = False
            agreement_rate = 0.0
            mismatches = 0
            comp_len = 0
        else:
            auth_passed = True
            # Extract Keys:
            # Leg 1: Alice distills key with Eve. Alice has K_AE, Eve has K_AE.
            alice_key = list(leg1_res.distillation_result.final_secret_key)
            alice_hex = leg1_res.distillation_result.final_hex_key
            eve_alice_key = list(alice_key)  # Eve holds the matching Leg 1 key
            eve_alice_hex = alice_hex

            # Leg 2: Eve distills key with Bob. Bob has K_EB, Eve has K_EB.
            bob_key = list(leg2_res.distillation_result.final_secret_key)
            bob_hex = leg2_res.distillation_result.final_hex_key
            eve_bob_key = list(bob_key)      # Eve holds the matching Leg 2 key
            eve_bob_hex = bob_hex

            # Key Agreement Analysis Between Alice and Bob
            comp_len = min(len(alice_key), len(bob_key))
            if comp_len > 0:
                mismatches = sum(1 for i in range(comp_len) if alice_key[i] != bob_key[i])
                matches = comp_len - mismatches
                agreement_rate = matches / comp_len
                keys_match = (mismatches == 0 and len(alice_key) == len(bob_key))
            else:
                mismatches = 0
                agreement_rate = 0.0
                keys_match = False

            auth_message = (
                "⚠️ Classical channel is unauthenticated! Eve actively intercepted and proxied "
                "all classical basis announcements without detection."
            )
            security_status = "MITM_SUCCESSFUL (COMPROMISED)"
            security_verdict = (
                f"🚨 **MITM ATTACK SUCCESSFUL ({clean_name}):** Eve successfully bifurcated the channel into two sessions. "
                f"Alice holds key $K_{{AE}}$ ({len(alice_key)} bits) and Bob holds key $K_{{EB}}$ ({len(bob_key)} bits). "
                f"Neither party observed abnormal QBER or Bell inequality violation. "
                f"**Eve possesses both keys in full.** Alice and Bob share **no matching secret key** "
                f"(Key bit agreement: {agreement_rate * 100:.1f}%)."
            )

        return MitmResult(
            protocol_name=clean_name,
            num_qubits=num_qubits,
            use_authentication=use_authentication,
            auth_passed=auth_passed,
            security_status=security_status,
            auth_message=auth_message,
            alice_eve_result=leg1_res,
            alice_key=alice_key,
            alice_hex=alice_hex,
            eve_alice_key=eve_alice_key,
            eve_alice_hex=eve_alice_hex,
            eve_bob_result=leg2_res,
            bob_key=bob_key,
            bob_hex=bob_hex,
            eve_bob_key=eve_bob_key,
            eve_bob_hex=eve_bob_hex,
            alice_bob_keys_match=keys_match,
            key_agreement_rate=agreement_rate,
            mismatch_count=mismatches,
            comparison_length=comp_len,
            security_verdict=security_verdict,
            authentic_packet=authentic_packet,
            forged_packet=forged_packet,
            authentic_payload_str=authentic_payload_str,
            forged_payload_str=forged_payload_str,
            authentic_tag=authentic_tag,
            forged_tag=forged_tag,
            expected_tag=expected_tag
        )
