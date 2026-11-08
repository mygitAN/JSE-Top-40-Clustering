"""Run the full paper workflow in order. Same functions as the guided notebook."""
import argparse
from study_workflow import StudySession


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id')
    parser.add_argument('--output', help='Registry root; each execution reserves a unique runs/<ID> directory')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--stability-runs', type=int, default=5)
    parser.add_argument('--baseline-only', action='store_true', help='Omit the additional UMAP sensitivity; retain all nine baseline comparisons')
    args = parser.parse_args()
    study = StudySession(run_id=args.run_id, output=args.output, seed=args.seed,
                         stability_runs=args.stability_runs, include_umap=not args.baseline_only)
    study.load_data()
    study.explore()
    study.fit_models()
    study.explain_clusters()
    study.compare_dates()
    study.finish()


if __name__ == '__main__':
    main()
