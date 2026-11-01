"""
Convenience entry point for running QKD Protocol Benchmarks.
Usage:
    python run_benchmarks.py --quick
    python run_benchmarks.py --experiment all
    python run_benchmarks.py --help
"""
import sys
import os

# Set root directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from benchmarks.cli import main

if __name__ == "__main__":
    main()
