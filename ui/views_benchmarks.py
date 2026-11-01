"""Benchmark results page. Requires Streamlit, pandas and Plotly."""
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

COLORS = {"BB84": "#38bdf8", "B92": "#fbbf24", "E91": "#c084fc"}
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FILE = ROOT / "benchmark_results" / "benchmark_summary.json"


@st.cache_data(show_spinner=False)
def parse_report(content):
    report = json.loads(content)
    if not isinstance(report, dict) or not isinstance(report.get("experiments"), list):
        raise ValueError("Choose a benchmark JSON containing an experiments list.")
    if not report["experiments"]:
        raise ValueError("This report contains no experiments.")
    for experiment in report["experiments"]:
        if not isinstance(experiment, dict) or not isinstance(experiment.get("records"), list):
            raise ValueError("Each experiment must contain a records list.")
    return report


def number(value, digits=2):
    return "N/A" if value is None or pd.isna(value) else f"{value:,.{digits}f}"


def normalise(records):
    df = pd.DataFrame(records)
    if df.empty:
        return df
    # Also accept the older exports, without inventing confidence intervals.
    aliases = {"sifted_key_length_mean": "n_sifted_mean",
               "final_key_length_mean": "n_final_key_mean",
               "key_rate_mean": "key_yield_per_pulse_mean",
               "execution_time_ms_mean": "simulator_runtime_ms_mean"}
    df = df.rename(columns={a: b for a, b in aliases.items() if b not in df})
    for col in df.columns:
        if col.endswith(("_mean", "_se", "_lower", "_upper", "_pct")) or col in (
            "num_qubits", "noise_level", "eve_intensity", "trial_count", "use_authentication"
        ):
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def plot(df, x, y, title, xlabel, ylabel, key, bounds=None, reference=None):
    if x not in df or y not in df:
        st.info(f"{title}: this metric is unavailable in this report.")
        return
    fig = go.Figure()
    for protocol, color in COLORS.items():
        part = df[df.protocol == protocol].sort_values(x).dropna(subset=[x, y])
        if part.empty:
            continue
        error = None
        if bounds and all(c in part for c in bounds):
            lo, hi = bounds
            error = dict(type="data", symmetric=False,
                         array=(part[hi] - part[y]).clip(lower=0),
                         arrayminus=(part[y] - part[lo]).clip(lower=0),
                         thickness=1.3, width=4)
        fig.add_trace(go.Scatter(
            x=part[x], y=part[y], name=protocol, mode="lines+markers",
            line=dict(color=color, width=3), marker=dict(size=8), error_y=error,
            hovertemplate=f"{protocol}<br>{xlabel}: %{{x}}<br>{ylabel}: %{{y:.3f}}<extra></extra>"
        ))
    if reference is not None:
        fig.add_hline(y=reference, line_dash="dash", line_color="#94a3b8",
                      annotation_text=f"Reference: {reference}")
    fig.update_layout(title=title, xaxis_title=xlabel, yaxis_title=ylabel,
                      height=370, margin=dict(l=15, r=15, t=55, b=20),
                      legend=dict(orientation="h", y=1.16), hovermode="x unified")
    st.plotly_chart(fig, width="stretch", key=key)


def tables(df, key):
    with st.expander("Inspect and download the numbers"):
        st.caption("Blank values mean unavailable or not applicable, rather than zero.")
        st.dataframe(df, width="stretch", hide_index=True)
        st.download_button("Download this table (CSV)", df.to_csv(index=False).encode(),
                           file_name=f"{key}.csv", mime="text/csv", key=f"download_{key}")


def authentication(df, key):
    if "use_authentication" not in df:
        st.info("Authentication settings are unavailable.")
        return
    st.write("**Question:** Does authenticating the classical channel stop the simulated MitM attack?")
    for enabled, label in [(0, "Without authentication"), (1, "With authentication")]:
        part = df[df.use_authentication == enabled]
        if part.empty:
            continue
        st.markdown(f"#### {label}")
        fig = go.Figure()
        for col, name, color in [("compromise_rate_pct", "Compromised", "#fb7185"),
                                  ("abort_rate_pct", "Aborted", "#38bdf8")]:
            if col in part:
                fig.add_trace(go.Bar(x=part.protocol, y=part[col], name=name,
                                     marker_color=color, hovertemplate="%{x}: %{y:.2f}%<extra>" + name + "</extra>"))
        fig.update_layout(barmode="group", yaxis=dict(title="Observed runs (%)", range=[0, 105]),
                          height=280, margin=dict(t=30, b=10), legend=dict(orientation="h"))
        st.plotly_chart(fig, width="stretch", key=f"{key}_auth_{enabled}")
    st.info("Compromised means the attacker succeeded. Aborted means no key was accepted. "
            "A low error rate inside Alice–Eve and Eve–Bob sessions does not authenticate the endpoints.")
    cols = [c for c in ["protocol", "use_authentication", "trial_count", "auth_status",
            "compromise_rate_pct", "abort_rate_pct", "alice_eve_qber_pct_mean",
            "eve_bob_qber_pct_mean", "alice_bob_mismatch_pct_mean"] if c in df]
    st.dataframe(df[cols], width="stretch", hide_index=True)


