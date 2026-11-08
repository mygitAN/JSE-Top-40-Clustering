"""Validate a saved run's status, completion marker and every artifact checksum."""
import argparse
import json
from pathlib import Path
from tracking import digest, verify


def verify_completed(out):
    out = Path(out)
    count = verify(out)
    status = json.loads((out/'status.json').read_text(encoding='utf-8'))
    if status['status'] != 'completed':
        raise ValueError(f'Run status is {status["status"]}')
    if (out/'COMPLETED').read_text().strip() != digest(out/'artifact_checksums.json'):
        raise ValueError('Completion marker does not match manifest')
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory')
    args = parser.parse_args()
    print(f'PASS: {verify_completed(args.run_directory)} artifacts verified')
