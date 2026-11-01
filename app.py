"""Main Streamlit Application: Quantum Key Distribution Suite."""
import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import qiskit
from ui.styles import QUANTUM_CSS, render_hero
from ui.views_simulator import render_simulator_view
from ui.views_analysis import render_analysis_view
from ui.views_theory import render_theory_view
from ui.views_benchmarks import render_benchmark_view

st.set_page_config(page_title="Quantum QKD Simulation & Analysis Suite", page_icon="⚛️",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(QUANTUM_CSS, unsafe_allow_html=True)
st.markdown(render_hero(title="Quantum QKD Simulation & Analysis Suite", subtitle=""), unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🎛️ Navigation & Control")
    nav_selection = st.radio("Select Dashboard Module", [
        "🔬 Protocol Simulator", "📊 Protocol Analysis & Comparison",
        "📈 Benchmark Results", "📚 Theory & Academy"], index=0)
    st.markdown("---")
    st.markdown("### ⚙️ Simulation Environment")
    st.markdown("- **Quantum Backend:** `Qiskit AerSimulator`")
    st.markdown("- **Method:** `Matrix Product State (MPS)`")
    st.markdown(f"- **Qiskit Core:** `v{qiskit.__version__}`")
    st.markdown(f"- **Python Version:** `{sys.version.split()[0]}`")
    st.markdown("---")
    st.markdown("### ℹ️ Quick Protocol Guide")
    st.caption("BB84: four states across two bases.\n\n"
               "B92: two non-orthogonal states.\n\n"
               "E91: entangled pairs and Bell-correlation testing.\n\n"
               "Security thresholds depend on the selected model and assumptions.")

if nav_selection == "🔬 Protocol Simulator":
    render_simulator_view()
elif nav_selection == "📊 Protocol Analysis & Comparison":
    render_analysis_view()
elif nav_selection == "📈 Benchmark Results":
    render_benchmark_view()
else:
    render_theory_view()