def get_available_benchmark_files():
    """Discovers all valid benchmark JSON report files in the project."""
    benchmark_dir = ROOT / "benchmark_results"
    if not benchmark_dir.exists():
        return []
    
    files = []
    for p in benchmark_dir.glob("*.json"):
        if p.is_file() and (p.name == "benchmark_summary.json" or p.name.startswith("benchmark_run_") or "benchmark" in p.name):
            files.append(p)
            
    summary_path = benchmark_dir / "benchmark_summary.json"
    other_files = [f for f in files if f != summary_path]
    other_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    if summary_path.exists() and summary_path in files:
        return [summary_path] + other_files
    return other_files


def render_benchmark_view(data_path=None):
    st.header("Benchmark results")
    st.write("Compare BB84, B92 and E91 under ideal conditions, channel noise and simulated attacks.")

    if data_path:
        selected_file = Path(data_path)
    else:
        available_files = get_available_benchmark_files()
        if not available_files:
            st.info("No benchmark results found in `benchmark_results/`. Run `python run_benchmarks.py` to generate results.")
            return

        # If there are multiple files, provide a selector. If only a single file, omit this section completely.
        if len(available_files) > 1:
            def format_file_label(p: Path) -> str:
                if p.name == "benchmark_summary.json":
                    return "benchmark_summary.json (Latest Master Summary)"
                stem = p.stem.replace("benchmark_run_", "")
                if len(stem) == 15 and "_" in stem:
                    date_part, time_part = stem.split("_")
                    formatted_dt = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                    return f"{p.name} ({formatted_dt})"
                return p.name

            col_select, _ = st.columns([1.5, 1])
            with col_select:
                selected_file = st.selectbox(
                    "Select Benchmark Result File",
                    available_files,
                    index=0,
                    format_func=format_file_label,
                    key="benchmark_selected_file"
                )
        else:
            selected_file = available_files[0]

    try:
        content = selected_file.read_bytes()
        report = parse_report(content)
    except FileNotFoundError:
        st.info(f"Could not find `{selected_file.name}` in `benchmark_results/`. Run `python run_benchmarks.py` to generate results.")
        return
    except (ValueError, TypeError, OSError) as error:
        st.error(f"Could not load benchmark results from `{selected_file.name}`: {error}")
        return

    env = report.get("environment", {})
    experiments = report["experiments"]
    frames = [normalise(e["records"]) for e in experiments]
    nonempty = [f for f in frames if not f.empty and "protocol" in f]
    if not nonempty:
        st.info("No protocol records found in this report.")
        return
    all_data = pd.concat(nonempty, ignore_index=True)
    trials = int(all_data.trial_count.fillna(0).sum()) if "trial_count" in all_data else None
    a, b, c, d = st.columns(4)
    a.metric("Protocols", all_data.protocol.nunique())
    b.metric("Scenarios", len(experiments))
    c.metric("Configurations", len(all_data))
    d.metric("Trials", f"{trials:,}" if trials is not None else "N/A")
    st.caption(f"Run: {report.get('run_id', 'N/A')} · "
               f"{env.get('trials_per_point', 'N/A')} trials per configuration · "
               f"Backend: {env.get('simulator_backend', 'N/A')}")
    st.info("These are simulation results for the selected implementation and decision thresholds. "
            "Key yield is output bits per reported pulse/pair; runtime measures simulator computation.")
    selected = st.multiselect("Protocols shown", list(COLORS), default=list(COLORS), key="benchmark_protocols")
    if not selected:
        st.info("Select at least one protocol.")
        return
    st.caption("Blue: BB84 · Amber: B92 · Purple: E91. Error bars show the reported 95% confidence "
               "interval for the mean across trials; they are not per-run security bounds.")
    labels = {"exp1_baseline_scaling": "Ideal channel", "exp2_noise_tolerance": "Channel noise",
              "exp3_intercept_resend": "Intercept–resend", "exp4_mitm_authentication": "MitM & authentication",
              "exp5_statistical_stability": "Sample size"}
    tabs = st.tabs([labels.get(e.get("experiment_id"), e.get("title", "Experiment")) for e in experiments])
    for i, (tab, exp, frame) in enumerate(zip(tabs, experiments, frames)):
        with tab:
            if frame.empty or "protocol" not in frame:
                st.info("No records in this scenario.")
                continue
            df = frame[frame.protocol.isin(selected)].copy()
            if df.empty:
                st.info("No results for the selected protocols.")
                continue
            eid = exp.get("experiment_id", str(i))
            key = f"benchmark_{i}"
            controls = exp.get("control_variables", {})
            st.caption("Fixed settings: " + " · ".join(f"{k.replace('_', ' ')}: {v}" for k, v in controls.items()))
            if eid == "exp4_mitm_authentication":
                authentication(df, key)
            else:
                x, xlabel, question = {
                    "exp1_baseline_scaling": ("num_qubits", "Reported signals / E91 pairs", "How does output change as the transmission size grows?"),
                    "exp2_noise_tolerance": ("noise_level", "Configured channel noise", "How does channel noise affect errors and accepted output?"),
                    "exp3_intercept_resend": ("eve_intensity", "Intercepted fraction (0–1)", "How does increasing interception affect the protocols?"),
                    "exp5_statistical_stability": ("num_qubits", "Reported signals / E91 pairs", "How do outcomes change with more signals per run?")
                }.get(eid, (exp.get("independent_variable", "num_qubits"), "Experiment setting", exp.get("description", "Compare the results.")))
                st.write(f"**Question:** {question}")
                left, right = st.columns(2)
                with left:
                    if eid == "exp1_baseline_scaling":
                        plot(df, x, "sifting_yield_pct_mean", "Sifted yield", xlabel, "Sifted yield (%)", key+"sift",
                             ("sifting_yield_pct_ci95_lower", "sifting_yield_pct_ci95_upper"))
                    else:
                        plot(df, x, "qber_pct_mean", "Observed errors", xlabel, "QBER (%)", key+"qber",
                             ("qber_pct_ci95_lower", "qber_pct_ci95_upper"))
                with right:
                    plot(df, x, "key_yield_per_pulse_mean", "Reported output yield", xlabel, "Output bits per pulse / pair", key+"yield",
                         ("key_yield_ci95_lower", "key_yield_ci95_upper"))
                if eid == "exp1_baseline_scaling":
                    st.caption("E91 uses one of nine setting combinations for key extraction here. Its denominator is "
                               "an entangled pair; BB84 and B92 use individual signals. This is not an equal-photon-cost comparison.")
                else:
                    st.caption("Higher QBER means more observed bit errors. A higher abort rate means fewer runs accepted "
                               "a key; under noise alone, abortion is not evidence of an attacker.")
                with st.expander("More detail: abortion, runtime and Bell test"):
                    plot(df, x, "abort_rate_pct", "Aborted runs", xlabel, "Runs aborted (%)", key+"abort")
                    plot(df, x, "simulator_runtime_ms_mean", "Simulator runtime", xlabel, "Runtime (ms)", key+"time")
                    e91 = df[df.protocol == "E91"]
                    if not e91.empty:
                        plot(e91, x, "bell_parameter_s_mean", "E91 Bell parameter", xlabel, "Mean S", key+"bell",
                             ("bell_parameter_s_ci95_lower", "bell_parameter_s_ci95_upper"), reference=2)
                        st.caption("The dashed line is S = 2 (the positive-branch Bell reference). Actual decisions "
                                   "may use |S| and per-trial values. An average above 2 is not a full security proof.")
            tables(df, key)
    with st.expander("How to read these results"):
        st.markdown("""
- **Sifted yield:** bits retained after the protocol's measurement-setting selection.
- **QBER:** fraction of compared bits that differ. N/A means no applicable comparison.
- **Output yield:** reported final bits divided by transmitted pulses or pairs. Interpret this according to the benchmark's post-processing model.
- **Abort rate:** fraction of runs that rejected the key. **Compromise rate:** fraction marked as attacker success.
- **Confidence interval:** uncertainty in the estimated mean over repeated trials. Zero observed errors do not prove a zero underlying error probability.

The configured noise parameter is not the same as QBER or channel loss. Larger trials, disclosed-bit removal,
error correction and privacy amplification must be documented before treating reported output as a secure key.
        """)
    with st.expander("Run metadata and complete report"):
        st.json(env)
        st.download_button("Download full benchmark JSON", content, file_name=selected_file.name,
                           mime="application/json", key="benchmark_full_download")
