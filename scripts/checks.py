"""Run input checks and unit tests, saving the actual command output as UTF-8."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


if __name__ == '__main__':
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'.runtime/matplotlib'))
    os.environ.setdefault('NUMBA_CACHE_DIR', str(ROOT/'.runtime/numba'))
    for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS']:
        os.environ.setdefault(key, '1')
    (ROOT/'reports').mkdir(exist_ok=True)
    commands = [[sys.executable, '-O', str(ROOT/'scripts/validate_data.py')],
                [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']]
    failed = False
    with (ROOT/'reports/test_results.txt').open('w', encoding='utf-8') as log:
        for command in commands:
            result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding='utf-8', errors='replace')
            log.write(f'COMMAND: {command!r}\nRETURN CODE: {result.returncode}\n{result.stdout}\n')
            print(result.stdout)
            failed |= result.returncode != 0
    sys.exit(int(failed))
