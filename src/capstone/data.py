"""Download the public sample from Zenodo by DOI, check every byte, and load it.

The sample is "Tennis Point-by-Point Dataset (Public Sample)" by Live Tennis API, concept DOI
10.5281/zenodo.22048730. This loader is pinned to version 1.0.3 (DOI 10.5281/zenodo.23718893),
so every student in a class works on the same files. Each file is checked three ways before it
is used: its size, the MD5 checksum Zenodo publishes, and a SHA-256 checksum pinned below.

The data is under CC BY-NC 4.0, not under this repository's MIT licence. It is downloaded into
data/ at the root of this repository and never committed. Set CAPSTONE_DATA_DIR to use another
folder, for example on Colab.

Run it from the repository root:

    python -m capstone.data            # download and check the three files
    python -m capstone.data --check    # check files already downloaded, without the network
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

#: The concept DOI names every version of the record. The version DOI names one of them.
CONCEPT_DOI = '10.5281/zenodo.22048730'
VERSION_DOI = '10.5281/zenodo.23718893'
VERSION = '1.0.3'
LICENCE = 'CC BY-NC 4.0'
LICENCE_URL = 'https://creativecommons.org/licenses/by-nc/4.0/'
ZENODO_API = 'https://zenodo.org/api/records/'


def _default_dir() -> Path:
    """CAPSTONE_DATA_DIR if set. Otherwise data/ at the repository root when the package runs
    from a clone (pip install -e), or data/ in the current folder when it was installed."""
    if os.environ.get('CAPSTONE_DATA_DIR'):
        return Path(os.environ['CAPSTONE_DATA_DIR']).expanduser()
    root = Path(__file__).resolve().parents[2]
    if (root / 'pyproject.toml').is_file():
        return root / 'data'
    return Path.cwd() / 'data'


DEFAULT_DIR = _default_dir()
USER_AGENT = 'tennis-capstone-starter/1.0'
TIMEOUT = 60


@dataclass(frozen=True)
class DataFile:
    name: str
    size: int
    md5: str
    sha256: str


#: The three data files of version 1.0.3, as the record lists them on Zenodo. The SHA-256
#: values were computed from the files downloaded from that record.
FILES = (
    DataFile('matches.csv.gz', 2430730, '0bf47dc8cd7d359621fa2e117ab932f7',
             '1a93740f6ed2c835b2097f631c06c6471af9733dcfd699fdd758df71165d0c1c'),
    DataFile('players.csv.gz', 420351, '92d3a7a6cc075da402668733a21a0709',
             '6fa1f3fd7b40e59d43fd79c66b3e0f4922f8873b799bad139f3177950637efa1'),
    DataFile('points_sample_2026-06.csv.gz', 9377769, 'cd484a2d728e3f8c3eb338576e9707bf',
             'ebcf0d542685027b56cba13682420e01a37c618c46504824d84fc634927332bb'),
)


class DataError(RuntimeError):
    """A file is missing, the record is not the pinned one, or a checksum does not match."""


def record_url(doi: str) -> str:
    """The Zenodo API address of a Zenodo DOI. Zenodo DOIs end in the record number."""
    prefix = '10.5281/zenodo.'
    if not doi.startswith(prefix) or not doi[len(prefix):].isdigit():
        raise DataError(f'{doi!r} is not a Zenodo DOI')
    return ZENODO_API + doi[len(prefix):]


class _HttpsOnlyRedirects(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only to another https address. The checksums guard the bytes, and
    this keeps the request itself off plain http."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith('https://'):
            raise DataError(f'refusing a redirect to {newurl}')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_HttpsOnlyRedirects)


def _get(url: str):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    return _OPENER.open(req, timeout=TIMEOUT)


def fetch_record(doi: str = VERSION_DOI) -> dict:
    """The record's metadata from the Zenodo API, checked against the pinned version."""
    with _get(record_url(doi)) as resp:
        record = json.load(resp)
    if record.get('doi') != VERSION_DOI or record.get('conceptdoi') != CONCEPT_DOI:
        raise DataError(
            f'Zenodo answered with {record.get("doi")!r}, not version {VERSION} '
            f'({VERSION_DOI}). This loader only accepts the pinned version.')
    listed = {f['key']: f for f in record.get('files', [])}
    for f in FILES:
        entry = listed.get(f.name)
        if entry is None:
            raise DataError(f'the record does not list {f.name}')
        if entry.get('checksum') != 'md5:' + f.md5 or entry.get('size') != f.size:
            raise DataError(f'the record lists {f.name} with a different size or checksum')
    return record


