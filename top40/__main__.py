"""Run the whole study from the command line: ``python -m top40``."""
import argparse

from .features import FEATURE_SETS
from .study import run_all


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feature-set', choices=sorted(FEATURE_SETS), help='Default: the one in configs/study.json')
    parser.add_argument('--run-id', help='Default: a unique timestamped id')
    parser.add_argument('--output', help='Registry root; the run is written to <output>/runs/<run-id>')
    parser.add_argument('--seed', type=int)
    parser.add_argument('--stability-runs', type=int)
    args = parser.parse_args()
    run_all(feature_set=args.feature_set, run_id=args.run_id, output=args.output, seed=args.seed,
            stability_runs=args.stability_runs)


if __name__ == '__main__':
    main()
