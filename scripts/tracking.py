"""Local-first runs. Exclusive directory reservation; serialized, atomic CSV registry."""
import contextlib
import csv
import hashlib
import io
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
import traceback
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['run_id', 'status', 'started_utc', 'ended_utc', 'experiment', 'purpose',
          'git_commit', 'git_dirty', 'runtime_seconds', 'artifact_path', 'error']


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    os.replace(tmp, path)


@contextlib.contextmanager
def registry_lock(base, timeout=15):
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    lock = base / '.registry.lock'
    start = time.monotonic()
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f'{os.getpid()} {utc()}'.encode())
            os.close(fd)
            break
        except (FileExistsError, PermissionError):
            # Windows can return ACCESS_DENIED while another owner closes/unlinks.
            if time.monotonic() - start > timeout:
                raise TimeoutError(f'Registry locked: {lock}; inspect owner before manual recovery')
            time.sleep(0.05)
    try:
        yield
    finally:
        lock.unlink()


def register(base, record, *, finalization_recovery=False):
    base = Path(base)
    with registry_lock(base):
        path = base / 'registry.csv'
        records = []
        if path.exists():
            with path.open(encoding='utf-8', newline='') as stream:
                records = list(csv.DictReader(stream))
        if record.get('status') not in {'running', 'completed', 'failed'}:
            raise ValueError('Invalid registry status')
        matches = [r for r in records if r['run_id'] == record['run_id']]
        if matches:
            transition = matches[0]['status'] == 'running' and record['status'] in {'completed', 'failed'}
            recovery = (finalization_recovery and matches[0]['status'] == 'completed' and
                        record['status'] == 'failed' and
                        not (base/'runs'/record['run_id']/'COMPLETED').exists())
            if not (transition or recovery):
                raise FileExistsError('Registry run ID already used or finalized')
        records = [r for r in records if r['run_id'] != record['run_id']]
        records.append({k: record.get(k, '') for k in FIELDS})
        buf = io.StringIO(newline='')
        writer = csv.DictWriter(buf, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
        tmp = base / ('registry.' + uuid.uuid4().hex + '.tmp')
        tmp.write_text(buf.getvalue(), encoding='utf-8', newline='')
        os.replace(tmp, path)


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True, encoding='utf-8')


def checksums(out):
    return {p.relative_to(out).as_posix(): digest(p) for p in sorted(out.rglob('*'))
            if p.is_file() and p.relative_to(out).as_posix() not in {'artifact_checksums.json', 'COMPLETED'}}


def verify(out):
    out = Path(out)
    expected = json.loads((out / 'artifact_checksums.json').read_text(encoding='utf-8'))
    actual = checksums(out)
    if actual != expected:
        raise ValueError('Artifact manifest mismatch (missing, changed or unexpected files)')
    return len(expected)


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            stream.write(text)
            stream.flush()
        return len(text)

    def flush(self):
        for stream in self.streams:
            stream.flush()


class Run:
    def __init__(self, base, config, experiment, purpose, run_id=None):
        self.base = Path(base).resolve()
        run_id = run_id or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:12]
        if Path(run_id).name != run_id or run_id in {'.', '..'} or '/' in run_id or '\\' in run_id:
            raise ValueError('run_id must be a single directory name')
        self.out = self.base / 'runs' / run_id
        self.out.mkdir(parents=True, exist_ok=False)
        self.started = time.monotonic()
        self.meta = dict(run_id=run_id, status='running', started_utc=utc(), ended_utc=None,
                         experiment=experiment, purpose=purpose, artifact_path=self.out.relative_to(self.base).as_posix(),
                         exact_command=[sys.executable, *sys.argv], cwd=str(Path.cwd()),
                         resolved_configuration=config, python=sys.version, platform=platform.platform(),
                         thread_environment={k: os.environ.get(k) for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS']})

    def __enter__(self):
        # Initial state is persisted before metadata, imports or input validation can fail.
        write_json(self.out / 'status.json', self.meta)
        register(self.base, self.meta)
        self.log = (self.out / 'run.log').open('w', encoding='utf-8')
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(contextlib.redirect_stdout(Tee(sys.stdout, self.log)))
        self.stack.enter_context(contextlib.redirect_stderr(Tee(sys.stderr, self.log)))
        return self

    def provenance(self):
        self.meta['versions'] = {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}
        self.meta.update(git_commit=git('rev-parse', 'HEAD').strip(),
                         git_dirty=bool(git('status', '--porcelain', '--untracked-files=normal')))
        (self.out / 'worktree.patch').write_text(git('diff', '--binary', 'HEAD'), encoding='utf-8')
        # Includes untracked implementation files, excludes result trees, caches and credentials.
        paths = []
        for folder in ['scripts', 'tests', 'configs', 'docs', 'data', '.github']:
            paths += [p for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
        paths += [ROOT / p for p in ['README.md', 'requirements.txt', '.gitignore']]
        with zipfile.ZipFile(self.out / 'source_snapshot.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            for p in sorted(paths):
                archive.write(p, p.relative_to(ROOT).as_posix())
        self.meta['input_sha256'] = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted((ROOT/'data').rglob('*')) if p.is_file()}
        self.meta['input_sha256']['docs/Top40_Retrospective_Model_Method_v1.json'] = digest(ROOT/'docs/Top40_Retrospective_Model_Method_v1.json')
        write_json(self.out / 'resolved_config.json', self.meta['resolved_configuration'])
        write_json(self.out / 'status.json', self.meta)

    def __exit__(self, kind, value, tb):
        if kind:
            traceback.print_exception(kind, value, tb)
        self.stack.close()
        self.log.close()
        self.meta.update(status='failed' if kind else 'completed', ended_utc=utc(),
                         runtime_seconds=time.monotonic()-self.started,
                         error=str(value) if kind else '')
        try:
            write_json(self.out / 'status.json', self.meta)
            write_json(self.out / 'artifact_checksums.json', checksums(self.out))
            verify(self.out)
            register(self.base, self.meta)
            if not kind:
                # The marker commits the completed state after outputs and registry succeed.
                (self.out / 'COMPLETED').write_text(digest(self.out/'artifact_checksums.json')+'\n', encoding='utf-8')
        except Exception as error:
            self.meta.update(status='failed', error=f'Finalization failed: {error}')
            (self.out/'finalization_error.txt').write_text(traceback.format_exc(), encoding='utf-8')
            try:
                register(self.base, self.meta, finalization_recovery=True)
            except Exception as registry_error:
                # A locked/corrupt registry must not conceal local failure evidence.
                self.meta['registry_error'] = str(registry_error)
            write_json(self.out/'status.json', self.meta)
            write_json(self.out/'artifact_checksums.json', checksums(self.out))
            raise
        return False