def _digests(path: Path) -> tuple[int, str, str]:
    md5, sha = hashlib.md5(usedforsecurity=False), hashlib.sha256()
    size = 0
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            size += len(chunk)
            md5.update(chunk)
            sha.update(chunk)
    return size, md5.hexdigest(), sha.hexdigest()


def verify(path: Path, expected: DataFile) -> None:
    """Raise DataError unless the file at `path` is byte for byte the pinned file."""
    if not path.is_file():
        raise DataError(f'{path} is missing. Run: python -m capstone.data')
    size, md5, sha = _digests(path)
    if size != expected.size:
        raise DataError(f'{path.name} has {size} bytes, expected {expected.size}')
    if md5 != expected.md5:
        raise DataError(f'{path.name} has MD5 {md5}, expected {expected.md5}')
    if sha != expected.sha256:
        raise DataError(f'{path.name} has SHA-256 {sha}, expected {expected.sha256}')


def _download(url: str, dest: Path, expected: DataFile) -> None:
    if not url.startswith('https://zenodo.org/'):
        raise DataError(f'refusing to download {expected.name} from {url}')
    fd, name = tempfile.mkstemp(prefix=dest.name + '.', suffix='.part', dir=dest.parent)
    part = Path(name)
    try:
        with os.fdopen(fd, 'wb') as out, _get(url) as resp:
            for chunk in iter(lambda: resp.read(1 << 20), b''):
                out.write(chunk)
        verify(part, expected)
        os.replace(part, dest)
    finally:
        part.unlink(missing_ok=True)


def download(data_dir: Path | str = DEFAULT_DIR, *, log=print) -> Path:
    """Download any file that is missing or wrong, check them all, and return the folder."""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    record = None
    for f in FILES:
        path = data_dir / f.name
        try:
            verify(path, f)
            log(f'{f.name}: already here, checksums match')
            continue
        except DataError:
            pass
        if record is None:
            record = fetch_record()
        links = {e['key']: e['links']['self'] for e in record['files']}
        log(f'{f.name}: downloading {f.size:,} bytes from Zenodo')
        _download(links[f.name], path, f)
        log(f'{f.name}: checksums match')
    return data_dir


def check(data_dir: Path | str = DEFAULT_DIR) -> None:
    """Check the downloaded files without touching the network."""
    for f in FILES:
        verify(Path(data_dir) / f.name, f)


def _read(name: str, data_dir: Path | str, **kwargs):
    import pandas as pd
    path = Path(data_dir) / name
    verify(path, next(f for f in FILES if f.name == name))
    return pd.read_csv(path, **kwargs)


def load_matches(data_dir: Path | str = DEFAULT_DIR):
    """matches.csv.gz as a DataFrame: one row per completed match, 2023-01-01 to 2026-08-13."""
    import pandas as pd
    df = _read('matches.csv.gz', data_dir, low_memory=False,
               dtype={'tournament_key': 'string', 'tier_key': 'string',
                      'is_qualifying': 'string', 'indoor': 'string'})
    df['scheduled_time_utc'] = pd.to_datetime(df['scheduled_time_utc'], format='ISO8601',
                                              utc=True)
    return df


def load_players(data_dir: Path | str = DEFAULT_DIR):
    """players.csv.gz as a DataFrame: one row per player."""
    return _read('players.csv.gz', data_dir, dtype={'birthday': 'string', 'hand': 'string'})


def load_points(data_dir: Path | str = DEFAULT_DIR):
    """points_sample_2026-06.csv.gz as a DataFrame: one row per observed score state.

    The point columns stay text, because a game uses 0, 15, 30, 40, A and AD while a
    tie-break uses counts. games_p1 and games_p2 stay as their JSON text, for example "[6, 4]".
    The rows keep the file's order, which is capture order within each match.
    """
    import pandas as pd
    df = _read('points_sample_2026-06.csv.gz', data_dir,
               dtype={'points_p1': 'string', 'points_p2': 'string', 'server': 'Int8'})
    # ISO8601 because a few timestamps have no fraction of a second, which defeats the
    # single format pandas would otherwise guess.
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], format='ISO8601', utc=True)
    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog='python -m capstone.data',
        description=f'Download the public tennis sample ({VERSION_DOI}) and check it.')
    parser.add_argument('--dir', default=str(DEFAULT_DIR), help='where the files go')
    parser.add_argument('--check', action='store_true',
                        help='check files already downloaded, without the network')
    args = parser.parse_args(argv)
    try:
        if args.check:
            check(args.dir)
            print(f'All {len(FILES)} files match version {VERSION}.')
        else:
            download(args.dir)
            print(f'Done. Data under {LICENCE}: {LICENCE_URL}')
    except (DataError, OSError) as exc:
        # OSError covers no network, a timeout, a dropped connection and a full disk.
        print(f'error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
