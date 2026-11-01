"""
Standardized Data Models and Schema for QKD Protocol Benchmarks.
Provides rigorous scientific metrics including finite-key accounting,
Standard Errors (SE), 95% Confidence Intervals (CI), and strict separation
of abort vs. compromise security outcomes.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
import json
import numpy as np


def sanitize_value(val: Any) -> Any:
    """Recursively converts numpy and custom types to native JSON-serializable types."""
    if isinstance(val, (np.floating, float)):
        return round(float(val), 4) if not np.isnan(val) else None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, np.ndarray):
        return [sanitize_value(x) for x in val.tolist()]
    if isinstance(val, dict):
        return {str(k): sanitize_value(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [sanitize_value(x) for x in val]
    return val


def compute_mean_se_ci(values: List[Optional[float]], confidence_multiplier: float = 1.96) -> Dict[str, Optional[float]]:
    """
    Computes sample mean, sample standard deviation, standard error, and 95% confidence intervals.
    Filters out None and NaN values.
    """
    valid = [float(v) for v in values if v is not None and not np.isnan(v)]
    if not valid:
        return {
            "mean": None,
            "std": None,
            "se": None,
            "ci95_lower": None,
            "ci95_upper": None,
            "min": None,
            "max": None
        }
    
    n = len(valid)
    mean_val = float(np.mean(valid))
    min_val = float(np.min(valid))
    max_val = float(np.max(valid))

    if n > 1:
        std_val = float(np.std(valid, ddof=1))
        se_val = float(std_val / np.sqrt(n))
        ci_lower = float(mean_val - confidence_multiplier * se_val)
        ci_upper = float(mean_val + confidence_multiplier * se_val)
    else:
        std_val = 0.0
        se_val = 0.0
        ci_lower = mean_val
        ci_upper = mean_val

    return {
        "mean": mean_val,
        "std": std_val,
        "se": se_val,
        "ci95_lower": ci_lower,
        "ci95_upper": ci_upper,
        "min": min_val,
        "max": max_val
    }


@dataclass
class TrialRecord:
    """Individual trial run for a single configuration."""
    trial_id: int
    protocol: str
    num_qubits: int                         # Pulses / Bell pairs transmitted
    noise_level: float
    attack_type: str
    eve_intensity: float

    # Pulse / Pair Accounting
    n_transmitted: int                      # Physical pulses / pairs emitted
    n_sifted: int                           # Raw sifted key length
    n_check_bits: Optional[int]             # Bits sampled for QBER estimation
    n_chsh_pairs: Optional[int]             # Pairs measured for Bell test (E91)
    sifting_yield_pct: float                # n_sifted / n_transmitted * 100

    # Error Rates & Key Distillation
    error_count: int
    qber_pct: Optional[float]               # None if no check bits compared
    n_final_key: int                        # Strict: 0 if session aborted or compromised
    key_yield_per_pulse: float              # n_final_key / n_transmitted
    
    # Security State
    security_verdict: str                   # "SECURE", "WARNING", "ABORTED", "MITM_COMPROMISED", "AUTH_REJECTED"
    is_aborted: bool                        # True if session stopped before key usage
    is_compromised: bool                    # True if Eve obtained key unnoticed
    simulator_runtime_ms: float

    # Protocol-Specific Metrics
    conclusive_detection_pct: Optional[float] = None  # B92 USD rate
    bell_parameter_s: Optional[float] = None          # E91 CHSH S
    bell_violated: Optional[bool] = None             # E91 |S| > 2.0

    # MitM-Specific Metrics
    use_authentication: Optional[bool] = None
    auth_status: Optional[str] = None                 # "VERIFIED", "REJECTED", "DISABLED"
    alice_eve_qber_pct: Optional[float] = None
    eve_bob_qber_pct: Optional[float] = None
    alice_bob_key_mismatch_pct: Optional[float] = None
    eve_knowledge_pct: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return sanitize_value(asdict(self))


@dataclass
class AggregatedRecord:
    """
    Statistical aggregate across N independent Monte Carlo trials for a specific parameter configuration.
    Includes Mean, Standard Error (SE), and 95% Confidence Intervals.
    """
    protocol: str
    num_qubits: int
    noise_level: float
    attack_type: str
    eve_intensity: float
    trial_count: int

    # Yield & Sifting Statistics
    n_sifted_mean: float
    n_sifted_se: float
    sifting_yield_pct_mean: float
    sifting_yield_pct_se: float
    sifting_yield_pct_ci95_lower: Optional[float]
    sifting_yield_pct_ci95_upper: Optional[float]

    # Sample Accounting Means
    n_check_bits_mean: Optional[float]
    n_chsh_pairs_mean: Optional[float]

    # Error Rates with Confidence Intervals
    error_count_mean: float
    qber_pct_mean: Optional[float]
    qber_pct_se: Optional[float]
    qber_pct_ci95_lower: Optional[float]
    qber_pct_ci95_upper: Optional[float]
    qber_pct_min: Optional[float]
    qber_pct_max: Optional[float]

    # Key Distillation (Strict zero on abort/compromise)
    n_final_key_mean: float
    n_final_key_se: float
    key_yield_per_pulse_mean: float
    key_yield_per_pulse_se: float
    key_yield_ci95_lower: Optional[float]
    key_yield_ci95_upper: Optional[float]

    # Simulator Performance
    simulator_runtime_ms_mean: float
    simulator_runtime_ms_se: float

    # Discrete Security Breakdown
    secure_count: int
    warning_count: int
    aborted_count: int
    compromised_count: int
    abort_rate_pct: float                   # % of runs safely aborted
    compromise_rate_pct: float              # % of runs successfully hijacked by Eve

    # Protocol-Specific Aggregates
    conclusive_detection_pct_mean: Optional[float] = None
    conclusive_detection_pct_se: Optional[float] = None

    bell_parameter_s_mean: Optional[float] = None
    bell_parameter_s_se: Optional[float] = None
    bell_parameter_s_ci95_lower: Optional[float] = None
    bell_parameter_s_ci95_upper: Optional[float] = None
    bell_violation_rate_pct: Optional[float] = None

    # MitM-Specific Aggregates
    use_authentication: Optional[bool] = None
    auth_status: Optional[str] = None
    auth_pass_rate_pct: Optional[float] = None
    alice_eve_qber_pct_mean: Optional[float] = None
    eve_bob_qber_pct_mean: Optional[float] = None
    alice_bob_mismatch_pct_mean: Optional[float] = None
    alice_bob_mismatch_pct_se: Optional[float] = None
    eve_knowledge_pct_mean: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return sanitize_value(asdict(self))


@dataclass
class ExperimentResult:
    """Results container for a single controlled experiment."""
    experiment_id: str
    title: str
    description: str
    independent_variable: str
    control_variables: Dict[str, Any]
    aggregated_records: List[AggregatedRecord] = field(default_factory=list)
    raw_trials: List[TrialRecord] = field(default_factory=list)

    def to_dict(self, include_raw_trials: bool = False) -> Dict[str, Any]:
        data = {
            "experiment_id": self.experiment_id,
            "title": self.title,
            "description": self.description,
            "independent_variable": self.independent_variable,
            "control_variables": self.control_variables,
            "total_configurations": len(self.aggregated_records),
            "records": [r.to_dict() for r in self.aggregated_records]
        }
        if include_raw_trials:
            data["raw_trials"] = [t.to_dict() for t in self.raw_trials]
        return sanitize_value(data)


@dataclass
class BenchmarkRun:
    """Top-level container for an entire benchmark execution run."""
    run_id: str
    timestamp: str
    environment: Dict[str, Any]
    experiments: List[ExperimentResult] = field(default_factory=list)
    scorecard: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self, include_raw_trials: bool = False) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "environment": self.environment,
            "experiments": [e.to_dict(include_raw_trials) for e in self.experiments],
            "scorecard": [sanitize_value(item) for item in self.scorecard]
        }

    def to_json(self, indent: int = 2, include_raw_trials: bool = False) -> str:
        return json.dumps(self.to_dict(include_raw_trials), indent=indent)
