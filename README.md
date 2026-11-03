# ⚛️ Quantum Key Distribution (QKD) Simulation & Analysis Suite

A unified, interactive Quantum Key Distribution (QKD) simulator built with **Qiskit** and **Streamlit**. 

This suite provides end-to-end simulations of **BB84**, **B92**, and **E91** protocols, models quantum channel attacks (**Intercept-Resend**) and physical noise (depolarizing and bit-flip), and provides rigorous statistical analysis and benchmark comparisons.

## 📞 Contact Information

- Email: yadavmanjeet629@gmail.com
- Phone: 9451250925
- Email: abdulkalam754600@gmail.com
- Phone: 9155748962

---

## 🌟 Key Features

1. **Core QKD Protocols**:
   - **BB84 (Bennett & Brassard 1984)**: 4-state encoding across Rectilinear ($Z$) and Diagonal ($X$) bases with Shannon error correction bound ($11.0\%$ QBER limit).
   - **B92 (Bennett 1992)**: 2-state non-orthogonal encoding ($|0\rangle, |+\rangle$) with Unambiguous State Discrimination (USD) and conclusive detection filtering ($4.8\%$ QBER cutoff).
   - **E91 (Ekert 1991)**: Entanglement-based protocol using EPR Bell pairs ($|\Phi^+\rangle$) with automated Clauser-Horne-Shimony-Holt (CHSH) Bell inequality validation ($|S| > 2.0$ confirms maximal entanglement and absence of eavesdroppers).

2. **Adversarial Attack & Noise Simulation**:
   - **Intercept-Resend Attack**: Eve measures flying qubits in transit and resends collapsed states. Formulates the exact theoretical $25\%$ QBER spike in BB84.
   - **Channel Noise**: Configurable fiber depolarizing and bit-flip channel noise models.

3. **Modern High-Tech Streamlit Dashboard**:
   - Step-by-step transmission logs (Alice prep $\to$ Channel & Eve $\to$ Bob measurement $\to$ Sifting $\to$ Error Estimation $\to$ Key Distillation).
   - Dynamic Qiskit quantum circuit visualization (`qc.draw('mpl')`).
   - Interactive comparative analysis suite with live benchmarks and analytical performance curves.
   - Quantum Cryptography Academy with complete theoretical proofs and formulas.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Qiskit, Qiskit-Aer, Streamlit, Matplotlib, Pylatexenc

### Installation
```bash
cd "quantum-auth-suite"
pip install -r requirements.txt
```

### Running the Application
Launch the interactive Streamlit dashboard:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

## 📁 Repository Structure
```
quantum-qkd-suite/
│
├── app.py                          # Main Streamlit Dashboard entry point
├── requirements.txt                # Dependency specifications
├── README.md                       # Comprehensive documentation
│
├── core/                           # Quantum Simulation Engine
│   ├── qiskit_engine.py            # AerSimulator wrapper (Matrix Product State)
│   ├── bb84.py                     # BB84 protocol implementation
│   ├── b92.py                      # B92 protocol implementation
│   └── e91.py                      # E91 entanglement & Bell protocol
│
├── attacks/                        # Eavesdropping & Channel Degradation Models
│   ├── intercept_resend.py         # Eve intercept-measure-resend
│   └── noise_channel.py            # Depolarizing & bit flip channel noise
│
├── postprocessing/                 # Key Distillation & Security Verification
│   ├── sifting.py                  # Basis reconciliation & inconclusive filters
│   ├── chsh_evaluator.py           # CHSH S-parameter calculation (Cirel'son bound)
│   ├── privacy_amp.py              # Parity reconciliation & Shannon privacy amplification
│   └── benchmark_evaluator.py      # Analytical modeling & multi-protocol benchmark runner
│
├── ui/                             # Streamlit UI & Visualizations
│   ├── styles.py                   # Cyberpunk dark theme CSS & tokens
│   ├── circuit_renderer.py         # Dynamic Qiskit MPL circuit diagram generator
│   ├── views_simulator.py          # Interactive single protocol lab
│   ├── views_analysis.py           # Protocol analysis & benchmark comparison suite
│   └── views_theory.py             # Theory academy & mathematical proofs
│
└── tests/                          # Automated Unit & Verification Tests
    └── test_benchmark_evaluator.py # Benchmark evaluator & analytical model tests
```
