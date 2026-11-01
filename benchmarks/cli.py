"""
Command-Line Interface (CLI) Runner for QKD Protocol Benchmarks.
Usage:
    python -m benchmarks.cli --help
    python -m benchmarks.cli --experiment all --quick
    python -m benchmarks.cli --experiment noise --trials 5 --output-dir my_results
"""
import sys
import os
import argparse
import datetime
import time

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import qiskit
from benchmarks.data_models import BenchmarkRun, ExperimentResult
from benchmarks.experiments import BenchmarkSuite
from benchmarks.data_exporter import DataExporter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Quantum Key Distribution (QKD) Protocol Benchmark & Comparative Analysis Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all 5 experiments with default settings
  python -m benchmarks.cli --experiment all

  # Quick sanity dry-run with compact parameter sweeps
  python -m benchmarks.cli --quick

  # Run only noise tolerance sweep with 10 trials per point
  python -m benchmarks.cli --experiment noise --trials 10

  # Run only Man-in-the-Middle authentication evaluation
  python -m benchmarks.cli --experiment mitm
        """
    )

    parser.add_argument(
        "-e", "--experiment",
        type=str,
        default="all",
        choices=["all", "baseline", "noise", "intercept", "mitm", "stability", "exp1", "exp2", "exp3", "exp4", "exp5"],
        help="Specific experiment to run, or 'all' to execute the complete benchmark suite."
    )

    parser.add_argument(
        "-t", "--trials",
        type=int,
        default=30,
        help="Number of independent Monte Carlo trials per parameter configuration (default: 30)."
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="benchmark_results",
        help="Directory to save generated JSON and CSV benchmark reports (default: 'benchmark_results')."
    )

    parser.add_argument(
        "-q", "--quick",
        action="store_true",
        help="Fast sanity mode: uses compact parameter grids and 5 trials per point."
    )

    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=42,
        help="Master random seed for reproducible benchmark execution (default: 42)."
    )

    parser.add_argument(
        "--format",
        type=str,
        default="both",
        choices=["both", "json", "csv"],
        help="Output serialization format (default: 'both')."
    )

    parser.add_argument(
        "--no-raw",
        action="store_true",
        help="Exclude raw trial-level rows from exported JSON/CSV (only keep aggregated metrics)."
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Normalize experiment aliases
    exp_target = args.experiment.lower()
    if exp_target in ["exp1", "baseline"]:
        run_targets = ["baseline"]
    elif exp_target in ["exp2", "noise"]:
        run_targets = ["noise"]
    elif exp_target in ["exp3", "intercept"]:
        run_targets = ["intercept"]
    elif exp_target in ["exp4", "mitm"]:
        run_targets = ["mitm"]
    elif exp_target in ["exp5", "stability"]:
        run_targets = ["stability"]
    else:
        run_targets = ["baseline", "noise", "intercept", "mitm", "stability"]

    trials = 5 if args.quick else args.trials
    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\n" + "=" * 70)
    print("[QKD] QUANTUM KEY DISTRIBUTION BENCHMARK SUITE")
    print("=" * 70)
    print(f"* Run ID:           {run_id}")
    print(f"* Target Suite(s):  {', '.join(run_targets).upper()}")
    print(f"* Trials Per Point: {trials} {'(Quick Mode: 5 trials)' if args.quick else ''}")
    print(f"* Output Directory: {os.path.abspath(args.output_dir)}")
    print(f"* Quantum Engine:   Qiskit AerSimulator (MPS backend) v{qiskit.__version__}")
    print(f"* Master Seed:      {args.seed}")
    print("=" * 70 + "\n")

    suite = BenchmarkSuite(rng_seed=args.seed)
    completed_experiments = []
    total_t0 = time.perf_counter()

    # Experiment 1: Baseline Scaling
    if "baseline" in run_targets:
        print("[1/5] Running Experiment 1: Baseline Efficiency & Key Scaling...")
        qubit_counts = [24, 48, 96] if args.quick else [48, 96, 144, 192, 240]
        t0 = time.perf_counter()
        exp1 = suite.run_experiment_1_baseline_scaling(
            qubit_counts=qubit_counts,
            trials_per_point=trials,
            base_seed=args.seed
        )
        elapsed = time.perf_counter() - t0
        print(f"      -> Completed in {elapsed:.2f}s ({len(exp1.aggregated_records)} configurations evaluated)")
        completed_experiments.append(exp1)

    # Experiment 2: Noise Tolerance
    if "noise" in run_targets:
        print("[2/5] Running Experiment 2: Depolarizing Noise Tolerance & Abort Thresholds...")
        noise_levels = [0.0, 0.04, 0.08, 0.12] if args.quick else [0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16]
        num_qubits = 72 if args.quick else 144
        t0 = time.perf_counter()
        exp2 = suite.run_experiment_2_noise_tolerance(
            noise_levels=noise_levels,
            num_qubits=num_qubits,
            trials_per_point=trials,
            base_seed=args.seed + 100
        )
        elapsed = time.perf_counter() - t0
        print(f"      -> Completed in {elapsed:.2f}s ({len(exp2.aggregated_records)} configurations evaluated)")
        completed_experiments.append(exp2)

    # Experiment 3: Intercept-Resend Eavesdropping
    if "intercept" in run_targets:
        print("[3/5] Running Experiment 3: Intercept-Resend Eavesdropping Sensitivity...")
        eve_intensities = [0.0, 0.25, 0.50, 1.0] if args.quick else [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0]
        num_qubits = 72 if args.quick else 144
        t0 = time.perf_counter()
        exp3 = suite.run_experiment_3_intercept_resend(
            eve_intensities=eve_intensities,
            num_qubits=num_qubits,
            noise_level=0.02,
            trials_per_point=trials,
            base_seed=args.seed + 200
        )
        elapsed = time.perf_counter() - t0
        print(f"      -> Completed in {elapsed:.2f}s ({len(exp3.aggregated_records)} configurations evaluated)")
        completed_experiments.append(exp3)

    # Experiment 4: Man-in-the-Middle Attack
    if "mitm" in run_targets:
        print("[4/5] Running Experiment 4: Man-in-the-Middle (MitM) & Classical Authentication...")
        num_qubits = 48 if args.quick else 72
        t0 = time.perf_counter()
        exp4 = suite.run_experiment_4_mitm_authentication(
            num_qubits=num_qubits,
            noise_level=0.0,
            trials_per_point=trials,
            base_seed=args.seed + 300
        )
        elapsed = time.perf_counter() - t0
        print(f"      -> Completed in {elapsed:.2f}s ({len(exp4.aggregated_records)} configurations evaluated)")
        completed_experiments.append(exp4)

    # Experiment 5: Finite-Key Stability
    if "stability" in run_targets:
        print("[5/5] Running Experiment 5: Finite-Key Statistical Convergence & Stability...")
        qubit_sizes = [24, 48, 96] if args.quick else [24, 48, 96, 144, 216]
        t0 = time.perf_counter()
        exp5 = suite.run_experiment_5_statistical_stability(
            qubit_sizes=qubit_sizes,
            noise_level=0.03,
            trials_per_size=trials,
            base_seed=args.seed + 400
        )
        elapsed = time.perf_counter() - t0
        print(f"      -> Completed in {elapsed:.2f}s ({len(exp5.aggregated_records)} configurations evaluated)")
        completed_experiments.append(exp5)

    total_time = time.perf_counter() - total_t0

    # Generate Scorecard Summary
    scorecard = suite.generate_scorecard(completed_experiments)

    # Compile Top-Level BenchmarkRun
    benchmark_run = BenchmarkRun(
        run_id=run_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        environment={
            "qiskit_version": qiskit.__version__,
            "python_version": sys.version.split(" ")[0],
            "simulator_backend": "AerSimulator",
            "simulation_method": "matrix_product_state",
            "total_runtime_seconds": round(total_time, 2),
            "trials_per_point": trials,
            "quick_mode": args.quick,
            "master_seed": args.seed
        },
        experiments=completed_experiments,
        scorecard=scorecard
    )

    # Export to Files
    exporter = DataExporter(output_dir=args.output_dir)
    save_json = args.format in ["both", "json"]
    save_csv = args.format in ["both", "csv"]
    exported = exporter.export_all(
        benchmark_run=benchmark_run,
        save_json=save_json,
        save_csv=save_csv,
        include_raw_trials=not args.no_raw
    )

    print("\n" + "=" * 70)
    print("[SUCCESS] BENCHMARK RUN COMPLETE")
    print("=" * 70)
    print(f"Total Execution Time: {total_time:.2f} seconds")
    print("Generated Artifacts:")
    for key, path in exported.items():
        print(f"  * {key:22s} -> {path}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
