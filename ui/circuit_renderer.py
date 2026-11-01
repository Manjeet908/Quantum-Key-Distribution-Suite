"""
Circuit rendering module using Qiskit and Matplotlib with dark mode themes.
"""
from typing import Optional
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit

def draw_quantum_circuit(
    circuit: QuantumCircuit, 
    max_qubits_to_draw: int = 8,
    style_dark: bool = True
) -> plt.Figure:
    """
    Renders a Qiskit QuantumCircuit into a Matplotlib Figure.
    If circuit has more than max_qubits_to_draw, creates a representative view
    of the first few qubits to maintain visual readability.
    """
    # If the circuit is very wide, slice representative subcircuit for display
    num_q = circuit.num_qubits
    if num_q > max_qubits_to_draw:
        # Create a compact representative circuit with first few qubits
        from qiskit import QuantumCircuit as SubCircuit
        sub_qc = SubCircuit(max_qubits_to_draw, max_qubits_to_draw)
        for instruction in circuit.data:
            # Map qubits if they fall in the first max_qubits_to_draw
            q_indices = [circuit.find_bit(q).index for q in instruction.qubits]
            if all(idx < max_qubits_to_draw for idx in q_indices):
                c_indices = [circuit.find_bit(c).index for c in instruction.clbits] if instruction.clbits else []
                if all(idx < max_qubits_to_draw for idx in c_indices):
                    sub_qc.append(instruction.operation, q_indices, c_indices)
        display_circuit = sub_qc
    else:
        display_circuit = circuit

    # Custom dark theme dictionary for Qiskit mpl drawer
    style = {
        "name": "iqx-dark" if style_dark else "default",
        "backgroundcolor": "#0b0f19" if style_dark else "#ffffff",
        "textcolor": "#f8fafc" if style_dark else "#000000",
        "subtextcolor": "#94a3b8" if style_dark else "#333333",
        "linecolor": "#38bdf8" if style_dark else "#000000",
        "barrierfacecolor": "#334155" if style_dark else "#cccccc",
        "displaycolor": {
            "x": ["#ec4899", "#ffffff"],
            "h": ["#00f5d4", "#0b0f19"],
            "cx": ["#7b2cbf", "#ffffff"],
            "ry": ["#f59e0b", "#0b0f19"],
            "measure": ["#ef4444", "#ffffff"],
        },
        "figwidth": -1,
        "dpi": 150
    }

    try:
        fig = display_circuit.draw(output='mpl', style=style)
        return fig
    except Exception:
        # Safe fallback: plain matplotlib figure
        fig, ax = plt.subplots(figsize=(8, 4))
        if style_dark:
            fig.patch.set_facecolor('#0b0f19')
            ax.set_facecolor('#0b0f19')
            ax.tick_params(colors='#94a3b8')
        ax.text(
            0.5, 0.5, 
            display_circuit.draw(output='text'), 
            family='monospace', 
            ha='center', 
            va='center',
            color='#00f5d4' if style_dark else '#000000',
            fontsize=9
        )
        ax.axis('off')
        return fig
