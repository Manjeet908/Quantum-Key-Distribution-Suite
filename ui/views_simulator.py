"""
View: Interactive Single Protocol Simulator for BB84, B92, and E91.
"""
import streamlit as st
import pandas as pd
import numpy as np

from core.bb84 import BB84Protocol
from core.b92 import B92Protocol
from core.e91 import E91Protocol
from attacks.intercept_resend import InterceptResendAttack
from attacks.mitm_attack import MitmAttackSimulator, MitmResult
from ui.circuit_renderer import draw_quantum_circuit
from ui.styles import render_badge, clean_html

def render_simulator_view():
    st.markdown("### 🔬 Interactive Quantum Key Distribution Laboratory")
    st.markdown(
        "Configure quantum parameters, simulate channel conditions and adversarial attacks, "
        "and observe step-by-step state collapse, sifting reconciliation, and key distillation."
    )

    # Top Control Bar
    col_proto, col_attack, col_qubits = st.columns([1.2, 1.2, 1.0])
    
    with col_proto:
        protocol_choice = st.selectbox(
            "Protocol Architecture",
            ["BB84 (4-State)", "B92 (2-State Non-Orthogonal)", "E91 (EPR Bell Entanglement)"]
        )

    with col_attack:
        attack_choice = st.selectbox(
            "Channel Eavesdropping / Threat Model",
            [
                "None (Ideal Secure Channel)",
                "Intercept-Resend Attack (Quantum Channel)",
                "Man-in-the-Middle (MitM) Attack (Dual-Channel)"
            ]
        )

    with col_qubits:
        qubit_count = st.slider(
            "Qubit / Pair Count",
            min_value=12, max_value=120, value=24, step=4,
            help="Higher count (e.g. 60-100) provides tighter statistical convergence for CHSH Bell tests."
        )

    # Attack & Noise Configuration
    col_noise, col_param = st.columns(2)
    with col_noise:
        noise_level = st.slider(
            "Channel Depolarizing Noise (ε)",
            min_value=0.0, max_value=0.30, value=0.0, step=0.02,
            help="Simulates environmental fiber decoherence and detector dark counts."
        )

    use_classical_auth = False
    with col_param:
        if "Intercept-Resend" in attack_choice:
            eve_intensity = st.slider(
                "Eve Interception Rate",
                min_value=0.1, max_value=1.0, value=1.0, step=0.1,
                help="Fraction of flying qubits intercepted and measured by Eve in transit."
            )
        elif "Man-in-the-Middle" in attack_choice:
            use_classical_auth = st.toggle(
                "🛡️ Enable Classical Authentication (Signed Channel)",
                value=False,
                help="When enabled, classical sifting announcements require valid HMAC-SHA256 signatures. Eve's forged classical messages fail validation, thwarting the MitM attack."
            )
            if use_classical_auth:
                st.caption("🔒 **Authenticated Mode Active:** Alice & Bob verify HMAC signatures. Eve cannot proxy announcements.")
            else:
                st.caption("⚠️ **Unauthenticated Channel:** Classical channel is unsigned. Eve can freely intercept and proxy announcements.")
        else:
            st.info("💡 Secure channel configured. No adversary injected.")

    # Execution Trigger
    run_btn = st.button("🚀 Execute Quantum Simulation", type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("Preparing states and executing quantum circuit on AerSimulator..."):
            if "Man-in-the-Middle" in attack_choice:
                mitm_res = MitmAttackSimulator.run(
                    protocol_name=protocol_choice,
                    num_qubits=qubit_count,
                    use_authentication=use_classical_auth,
                    noise_level=noise_level
                )
                res = None
            else:
                mitm_res = None
                attack_obj = None
                if "Intercept-Resend" in attack_choice:
                    attack_obj = InterceptResendAttack(intercept_prob=eve_intensity)

                # Run selected protocol simulation
                if "BB84" in protocol_choice:
                    runner = BB84Protocol()
                    res = runner.run(num_qubits=qubit_count, attack=attack_obj, noise_level=noise_level)
                elif "B92" in protocol_choice:
                    runner = B92Protocol()
                    res = runner.run(num_qubits=qubit_count, attack=attack_obj, noise_level=noise_level)
                elif "E91" in protocol_choice:
                    runner = E91Protocol()
                    res = runner.run(num_pairs=qubit_count, attack=attack_obj, noise_level=noise_level)
                else:
                    res = None

        # Render results OUTSIDE the spinner block
        if mitm_res is not None:
            render_mitm_results(mitm_res)
        elif res is not None:
            if "BB84" in protocol_choice:
                render_bb84_results(res)
            elif "B92" in protocol_choice:
                render_b92_results(res)
            elif "E91" in protocol_choice:
                render_e91_results(res)



def render_key_formation_pipeline(
    protocol_name: str,
    res,
    sender_name: str = "Alice",
    receiver_name: str = "Bob",
    key_prefix: str = "",
    auth_failed: bool = False
):
    """
    Renders the sequential 5-stage key formation and distillation pipeline,
    highlighting the path from quantum state preparation through sifting,
    threshold decision gates, to final secret key generation or rejection.
    Supports customization for standard runs and MitM legs.
    """
    st.markdown("##### 🔑 Key Formation & Distillation Pipeline")
    with st.expander("🔄 View Step-by-Step Sequence of Key Formation (Stages 1–5)", expanded=True):
        # STAGE 1: Quantum State Preparation
        st.markdown("###### **Stage 1: Quantum State Preparation**")
        col_s1_desc, col_s1_data = st.columns([1.5, 1.0])
        with col_s1_desc:
            if protocol_name == "BB84":
                st.write(
                    f"- **{sender_name}** generates **{res.num_qubits} random bits** (0 or 1) and selects **random encoding bases** "
                    "(Z-rectilinear {|0⟩, |1⟩} or X-diagonal {|+⟩, |−⟩})."
                )
                st.write(f"- Prepares single photons in corresponding quantum superpositions for transmission to {receiver_name}.")
            elif protocol_name == "B92":
                st.write(
                    f"- **{sender_name}** encodes **{res.num_qubits} random bits** into **two non-orthogonal states**: "
                    "Bit 0 → |0⟩ (Rectilinear), Bit 1 → |+⟩ (Diagonal)."
                )
                st.write("- Non-orthogonality overlap forbids perfect eavesdropping cloning without disturbance.")
            elif protocol_name == "E91":
                st.write(
                    f"- Entangled photon source generates **{res.num_pairs} EPR Bell pairs**: "
                    r"$|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}$."
                )
                st.write(
                    f"- Dual-arm optical distribution: Photon A is routed to **{sender_name}**, Photon B is routed to **{receiver_name}**."
                )
        with col_s1_data:
            if protocol_name in ["BB84", "B92"]:
                raw_preview = "".join(str(b) for b in res.alice_bits[:24])
                if len(res.alice_bits) > 24:
                    raw_preview += "..."
                st.text_input(f"{sender_name} Raw Prepared Bits", value=raw_preview, disabled=True, key=f"{key_prefix}{protocol_name}_s1_raw")
            else:
                st.info(f"✨ **{res.num_pairs} Bell Pairs** prepared with maximal entanglement (ideal $|S| = 2.828$).")

        st.markdown("---")

        # STAGE 2: Quantum Channel Transmission & Adversarial Interaction
        st.markdown("###### **Stage 2: Channel Transmission & Noise / Adversarial Interaction**")
        col_s2_left, col_s2_right = st.columns(2)
        with col_s2_left:
            st.write(f"- **Physical Depolarizing Noise Rate (ε):** `{res.noise_level * 100:.1f}%`")
            st.caption(f"Simulates environmental fiber birefringence, dark counts, and decoherence between {sender_name} and {receiver_name}.")
        with col_s2_right:
            if sender_name == "Eve" or receiver_name == "Eve":
                st.warning(f"👿 **MitM Active on Link:** Eve is acting as **{receiver_name if receiver_name == 'Eve' else sender_name}**, terminating/generating quantum states.")
            elif res.intercept_result and res.intercept_result.qubits_intercepted_count > 0:
                count = res.intercept_result.qubits_intercepted_count
                total = res.num_qubits if hasattr(res, 'num_qubits') else res.num_pairs
                rate = res.intercept_result.interception_rate * 100
                st.warning(f"👿 **Eve Active:** Intercepted **{count} of {total}** flying photons ({rate:.1f}%). Quantum state collapsed!")
            else:
                st.success(f"🛡️ **Channel Integrity:** Quantum transmission complete from {sender_name} to {receiver_name}.")

        st.markdown("---")

        # STAGE 3: Measurement & Classical Sifting (Reconciliation / Partitioning)
        st.markdown("###### **Stage 3: Measurement & Classical Sifting (Reconciliation)**")
        col_s3_desc, col_s3_data = st.columns([1.5, 1.0])
        with col_s3_desc:
            if auth_failed:
                st.error(
                    f"⛔ **Basis Reconciliation Blocked (Authentication Failure):**\n"
                    f"- During public sifting, classical basis announcements required a valid HMAC-SHA256 signature signed with `ALICE_BOB_SECRET`.\n"
                    f"- Eve attempted to proxy/forge classical messages using `EVE_FORGED_SECRET`, causing verification to **FAIL**.\n"
                    f"- **Basis announcements were rejected:** Neither party confirmed matching bases.\n"
                    f"- **0 bits were sifted** — Eve cannot determine which measurement bases matched."
                )
            elif protocol_name == "BB84":
                st.write(
                    f"- **{receiver_name}** measures in independent random bases ($Z$ or $X$). "
                    f"**{sender_name}** and **{receiver_name}** announce bases over the classical channel."
                )
                st.write(
                    f"- **Basis Sifting:** Mismatched bases are discarded. "
                    f"**{res.sifting_result.sifted_key_length} of {res.num_qubits} bits retained** "
                    f"({res.sifting_result.sifting_ratio*100:.1f}% yield; ~50% expected)."
                )
            elif protocol_name == "B92":
                st.write(
                    f"- **{receiver_name}** performs Unambiguous State Discrimination (USD): Basis 0 tests orthogonal to $|0\\rangle$, "
                    "Basis 1 tests orthogonal to $|+\\rangle$."
                )
                st.write(
                    f"- **Conclusive Sifting:** {receiver_name} announces positions where outcome = 1 (**{res.sifting_result.sifted_key_length} bits**, "
                    f"{res.sifting_result.sifting_ratio*100:.1f}% yield). Inconclusive zeros ({res.num_qubits - res.sifting_result.sifted_key_length} bits) discarded."
                )
            elif protocol_name == "E91":
                st.write(
                    f"- **{sender_name}** measures at angles {{0°, 45°, 90°}}; **{receiver_name}** measures at angles {{22.5°, 45°, 67.5°}}. "
                    "They publish their chosen angle indices."
                )
                st.write(
                    f"- **Entanglement Partitioning:**\n"
                    f"  - **🔑 Key Generation Pool (a2 = b2 = 45°):** **{res.sifting_result.sifted_key_length} pairs** "
                    f"({res.sifting_result.sifting_ratio*100:.1f}% yield) where identical measurement outcomes are guaranteed by Bell correlation.\n"
                    f"  - **🔔 CHSH Bell Test Pool:** Remaining **{res.num_pairs - res.sifting_result.sifted_key_length} pairs** "
                    "allocated to verify quantum non-locality (S parameter)."
                )
        with col_s3_data:
            if auth_failed:
                st.text_input(f"{sender_name} Sifted Key Bits", value="(Blocked - Classical Auth Failed)", disabled=True, key=f"{key_prefix}{protocol_name}_s3_a")
                st.text_input(f"{receiver_name} Sifted Key Bits", value="(Blocked - Classical Auth Failed)", disabled=True, key=f"{key_prefix}{protocol_name}_s3_b")
                st.caption("🔒 No basis reconciliation permitted without authentic HMAC signature.")
            else:
                sift_a = "".join(str(b) for b in res.sifting_result.alice_sifted[:24])
                sift_b = "".join(str(b) for b in res.sifting_result.bob_sifted[:24])
                if len(res.sifting_result.alice_sifted) > 24:
                    sift_a += "..."
                    sift_b += "..."
                st.text_input(f"{sender_name} Sifted Key Bits", value=sift_a if sift_a else "(None)", disabled=True, key=f"{key_prefix}{protocol_name}_s3_a")
                st.text_input(f"{receiver_name} Sifted Key Bits", value=sift_b if sift_b else "(None)", disabled=True, key=f"{key_prefix}{protocol_name}_s3_b")

        st.markdown("---")

        # STAGE 4: Error Estimation & Security Gate (Accept vs Reject Decision)
        st.markdown("###### **Stage 4: Error Estimation & Security Gate (Accept / Abort)**")
        qber = res.sifting_result.qber
        thresh = res.sifting_result.security_threshold
        is_aborted = res.distillation_result.is_aborted or auth_failed

        if auth_failed:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.metric("Check 4A: Classical Channel Authentication", "FAILED", "Signature Mismatch", delta_color="inverse")
                st.caption(f"{receiver_name} verified basis announcements using authentic pre-shared secret. Verification failed!")
            with col_g2:
                st.metric("Check 4B: Session Abort Decision", "ABORTED", "0 Sifted Bits Released", delta_color="inverse")
                st.caption("Active adversarial proxy detected on classical link. Key distillation terminated.")

            st.error(
                f"🚨 **CLASSICAL AUTHENTICATION GATE FAILED (SESSION ABORTED):** "
                f"Classical HMAC signature check failed for {receiver_name}! "
                f"Eve does not possess the authentic pre-shared secret key, so her intercepted and proxied basis announcements "
                f"were detected and rejected. Basis reconciliation was blocked and 0 sifted or secret bits were released to Eve."
            )
        elif protocol_name == "E91":
            s_val = res.chsh_result.s_value
            is_bell_ok = res.chsh_result.is_violated
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.metric("Check 4A: CHSH Bell Parameter |S|", f"{s_val:.3f}", "Required: > 2.000", delta_color="normal" if is_bell_ok else "inverse")
                st.caption("Verifies entanglement non-locality. Values ≤ 2.0 prove local realism or eavesdropping.")
            with col_g2:
                st.metric("Check 4B: Key Pair QBER", f"{qber*100:.1f}%", f"Limit: {thresh*100:.1f}%", delta_color="normal" if qber <= thresh else "inverse")
                st.caption(f"Error count: {res.sifting_result.error_count} bit mismatches across {res.sifting_result.sifted_key_length} key pairs.")

            if not is_aborted:
                st.success(
                    f"✅ **DUAL SECURITY GATE PASSED:** Both Bell test (|S| = {s_val:.3f} > 2.0) and Key QBER ({qber*100:.1f}% ≤ {thresh*100:.1f}%) "
                    f"are satisfied! Channel entanglement intact between {sender_name} and {receiver_name}. Proceeding to Key Distillation."
                )
            else:
                reason = []
                if not is_bell_ok:
                    reason.append(f"Bell inequality broken (|S| = {s_val:.3f} ≤ 2.0)")
                if qber > thresh:
                    reason.append(f"Key QBER ({qber*100:.1f}%) > threshold ({thresh*100:.1f}%)")
                st.error(
                    f"🚨 **SECURITY GATE FAILED (SESSION ABORTED):** {', '.join(reason)}. "
                    f"All sifted bits are immediately purged to prevent key leakage."
                )
        else:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.metric("QBER Threshold Bound", f"{thresh*100:.1f}%", "Protocol Security Cutoff")
            with col_g2:
                st.metric("Measured Channel QBER", f"{qber*100:.1f}%", f"{res.sifting_result.error_count} error bits", delta_color="normal" if qber <= thresh else "inverse")

            if not is_aborted:
                st.success(
                    f"✅ **SECURITY GATE PASSED:** Measured QBER ({qber*100:.1f}%) ≤ Safety Limit ({thresh*100:.1f}%). "
                    f"Errors are within information-theoretic correction capacity. Key candidate accepted for distillation."
                )
            else:
                st.error(
                    f"🚨 **SECURITY GATE FAILED (SESSION ABORTED):** Measured QBER ({qber*100:.1f}%) exceeds safety limit ({thresh*100:.1f}%)! "
                    f"All {res.sifting_result.sifted_key_length} sifted bits are destroyed to guarantee 0% key leakage."
                )

        st.markdown("---")

        # STAGE 5: Information Reconciliation & Privacy Amplification
        st.markdown("###### **Stage 5: Information Reconciliation & Final Privacy Amplification**")
        if is_aborted:
            st.error(
                f"🛑 **KEY FORMATION TERMINATED:** No secret key was distilled between {sender_name} and {receiver_name}. "
                f"Sifted bits purged: `{res.sifting_result.sifted_key_length} bits`. "
                f"Secret bits released: `0 bits`. Secrecy leak guarantee: `0.0%`."
            )
        else:
            final_bits = res.distillation_result.final_secret_key
            final_hex = res.distillation_result.final_hex_key
            comp_ratio = res.distillation_result.compression_ratio * 100

            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.metric("1. Error Reconciliation", f"{len(res.distillation_result.corrected_key)} bits", "Parity Harmonized")
            with col_p2:
                st.metric("2. Privacy Amplification", f"{len(final_bits)} bits", f"{comp_ratio:.0f}% compression yield")
            with col_p3:
                st.metric("3. Final Security Verdict", "Key Established", f"{sender_name} ↔ {receiver_name}")

            if protocol_name == "E91":
                pa_desc = "Employs device-independent universal hash compression ($r = 1 - 2h(QBER) - I_{Eve}(S)$) where potential leakage is bounded directly by the observed Bell parameter |S|."
            else:
                pa_desc = "Employs universal hash compression ($r = 1 - 2h(QBER)$) based strictly on observable QBER (Shor-Preskill / Devetak-Winter bound)."

            st.write(
                f"- **Error Reconciliation:** {sender_name} and {receiver_name} reconcile any remaining bit discrepancies via parity exchange. "
                f"Harmonized string length: **{len(res.distillation_result.corrected_key)} bits**.\n"
                f"- **Privacy Amplification:** {pa_desc}\n"
                f"- **Final Secret Key Distilled:** **{len(final_bits)} bits** (ready for One-Time Pad / AES encryption)."
            )

            col_k1, col_k2 = st.columns(2)
            with col_k1:
                st.markdown("**Binary Key String:**")
                st.code("".join(str(b) for b in final_bits), language="text")
            with col_k2:
                st.markdown("**Hexadecimal Key:**")
                st.code(f"0x{final_hex}", language="text")


def render_bb84_results(res):
    """Renders BB84 execution cards and data tables."""
    st.markdown("---")
    st.markdown(f"#### 📊 BB84 Execution Overview {render_badge(res.security_status)}", unsafe_allow_html=True)

    # Metric Row
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Qubits Sent", res.num_qubits)
    m2.metric("Sifted Key Length", f"{res.sifting_result.sifted_key_length} bits", f"{res.sifting_result.sifting_ratio*100:.1f}% yield")
    m3.metric("Error Count", f"{res.sifting_result.error_count} bits")
    
    delta_color = "normal" if res.sifting_result.qber <= 0.11 else "inverse"
    m4.metric("QBER", f"{res.sifting_result.qber*100:.1f}%", f"Limit: {res.sifting_result.security_threshold*100:.1f}%", delta_color=delta_color)
    m5.metric("Final Secret Key", f"{len(res.distillation_result.final_secret_key)} bits", f"{res.distillation_result.compression_ratio*100:.0f}% distilled")

    # Security Alert Box
    if res.security_status == "COMPROMISED":
        st.error(
            f"🚨 **SESSION ABORTED:** QBER ({res.sifting_result.qber*100:.1f}%) exceeds the 11.0% Shannon security limit! "
            f"Adversary detection triggered. Sifted bits discarded to prevent key leakage."
        )
    elif res.security_status == "WARNING":
        st.warning("⚠️ **ELEVATED NOISE:** QBER is elevated. Privacy amplification required higher compression.")
    else:
        st.success(f"🎉 **SECURE SECRET KEY ESTABLISHED:** Distilled key hex: `{res.distillation_result.final_hex_key}`")

    # Step-by-Step Key Formation Pipeline
    render_key_formation_pipeline("BB84", res)

    # Detailed Step-by-Step Transmission Table
    with st.expander("🔍 Step-by-Step Bit & Measurement Transmission Log", expanded=False):
        basis_names = {0: "Z (|0⟩,|1⟩)", 1: "X (|+⟩,|-⟩)"}
        eve_bases = res.intercept_result.eve_bases if res.intercept_result else [None]*res.num_qubits
        eve_bits = res.intercept_result.eve_bits if res.intercept_result else [None]*res.num_qubits

        df_data = []
        for i in range(res.num_qubits):
            matched = (i in res.sifting_result.matching_indices)
            is_err = matched and (res.alice_bits[i] != res.bob_measured_bits[i])
            df_data.append({
                "Alice Bit": res.alice_bits[i],
                "Alice Basis": basis_names[res.alice_bases[i]],
                "Eve Intercepted?": "👿 YES" if (res.intercept_result and res.intercept_result.intercepted[i]) else "—",
                "Eve Basis": basis_names.get(eve_bases[i], "—") if (res.intercept_result and res.intercept_result.intercepted[i]) else "—",
                "Bob Basis": basis_names[res.bob_bases[i]],
                "Bob Measured": res.bob_measured_bits[i],
                "Bases Match?": "✅ Sifted" if matched else "❌ Discard",
                "Error Status": "🚨 ERROR" if is_err else ("✅ OK" if matched else "—")
            })
        st.dataframe(pd.DataFrame(df_data), use_container_width=True, height=280)

    # Circuit Diagram
    with st.expander("⚡ Quantum Circuit Visualization (Qiskit MPL)", expanded=False):
        st.caption("Displays the quantum register, Alice's preparation, channel barriers, and Bob's measurements.")
        fig = draw_quantum_circuit(res.circuit, max_qubits_to_draw=res.num_qubits)
        st.pyplot(fig)


def render_b92_results(res):
    """Renders B92 execution cards and data tables."""
    st.markdown("---")
    st.markdown(f"#### 📊 B92 Execution Overview {render_badge(res.security_status)}", unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Qubits Sent", res.num_qubits)
    m2.metric("Conclusive Detections", f"{res.sifting_result.sifted_key_length} bits", f"{res.sifting_result.sifting_ratio*100:.1f}% yield")
    m3.metric("Inconclusive Discards", f"{res.num_qubits - res.sifting_result.sifted_key_length} bits")
    
    delta_color = "normal" if res.sifting_result.qber <= 0.048 else "inverse"
    m4.metric("QBER", f"{res.sifting_result.qber*100:.1f}%", f"Limit: 4.8%", delta_color=delta_color)
    m5.metric("Final Secret Key", f"{len(res.distillation_result.final_secret_key)} bits")

    if res.security_status == "COMPROMISED":
        st.error(
            f"🚨 **SESSION ABORTED:** B92 QBER ({res.sifting_result.qber*100:.1f}%) exceeds the 4.8% cutoff! "
            f"B92 is highly sensitive to noise and eavesdropping."
        )
    else:
        st.success(f"🎉 **SECURE B92 KEY ESTABLISHED:** Distilled key hex: `{res.distillation_result.final_hex_key}`")

    # Step-by-Step Key Formation Pipeline
    render_key_formation_pipeline("B92", res)

    with st.expander("🔍 B92 Conclusive vs Inconclusive Measurement Log", expanded=False):
        b92_basis_desc = {0: "Basis 0 (Test |1⟩)", 1: "Basis 1 (Test |−⟩)"}
        eve_bases = res.intercept_result.eve_bases if res.intercept_result else [None]*res.num_qubits
        eve_bits = res.intercept_result.eve_bits if res.intercept_result else [None]*res.num_qubits

        df_data = []
        for i in range(res.num_qubits):
            is_conc = res.bob_conclusive[i]
            inferred = res.bob_inferred_bits[i]
            is_err = is_conc and (res.alice_bits[i] != inferred)
            row = {
                "Qubit #": i,
                "Alice Bit": res.alice_bits[i],
                "Alice State": res.alice_states[i],
            }
            if res.intercept_result:
                was_int = res.intercept_result.intercepted[i]
                row["Eve Intercepted?"] = "👿 YES" if was_int else "—"
                row["Eve Basis"] = ("Z" if eve_bases[i] == 0 else "X") if was_int else "—"
                row["Eve Measured"] = eve_bits[i] if (was_int and eve_bits[i] is not None) else "—"
            row.update({
                "Bob Test Operator": b92_basis_desc[res.bob_bases[i]],
                "Bob Measurement": res.bob_raw_measurements[i],
                "Detection Result": "✅ CONCLUSIVE" if is_conc else "⚪ Inconclusive",
                "Bob Inferred Bit": inferred if is_conc else "—",
                "Match Status": "🚨 ERROR" if is_err else ("✅ Match" if is_conc else "—")
            })
            df_data.append(row)
        st.dataframe(pd.DataFrame(df_data), use_container_width=True, height=280)

    with st.expander("⚡ Quantum Circuit Visualization (Qiskit MPL)", expanded=False):
        fig = draw_quantum_circuit(res.circuit, res.num_qubits)
        st.pyplot(fig)


def render_e91_results(res):
    """Renders E91 execution cards and data tables."""
    st.markdown("---")
    st.markdown(f"#### 📊 E91 Entanglement Execution Overview {render_badge(res.security_status)}", unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("EPR Pairs Generated", res.num_pairs)
    m2.metric("Key Generation Pairs", f"{res.sifting_result.sifted_key_length} pairs")
    
    chsh_color = "normal" if res.chsh_result.is_violated else "inverse"
    m3.metric("CHSH Bell Parameter |S|", f"{res.chsh_result.s_value:.3f}", "Bound: > 2.0", delta_color=chsh_color)
    m4.metric("QBER on Key Pairs", f"{res.sifting_result.qber*100:.1f}%")
    m5.metric("Final Secret Key", f"{len(res.distillation_result.final_secret_key)} bits")

    # Security Alert Box for E91
    if res.security_status == "COMPROMISED":
        st.error(
            f"🚨 **SESSION ABORTED:** E91 security checks failed! "
            f"Bell parameter |S| = {res.chsh_result.s_value:.3f} (Bound: > 2.000) or QBER = {res.sifting_result.qber*100:.1f}% (Limit: 11.0%). "
            f"Adversary detection triggered or entanglement broken. Sifted bits discarded to prevent key leakage."
        )
    elif res.security_status == "WARNING":
        st.warning(
            f"⚠️ **ELEVATED NOISE / CAUTION:** Bell parameter |S| = {res.chsh_result.s_value:.3f} is close to classical threshold (2.0). "
            f"Privacy amplification required higher compression ratio."
        )
    else:
        st.success(
            f"🎉 **SECURE E91 SECRET KEY ESTABLISHED:** Distilled key hex: `{res.distillation_result.final_hex_key}` "
            f"({len(res.distillation_result.final_secret_key)} bits, CHSH |S| = {res.chsh_result.s_value:.3f})"
        )

    st.info(res.chsh_result.security_verdict)

    if res.intercept_result:
        st.warning(
            f"👿 **Adversary Interception:** Eve intercepted {res.intercept_result.qubits_intercepted_count} of {res.num_pairs} transiting photons ({res.intercept_result.interception_rate*100:.1f}%), "
            f"collapsing entanglement and breaking Bell inequality violation!"
        )

    if res.num_pairs < 48:
        st.caption("💡 *Tip: CHSH Bell evaluation tests 4 correlation terms over 9 random basis combinations. For high statistical certainty (|S| > 2.0 with minimal variance), increase pair count to ≥ 60–100.*")

    # Step-by-Step Key Formation Pipeline for E91
    render_key_formation_pipeline("E91", res)

    # 1. CHSH Correlation Terms & Key Basis Alignment Expander (Preserved)
    with st.expander("🔍 CHSH Correlation Terms & Key Basis Alignment", expanded=False):
        col_chsh, col_table = st.columns([1, 1.4])
        with col_chsh:
            st.markdown("**CHSH 4-Correlation Components:**")
            for term, val in res.chsh_result.correlation_terms.items():
                st.write(f"- `{term}`: **{val:+.3f}** (samples: {res.chsh_result.sample_counts.get(term, 0)})")
            st.markdown(f"**Calculated |S|:** `{res.chsh_result.s_value:.4f}`")
            st.caption("Classical limit ≤ 2.0. Quantum maximum (Cirel'son bound) = 2.8284.")
        
        with col_table:
            st.markdown("**Aligned Key Generation Samples:**")
            df_e91 = pd.DataFrame({
                "Pair #": res.sifting_result.matching_indices,
                "Alice Measured": res.sifting_result.alice_sifted,
                "Bob Measured": res.sifting_result.bob_sifted,
                "Match?": ["✅" if a == b else "❌" for a, b in zip(res.sifting_result.alice_sifted, res.sifting_result.bob_sifted)]
            })
            st.dataframe(df_e91, use_container_width=True, height=200)

    # 2. Complete Step-by-Step Entangled Pair & Measurement Transmission Log for E91
    with st.expander("🔍 Complete Step-by-Step Entangled Pair Transmission Log", expanded=False):
        alice_angle_names = {0: "a1 (0°)", 1: "a2 (45°)", 2: "a3 (90°)"}
        bob_angle_names = {0: "b1 (22.5°)", 1: "b2 (45°)", 2: "b3 (67.5°)"}

        df_e91_full = []
        for i in range(res.num_pairs):
            is_key_pair = (res.alice_bases[i] == 1 and res.bob_bases[i] == 1)
            is_match = (res.alice_measured_bits[i] == res.bob_measured_bits[i])

            row = {
                "Pair #": i,
                "Alice Angle": alice_angle_names[res.alice_bases[i]],
                "Alice Bit": res.alice_measured_bits[i],
                "Bob Angle": bob_angle_names[res.bob_bases[i]],
                "Bob Bit": res.bob_measured_bits[i],
            }
            if res.intercept_result:
                was_int = res.intercept_result.intercepted[i]
                row["Eve Intercepted?"] = "👿 YES" if was_int else "—"

            row["Protocol Role"] = "🔑 Key Generation (45°/45°)" if is_key_pair else "🔔 CHSH Bell Test"
            if is_key_pair:
                row["Outcome Status"] = "✅ Key Match" if is_match else "🚨 Key Error"
            else:
                row["Outcome Status"] = "— Bell Sample"

            df_e91_full.append(row)
        st.dataframe(pd.DataFrame(df_e91_full), use_container_width=True, height=280)

    # Circuit Diagram Expander (Preserved)
    with st.expander("⚡ Quantum Circuit Visualization (Qiskit MPL)", expanded=False):
        fig = draw_quantum_circuit(res.circuit, res.num_pairs)
        st.pyplot(fig)


def render_mitm_leg_view(
    leg_title: str,
    sender_name: str,
    receiver_name: str,
    protocol_name: str,
    res,
    auth_failed: bool = False,
    key_prefix: str = ""
):
    """
    Renders complete end-to-end execution details for a MitM leg (Leg 1 or Leg 2),
    matching the exact UI structure, 5-stage pipeline, metrics, transmission log table,
    and quantum circuit of normal protocol simulation results.
    """
    st.markdown(f"#### 📊 {leg_title}", unsafe_allow_html=True)

    # 1. Metric Row
    final_bits_count = len(res.distillation_result.final_secret_key)
    if protocol_name == "E91":
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("EPR Pairs Generated", res.num_pairs)
        if auth_failed:
            m2.metric("Key Generation Pairs", "0 pairs", delta="Auth Blocked", delta_color="inverse")
            m3.metric("CHSH Bell Parameter |S|", "N/A (Aborted)")
            m4.metric("QBER on Key Pairs", "N/A (Aborted)")
        else:
            m2.metric("Key Generation Pairs", f"{res.sifting_result.sifted_key_length} pairs")
            chsh_color = "normal" if res.chsh_result.is_violated else "inverse"
            m3.metric("CHSH Bell Parameter |S|", f"{res.chsh_result.s_value:.3f}", "Bound: > 2.0", delta_color=chsh_color)
            m4.metric("QBER on Key Pairs", f"{res.sifting_result.qber*100:.1f}%")
        m5.metric("Final Secret Key", f"{final_bits_count} bits", delta="Aborted (0 Bits)" if res.distillation_result.is_aborted else "Distilled")
    else:
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Qubits Sent", res.num_qubits)
        if auth_failed:
            m2.metric("Sifted Key Length", "0 bits", delta="Auth Blocked", delta_color="inverse")
            m3.metric("Error Count", "0 bits")
            m4.metric("QBER", "N/A (Aborted)")
        else:
            m2.metric("Sifted Key Length", f"{res.sifting_result.sifted_key_length} bits", f"{res.sifting_result.sifting_ratio*100:.1f}% yield")
            m3.metric("Error Count", f"{res.sifting_result.error_count} bits")
            delta_color = "normal" if res.sifting_result.qber <= res.sifting_result.security_threshold else "inverse"
            m4.metric("QBER", f"{res.sifting_result.qber*100:.1f}%", f"Limit: {res.sifting_result.security_threshold*100:.1f}%", delta_color=delta_color)
        m5.metric("Final Secret Key", f"{final_bits_count} bits", delta="Aborted (0 Bits)" if res.distillation_result.is_aborted else "Distilled")

    # 2. Security Alert Box
    if auth_failed:
        st.error(
            f"🚨 **SESSION ABORTED ({sender_name} ↔ {receiver_name}):** Classical channel authentication failed! "
            f"HMAC signature mismatch detected during basis announcements. Sifted bits purged, 0 keys released."
        )
    elif res.distillation_result.is_aborted:
        st.error(f"🚨 **SESSION ABORTED:** {res.distillation_result.status_message}")
    else:
        st.warning(
            f"⚠️ **ACTIVE MITM KEY FORMED ({sender_name} ↔ {receiver_name}):** "
            f"A valid key of length {final_bits_count} bits was distilled between {sender_name} and {receiver_name} "
            f"(`0x{res.distillation_result.final_hex_key}`). Neither party detected channel disturbance!"
        )

    # 3. Complete Step-by-Step Key Formation Pipeline (Stages 1–5)
    render_key_formation_pipeline(
        protocol_name=protocol_name,
        res=res,
        sender_name=sender_name,
        receiver_name=receiver_name,
        key_prefix=key_prefix,
        auth_failed=auth_failed
    )

    # 4. Detailed Step-by-Step Bit & Measurement Transmission Log
    with st.expander(f"🔍 Step-by-Step Bit & Measurement Transmission Log ({sender_name} ↔ {receiver_name})", expanded=False):
        if protocol_name == "BB84":
            basis_names = {0: "Z (|0⟩,|1⟩)", 1: "X (|+⟩,|-⟩)"}
            df_data = []
            for i in range(res.num_qubits):
                if auth_failed:
                    status_str = "⛔ Auth Rejected"
                    err_str = "⛔ Aborted"
                else:
                    matched = (i in res.sifting_result.matching_indices)
                    is_err = matched and (res.alice_bits[i] != res.bob_measured_bits[i])
                    status_str = "✅ Sifted" if matched else "❌ Discard"
                    err_str = "🚨 ERROR" if is_err else ("✅ OK" if matched else "—")
                df_data.append({
                    f"{sender_name} Bit": res.alice_bits[i],
                    f"{sender_name} Basis": basis_names[res.alice_bases[i]],
                    f"{receiver_name} Basis": basis_names[res.bob_bases[i]],
                    f"{receiver_name} Measured": res.bob_measured_bits[i],
                    "Bases Match?": status_str,
                    "Error Status": err_str
                })
            st.dataframe(pd.DataFrame(df_data), use_container_width=True, height=260)
        elif protocol_name == "B92":
            b92_basis_desc = {0: "Basis 0 (Test |1⟩)", 1: "Basis 1 (Test |−⟩)"}
            df_data = []
            for i in range(res.num_qubits):
                if auth_failed:
                    det_status = "⛔ Auth Rejected"
                    inferred_str = "⛔ Aborted"
                    match_status = "⛔ Aborted"
                else:
                    is_conc = res.bob_conclusive[i]
                    inferred = res.bob_inferred_bits[i]
                    is_err = is_conc and (res.alice_bits[i] != inferred)
                    det_status = "✅ CONCLUSIVE" if is_conc else "⚪ Inconclusive"
                    inferred_str = inferred if is_conc else "—"
                    match_status = "🚨 ERROR" if is_err else ("✅ Match" if is_conc else "—")
                df_data.append({
                    "Qubit #": i,
                    f"{sender_name} Bit": res.alice_bits[i],
                    f"{sender_name} State": res.alice_states[i],
                    f"{receiver_name} Test Operator": b92_basis_desc[res.bob_bases[i]],
                    f"{receiver_name} Measurement": res.bob_raw_measurements[i],
                    "Detection Result": det_status,
                    f"{receiver_name} Inferred Bit": inferred_str,
                    "Match Status": match_status
                })
            st.dataframe(pd.DataFrame(df_data), use_container_width=True, height=260)
        else:  # E91
            alice_angle_names = {0: "a1 (0°)", 1: "a2 (45°)", 2: "a3 (90°)"}
            bob_angle_names = {0: "b1 (22.5°)", 1: "b2 (45°)", 2: "b3 (67.5°)"}
            df_data = []
            for i in range(res.num_pairs):
                if auth_failed:
                    role_str = "⛔ Auth Rejected"
                    outcome_str = "⛔ Aborted"
                else:
                    is_key_pair = (res.alice_bases[i] == 1 and res.bob_bases[i] == 1)
                    is_match = (res.alice_measured_bits[i] == res.bob_measured_bits[i])
                    role_str = "🔑 Key Generation (45°/45°)" if is_key_pair else "🔔 CHSH Bell Test"
                    outcome_str = ("✅ Key Match" if is_match else "🚨 Key Error") if is_key_pair else "— Bell Sample"
                df_data.append({
                    "Pair #": i,
                    f"{sender_name} Angle": alice_angle_names[res.alice_bases[i]],
                    f"{sender_name} Bit": res.alice_measured_bits[i],
                    f"{receiver_name} Angle": bob_angle_names[res.bob_bases[i]],
                    f"{receiver_name} Bit": res.bob_measured_bits[i],
                    "Protocol Role": role_str,
                    "Outcome Status": outcome_str
                })
            st.dataframe(pd.DataFrame(df_data), use_container_width=True, height=260)

    # 5. Quantum Circuit Visualization
    with st.expander(f"⚡ Quantum Circuit Visualization ({sender_name} ↔ {receiver_name})", expanded=False):
        max_q = min(24, res.num_qubits if hasattr(res, 'num_qubits') else res.num_pairs * 2)
        fig = draw_quantum_circuit(res.circuit, max_qubits_to_draw=max_q)
        st.pyplot(fig)


def render_mitm_results(res: MitmResult):
    """Renders comprehensive execution cards, topological flow, and keys for MitM attack."""
    st.markdown("---")
    badge_html = (
        '<span class="badge-compromised">🚨 MITM ATTACK SUCCESSFUL</span>'
        if res.auth_passed
        else '<span class="badge-secure">🛡️ MITM ATTACK THWARTED</span>'
    )
    st.markdown(f"#### 🎭 Man-in-the-Middle (MitM) Dual-Channel Execution {badge_html}", unsafe_allow_html=True)

    # 1. Custom Cyber Status Alert Banner
    if res.auth_passed:
        banner_html = f"""
        <div class="mitm-banner mitm-banner-compromised">
            <div class="mitm-banner-top">
                <div class="mitm-banner-title">
                    <span>🚨</span>
                    <span>CRITICAL VULNERABILITY: DUAL-CHANNEL MITM COMPROMISE</span>
                </div>
                <div class="mitm-banner-meta">PROTOCOL: {res.protocol_name} | CLASSICAL LINK: UNSIGNED (VULNERABLE)</div>
            </div>
            <div class="mitm-banner-desc">
                Because classical sifting announcements were <b>unauthenticated</b>, Eve intercepted and severed the communication channel.
                Eve established two independent QKD sessions without inducing anomalous QBER or violating Bell inequalities.
                <b>Eve holds BOTH keys</b>; Alice and Bob believe they share a private key, but their keys do not match.
            </div>
            <div class="mitm-points-grid">
                <div class="mitm-point-card point-danger">
                    <div class="mitm-point-title">⚡ Session Bifurcation</div>
                    Eve terminated Leg 1 with Alice (generating key <code>K_AE</code>) and Leg 2 with Bob (generating key <code>K_EB</code>).
                </div>
                <div class="mitm-point-card point-danger">
                    <div class="mitm-point-title">👿 Full Key Interception</div>
                    Eve possesses 100% of both keys, allowing total transparent decryption, tampering, and forgery of all user data.
                </div>
                <div class="mitm-point-card point-danger">
                    <div class="mitm-point-title">❌ Direct Key Divergence</div>
                    Alice & Bob key agreement is <b>{res.key_agreement_rate * 100:.1f}%</b> (pure statistical coincidence, ~50% random chance).
                </div>
            </div>
        </div>
        """
    else:
        banner_html = f"""
        <div class="mitm-banner mitm-banner-thwarted">
            <div class="mitm-banner-top">
                <div class="mitm-banner-title">
                    <span>🛡️</span>
                    <span>SECURITY SHIELD ACTIVE: MITM ATTACK DETECTED & THWARTED</span>
                </div>
                <div class="mitm-banner-meta">PROTOCOL: {res.protocol_name} | CLASSICAL LINK: HMAC-SHA256 SIGNED (SECURE)</div>
            </div>
            <div class="mitm-banner-desc">
                Classical channel authentication is <b>ENABLED</b>. When Eve attempted to intercept and proxy public basis announcements, 
                cryptographic signature verification (HMAC-SHA256) failed on the receiver's end. Key distillation was immediately aborted.
            </div>
            <div class="mitm-points-grid">
                <div class="mitm-point-card point-success">
                    <div class="mitm-point-title">🔑 Cryptographic Verification</div>
                    Public basis announcements require valid signatures using <code>ALICE_BOB_SECRET</code>. Eve cannot forge this signature.
                </div>
                <div class="mitm-point-card point-success">
                    <div class="mitm-point-title">🛑 Session Terminated (Stage 4)</div>
                    Bob detected classical tampering during basis reconciliation. Sifted bit pools were instantly purged before distillation.
                </div>
                <div class="mitm-point-card point-success">
                    <div class="mitm-point-title">🔒 Zero Adversary Leakage</div>
                    Exactly <b>0 secret bits</b> were released to Eve. The security of quantum cryptographic key generation is preserved.
                </div>
            </div>
        </div>
        """
    st.markdown(clean_html(banner_html), unsafe_allow_html=True)

    # 2. Modern 5-Metric Responsive Grid (No Text Truncation)
    alice_len = f"{len(res.alice_key)} bits" if res.alice_key else "0 bits"
    bob_len = f"{len(res.bob_key)} bits" if res.bob_key else "0 bits"
    proto_tag = "4-State BB84" if "BB84" in res.protocol_name else ("2-State Non-Orthogonal" if "B92" in res.protocol_name else "EPR Bell Pairs")
    
    if res.use_authentication:
        auth_icon = "🛡️"
        auth_val = "Signed (Secure)"
        auth_sub = "HMAC-SHA256 Active"
        auth_sub_class = "sub-green"
    else:
        auth_icon = "⚠️"
        auth_val = "Unsigned"
        auth_sub = "Vulnerable (No Auth)"
        auth_sub_class = "sub-red"

    if res.auth_passed:
        alice_sub = "Distilled with Eve"
        alice_sub_class = "sub-cyan"
        bob_sub = "Distilled with Eve"
        bob_sub_class = "sub-cyan"
        match_val = f"{res.key_agreement_rate * 100:.1f}%"
        match_sub = "🚨 Keys Mismatch (Compromised)"
        match_sub_class = "sub-red"
    else:
        alice_sub = "Purged (0 Bits)"
        alice_sub_class = "sub-red"
        bob_sub = "Purged (0 Bits)"
        bob_sub_class = "sub-red"
        match_val = "0% Match"
        match_sub = "🛡️ Aborted (Zero Leak)"
        match_sub_class = "sub-green"

    metrics_html = f"""
    <div class="mitm-stat-grid">
        <div class="mitm-stat-card">
            <div class="mitm-stat-label"><span>⚛️</span> Protocol Architecture</div>
            <div class="mitm-stat-val">{res.protocol_name}</div>
            <div class="mitm-stat-sub sub-cyan">{proto_tag}</div>
        </div>
        <div class="mitm-stat-card">
            <div class="mitm-stat-label"><span>{auth_icon}</span> Classical Channel</div>
            <div class="mitm-stat-val">{auth_val}</div>
            <div class="mitm-stat-sub {auth_sub_class}">{auth_sub}</div>
        </div>
        <div class="mitm-stat-card">
            <div class="mitm-stat-label"><span>🔑</span> Alice Key (K_AE)</div>
            <div class="mitm-stat-val">{alice_len}</div>
            <div class="mitm-stat-sub {alice_sub_class}">{alice_sub}</div>
        </div>
        <div class="mitm-stat-card">
            <div class="mitm-stat-label"><span>🔑</span> Bob Key (K_EB)</div>
            <div class="mitm-stat-val">{bob_len}</div>
            <div class="mitm-stat-sub {bob_sub_class}">{bob_sub}</div>
        </div>
        <div class="mitm-stat-card">
            <div class="mitm-stat-label"><span>⚖️</span> Alice vs Bob Key Match</div>
            <div class="mitm-stat-val">{match_val}</div>
            <div class="mitm-stat-sub {match_sub_class}">{match_sub}</div>
        </div>
    </div>
    """
    st.markdown(clean_html(metrics_html), unsafe_allow_html=True)

    # 3. Interactive Network Architecture & Key Topology Visualization
    with st.expander("🌐 View Man-in-the-Middle Attack Architecture & Key Topology", expanded=True):
        if res.auth_passed:
            status_pill = '<span class="topology-status-pill status-pill-compromised">🚨 MITM ACTIVE (UNAUTHENTICATED CLASSICAL LINK)</span>'
            eve_badge = f'Holds: K_AE ({alice_len}) & K_EB ({bob_len})'
            leg1_class = "Unsigned (Intercepted)"
            leg1_color = "#f87171"
            leg2_class = "Unsigned (Proxied)"
            leg2_color = "#f87171"
            summary_class = "summary-compromised"
            summary_headline = f"❌ Keys Mismatch ({res.key_agreement_rate * 100:.1f}% random correlation)"
            eve_knowledge = "100% of Both Keys"
            bit_correlation = "0% Quantum Correlation"
        else:
            status_pill = '<span class="topology-status-pill status-pill-thwarted">🛡️ MITM BLOCKED (AUTHENTICATED CLASSICAL LINK)</span>'
            eve_badge = "Blocked (0 Keys Formed)"
            leg1_class = "Signed (Alice Secret)"
            leg1_color = "#34d399"
            leg2_class = "Signature Mismatch (Rejected)"
            leg2_color = "#f87171"
            summary_class = "summary-thwarted"
            summary_headline = "🛡️ Sifting Purged (0 bits distilled, zero adversary intelligence)"
            eve_knowledge = "0% (No keys formed)"
            bit_correlation = "Aborted at Stage 4 Security Gate"

        topology_html = f"""
        <div class="topology-container">
            <div class="topology-status-bar">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:1.15rem;">🌐</span>
                    <span style="font-weight:700; color:#f8fafc; font-size:0.95rem;">Dual-Channel Network Topology & Key Exchange Flow</span>
                </div>
                {status_pill}
            </div>

            <div class="topology-flow-grid">
                <!-- Node Alice -->
                <div class="topology-node node-alice">
                    <div>
                        <div class="node-avatar">👩‍💻</div>
                        <div class="node-title">Alice</div>
                        <div class="node-subtitle">Sender / Qubit Source</div>
                    </div>
                    <div class="node-key-badge badge-alice">
                        K_AE: {alice_len}
                    </div>
                </div>

                <!-- Leg 1 Link -->
                <div class="topology-link">
                    <div class="link-header">🔵 Leg 1 (Alice ↔ Eve)</div>
                    <div class="link-item">
                        <span class="link-item-name">⚡ Quantum</span>
                        <span class="link-item-val" style="color:#38bdf8;">Transmitted</span>
                    </div>
                    <div class="link-item">
                        <span class="link-item-name">📡 Classical</span>
                        <span class="link-item-val" style="color:{leg1_color};">{leg1_class}</span>
                    </div>
                    <div class="link-item">
                        <span class="link-item-name">🔑 Key Distilled</span>
                        <span class="link-item-val" style="color:#00f5d4;">K_AE ({alice_len})</span>
                    </div>
                </div>

                <!-- Node Eve -->
                <div class="topology-node node-eve">
                    <div>
                        <div class="node-avatar">👿</div>
                        <div class="node-title">Eve (Adversary)</div>
                        <div class="node-subtitle">Man-in-the-Middle Proxy</div>
                        <div style="font-size:0.75rem; color:#cbd5e1; margin-bottom:6px; line-height:1.35;">
                            Posing as <b>Bob</b> to Alice<br>
                            Posing as <b>Alice</b> to Bob
                        </div>
                    </div>
                    <div class="node-key-badge badge-eve">
                        {eve_badge}
                    </div>
                </div>

                <!-- Leg 2 Link -->
                <div class="topology-link">
                    <div class="link-header">🟣 Leg 2 (Eve ↔ Bob)</div>
                    <div class="link-item">
                        <span class="link-item-name">⚡ Quantum</span>
                        <span class="link-item-val" style="color:#c084fc;">Forwarded</span>
                    </div>
                    <div class="link-item">
                        <span class="link-item-name">📡 Classical</span>
                        <span class="link-item-val" style="color:{leg2_color};">{leg2_class}</span>
                    </div>
                    <div class="link-item">
                        <span class="link-item-name">🔑 Key Distilled</span>
                        <span class="link-item-val" style="color:#00f5d4;">K_EB ({bob_len})</span>
                    </div>
                </div>

                <!-- Node Bob -->
                <div class="topology-node node-bob">
                    <div>
                        <div class="node-avatar">👨‍💻</div>
                        <div class="node-title">Bob</div>
                        <div class="node-subtitle">Receiver / Analyzer</div>
                    </div>
                    <div class="node-key-badge badge-bob">
                        K_EB: {bob_len}
                    </div>
                </div>
            </div>

            <!-- Alice vs Bob Direct Agreement Bar -->
            <div class="topology-summary-bar {summary_class}">
                <div>
                    <b>Direct Key Agreement (Alice ↔ Bob):</b> {summary_headline}
                </div>
                <div style="display:flex; gap:18px; font-size:0.84rem;">
                    <span>Eve Knowledge: <b>{eve_knowledge}</b></span>
                    <span>Correlation: <b>{bit_correlation}</b></span>
                </div>
            </div>
        </div>
        """
        st.markdown(clean_html(topology_html), unsafe_allow_html=True)

    # 4. Classical Packet Inspection & Cryptographic Authentication Console
    if hasattr(res, 'authentic_packet') and res.authentic_packet is not None:
        with st.expander("📦 Deep Dive: Inspected Classical Basis Packets & HMAC Verification", expanded=True):
            st.markdown(
                "In quantum key distribution, measurement bases and detections are published across the public classical channel. "
                "Below are the **structured classical payloads** exchanged during simulation and intercepted by Eve."
            )
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown("**1️⃣ Alice's Genuine Announcement Packet:**")
                st.code(res.authentic_payload_str, language="json")
                st.caption(f"🔑 Signed with `ALICE_BOB_SECRET`: HMAC = `{res.authentic_tag}`")

            with col_p2:
                st.markdown("**2️⃣ Eve's Intercepted & Tampered Packet (Sent to Bob):**")
                st.code(res.forged_payload_str, language="json")
                if res.use_authentication:
                    st.caption(f"👿 Signed with `EVE_FORGED_SECRET`: HMAC = `{res.forged_tag}`")
                else:
                    st.caption("⚠️ Transmitted without HMAC tag over unauthenticated classical channel.")

            if res.use_authentication:
                crypto_html = f"""
                <div class="crypto-console">
                    <div class="crypto-grid">
                        <div class="crypto-box">
                            <div class="crypto-box-label">Received HMAC (from Eve)</div>
                            <div class="crypto-tag-code tag-mismatch">0x{res.forged_tag}</div>
                            <div style="font-size:0.75rem; color:#94a3b8; margin-top:6px;">Signed with EVE_FORGED_SECRET</div>
                        </div>
                        <div class="crypto-box">
                            <div class="crypto-box-label">Expected HMAC (ALICE_BOB_SECRET)</div>
                            <div class="crypto-tag-code tag-expected">0x{res.expected_tag}</div>
                            <div style="font-size:0.75rem; color:#94a3b8; margin-top:6px;">Computed with authentic pre-shared key</div>
                        </div>
                        <div class="crypto-box">
                            <div class="crypto-box-label">Bob's Verification Verdict</div>
                            <div class="crypto-tag-code tag-mismatch" style="font-size:0.85rem;">❌ SIGNATURE MISMATCH</div>
                            <div style="font-size:0.75rem; color:#fca5a5; margin-top:6px;">Basis Reconciliation Aborted</div>
                        </div>
                    </div>
                    <div class="crypto-explanation crypto-exp-danger">
                        ❌ <b>Bob Cryptographic Verification Result:</b> Bob recomputed <code>HMAC-SHA256(ALICE_BOB_SECRET, payload) = 0x{res.expected_tag}</code>. 
                        Because Eve does not possess <code>ALICE_BOB_SECRET</code>, the received signature (<code>0x{res.forged_tag}</code>) failed verification!
                        Bob immediately detected unauthorized classical message tampering. Basis reconciliation was rejected and 0 secret bits were distilled.
                    </div>
                </div>
                """
            else:
                crypto_html = """
                <div class="crypto-console">
                    <div class="crypto-grid">
                        <div class="crypto-box">
                            <div class="crypto-box-label">Received HMAC</div>
                            <div class="crypto-tag-code tag-neutral">None (Unsigned Packet)</div>
                            <div style="font-size:0.75rem; color:#94a3b8; margin-top:6px;">Classical channel is unauthenticated</div>
                        </div>
                        <div class="crypto-box">
                            <div class="crypto-box-label">Expected HMAC</div>
                            <div class="crypto-tag-code tag-neutral">Bypassed</div>
                            <div style="font-size:0.75rem; color:#94a3b8; margin-top:6px;">No cryptographic signature required</div>
                        </div>
                        <div class="crypto-box">
                            <div class="crypto-box-label">Bob's Verification Verdict</div>
                            <div class="crypto-tag-code tag-neutral" style="font-size:0.85rem; color:#fcd34d;">⚠️ BYPASS (NO AUTH)</div>
                            <div style="font-size:0.75rem; color:#fcd34d; margin-top:6px;">Unchecked Basis Acceptance</div>
                        </div>
                    </div>
                    <div class="crypto-explanation crypto-exp-warning">
                        ⚠️ <b>Classical Channel Unprotected:</b> Bob accepted Eve's substituted basis announcements without requiring an HMAC authentication tag.
                        Bob completed basis reconciliation directly with the adversary, enabling Eve to negotiate an independent secret key undetected.
                    </div>
                </div>
                """
            st.markdown(clean_html(crypto_html), unsafe_allow_html=True)

    # 5. Keys Comparison Matrix (when attack succeeded and keys formed)
    if res.auth_passed:
        st.markdown("##### 🔑 Multi-Party Key Distillation & Compromise Matrix")
        alice_preview = "".join(str(b) for b in res.alice_key[:32]) + ("..." if len(res.alice_key) > 32 else "")
        bob_preview = "".join(str(b) for b in res.bob_key[:32]) + ("..." if len(res.bob_key) > 32 else "")

        keys_html = f"""
        <div class="key-matrix-grid">
            <div class="key-card key-card-alice">
                <div class="key-card-header">
                    <div class="key-card-title">👩‍💻 Alice's Key (K_AE)</div>
                    <div class="node-key-badge badge-alice">{len(res.alice_key)} bits</div>
                </div>
                <div class="key-preview-bits">{alice_preview}</div>
                <div>
                    <span class="key-hex-pill">0x{res.alice_hex}</span>
                </div>
                <div class="key-status-text">
                    Negotiated with Eve (posing as Bob). Distilled via Stages 1–5 sifting & privacy amplification.
                </div>
            </div>

            <div class="key-card key-card-eve">
                <div class="key-card-header">
                    <div class="key-card-title">👿 Eve's Intercepted Keys</div>
                    <div class="node-key-badge badge-eve">Both Keys Captured</div>
                </div>
                <div class="key-preview-bits" style="color:#fca5a5;">
                    K_AE: 0x{res.eve_alice_hex}<br>
                    K_EB: 0x{res.eve_bob_hex}
                </div>
                <div>
                    <span class="key-hex-pill" style="color:#f43f5e; background:rgba(244,63,94,0.15);">100% Adversary Leak</span>
                </div>
                <div class="key-status-text">
                    Eve holds BOTH keys simultaneously. All Alice ↔ Bob encrypted traffic can be read, tampered, and forged.
                </div>
            </div>

            <div class="key-card key-card-bob">
                <div class="key-card-header">
                    <div class="key-card-title">👨‍💻 Bob's Key (K_EB)</div>
                    <div class="node-key-badge badge-bob">{len(res.bob_key)} bits</div>
                </div>
                <div class="key-preview-bits">{bob_preview}</div>
                <div>
                    <span class="key-hex-pill">0x{res.bob_hex}</span>
                </div>
                <div class="key-status-text">
                    Negotiated with Eve (posing as Alice). Independent distillation yield without channel disturbance.
                </div>
            </div>
        </div>
        """
        st.markdown(clean_html(keys_html), unsafe_allow_html=True)

        # Bitwise Alice vs Bob Comparison Table
        with st.expander("🔍 Bitwise Comparison: Alice's Key vs Bob's Key (Demonstrating Key Divergence)", expanded=False):
            st.caption(
                "Because Alice and Bob negotiated keys independently with Eve, their raw bit strings "
                "have zero mutual quantum correlation. Bit mismatches approximate ~50% (random chance)."
            )
            df_compare = []
            for i in range(min(32, res.comparison_length)):
                a_bit = res.alice_key[i]
                b_bit = res.bob_key[i]
                match = (a_bit == b_bit)
                df_compare.append({
                    "Bit Position": f"Bit #{i}",
                    "Alice Key Bit (K_AE)": a_bit,
                    "Bob Key Bit (K_EB)": b_bit,
                    "Eve Knowledge": "✅ Known (Both)",
                    "Alice == Bob?": "✅ Coincidence" if match else "🚨 MISMATCH"
                })
            st.dataframe(pd.DataFrame(df_compare), use_container_width=True)

    # 6. Deep dive tabs for both legs with complete end-to-end details
    if res.alice_eve_result and res.eve_bob_result:
        st.markdown("##### 🔬 End-to-End Key Formation by Link (Leg 1 & Leg 2)")
        tab_leg1, tab_leg2 = st.tabs([
            f"🔵 Leg 1: Alice ↔ Eve ({res.protocol_name})",
            f"🟣 Leg 2: Eve ↔ Bob ({res.protocol_name})"
        ])

        with tab_leg1:
            render_mitm_leg_view(
                leg_title="Leg 1: Alice ↔ Eve (Eve Posing as Bob)",
                sender_name="Alice",
                receiver_name="Eve",
                protocol_name=res.protocol_name,
                res=res.alice_eve_result,
                auth_failed=(not res.auth_passed),
                key_prefix="mitm_l1_"
            )

        with tab_leg2:
            render_mitm_leg_view(
                leg_title="Leg 2: Eve ↔ Bob (Eve Posing as Alice)",
                sender_name="Eve",
                receiver_name="Bob",
                protocol_name=res.protocol_name,
                res=res.eve_bob_result,
                auth_failed=(not res.auth_passed),
                key_prefix="mitm_l2_"
            )


