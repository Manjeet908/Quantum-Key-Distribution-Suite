"""
Data Exporter for QKD Benchmark Results.
Serializes structured BenchmarkRun objects into standard JSON and CSV files.
"""
import os
import csv
import json
from typing import Dict, Any, List
import pandas as pd

from benchmarks.data_models import BenchmarkRun, ExperimentResult, AggregatedRecord, TrialRecord


class DataExporter:
    """Exports benchmark execution results to JSON and standard CSV files."""

    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def export_all(
        self,
        benchmark_run: BenchmarkRun,
        save_json: bool = True,
        save_csv: bool = True,
        include_raw_trials: bool = True
    ) -> Dict[str, str]:
        """
        Exports the entire benchmark run into JSON and CSV files.
        Returns a dictionary of generated file paths.
        """
        generated_files = {}

        # 1. Master JSON export
        if save_json:
            json_filename = f"benchmark_run_{benchmark_run.run_id}.json"
            json_path = os.path.join(self.output_dir, json_filename)
            master_json_path = os.path.join(self.output_dir, "benchmark_summary.json")

            json_content = benchmark_run.to_json(indent=2, include_raw_trials=include_raw_trials)
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(json_content)
            # Also write to standard "benchmark_summary.json" for predictable consumption
            with open(master_json_path, "w", encoding="utf-8") as f:
                f.write(json_content)

            generated_files["master_json"] = master_json_path
            generated_files["run_json"] = json_path

        # 2. Experiment CSV exports
        if save_csv:
            # Scorecard CSV
            if benchmark_run.scorecard:
                scorecard_path = os.path.join(self.output_dir, "summary_scorecard.csv")
                df_scorecard = pd.DataFrame(benchmark_run.scorecard)
                df_scorecard.to_csv(scorecard_path, index=False)
                generated_files["scorecard_csv"] = scorecard_path

            # Individual Experiment CSVs
            for exp in benchmark_run.experiments:
                exp_records = [r.to_dict() for r in exp.aggregated_records]
                if exp_records:
                    exp_csv_path = os.path.join(self.output_dir, f"{exp.experiment_id}.csv")
                    df_exp = pd.DataFrame(exp_records)
                    df_exp.to_csv(exp_csv_path, index=False)
                    generated_files[f"{exp.experiment_id}_csv"] = exp_csv_path

            # All Raw Trials CSV (for deep regression / scatter analysis)
            if include_raw_trials:
                all_trials: List[Dict[str, Any]] = []
                for exp in benchmark_run.experiments:
                    for t in exp.raw_trials:
                        t_dict = t.to_dict()
                        t_dict["experiment_id"] = exp.experiment_id
                        all_trials.append(t_dict)
                if all_trials:
                    raw_trials_path = os.path.join(self.output_dir, "all_raw_trials.csv")
                    df_trials = pd.DataFrame(all_trials)
                    df_trials.to_csv(raw_trials_path, index=False)
                    generated_files["raw_trials_csv"] = raw_trials_path

        return generated_files
