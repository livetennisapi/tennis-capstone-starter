"""The loader, offline. Zenodo is replaced by a fake that serves small files from memory."""
from __future__ import annotations

import gzip
import hashlib
import io
import json

import pytest

from capstone import data

CSV = {
    'matches.csv.gz': 'match_id,player1_id,player2_id,tournament,tournament_key,tier_key,surface,'
                      'indoor,best_of,round,scheduled_time_utc,event_status,is_qualifying\n'
                      '1,10,11,Sample Open,5,265,clay,,BO3,R1,2026-06-01 10:00:00,,False\n',
    'players.csv.gz': 'player_id,name,tour,country,birthday,hand\n10,Player A,atp,aaa,,R\n'
                      '11,Player B,atp,bbb,,L\n',
    'points_sample_2026-06.csv.gz': 'match_id,sets_p1,sets_p2,games_p1,games_p2,points_p1,'
                                    'points_p2,server,is_tiebreak,timestamp_utc\n'
                                    '1,0,0,[0],[0],0,0,1,False,2026-06-01 10:01:00.000001\n'
                                    '1,0,0,[0],[0],15,0,1,False,2026-06-01 10:01:30.000001\n'
                                    '1,0,0,"[6, 6]","[6, 6]",AD,40,,False,'
                                    '2026-06-01 11:01:30\n',
}


def _gz(text: str) -> bytes:
    return gzip.compress(text.encode(), mtime=0)


BLOBS = {name: _gz(text) for name, text in CSV.items()}


def _pin(name: str, blob: bytes) -> data.DataFile:
    return data.DataFile(name, len(blob), hashlib.md5(blob).hexdigest(),
                         hashlib.sha256(blob).hexdigest())


class FakeZenodo:
    """Answers the record request and the file requests, and counts them."""

    def __init__(self, blobs, *, doi=data.VERSION_DOI, listed=None):
        self.blobs, self.doi, self.calls = blobs, doi, []
        self.listed = listed if listed is not None else {n: _pin(n, b) for n, b in blobs.items()}

    def record(self):
        return {'doi': self.doi, 'conceptdoi': data.CONCEPT_DOI, 'files': [
            {'key': f.name, 'size': f.size, 'checksum': 'md5:' + f.md5,
             'links': {'self': f'https://zenodo.org/api/records/1/files/{f.name}/content'}}
            for f in self.listed.values()]}

    def __call__(self, url):
        self.calls.append(url)
        if url == data.record_url(data.VERSION_DOI):
            return io.BytesIO(json.dumps(self.record()).encode())
        name = url.split('/files/', 1)[1].split('/', 1)[0]
        return io.BytesIO(self.blobs[name])


@pytest.fixture
def pinned(monkeypatch):
    files = tuple(_pin(n, b) for n, b in BLOBS.items())
    monkeypatch.setattr(data, 'FILES', files)
    return files


def test_record_url_reads_the_record_number_from_the_doi():
    assert data.record_url('10.5281/zenodo.23718893') == 'https://zenodo.org/api/records/23718893'
    with pytest.raises(data.DataError):
        data.record_url('10.1000/xyz123')


def test_the_pins_name_the_three_files_of_version_1_0_3():
    assert data.CONCEPT_DOI == '10.5281/zenodo.22048730'
    assert data.VERSION_DOI == '10.5281/zenodo.23718893'
    assert [f.name for f in data.FILES] == [
        'matches.csv.gz', 'players.csv.gz', 'points_sample_2026-06.csv.gz']
    for f in data.FILES:
        assert len(f.md5) == 32 and len(f.sha256) == 64


def test_download_fetches_checks_and_then_reuses(tmp_path, monkeypatch, pinned):
    fake = FakeZenodo(BLOBS)
    monkeypatch.setattr(data, '_get', fake)
    data.download(tmp_path, log=lambda *_: None)
    assert len(fake.calls) == 4
    for f in pinned:
        assert (tmp_path / f.name).read_bytes() == BLOBS[f.name]
    data.download(tmp_path, log=lambda *_: None)
    assert len(fake.calls) == 4, 'a second run must not touch the network'
    assert not list(tmp_path.glob('*.part'))


def test_a_corrupt_download_is_refused_and_never_kept(tmp_path, monkeypatch, pinned):
    bad = dict(BLOBS)
    bad['players.csv.gz'] = _gz(CSV['players.csv.gz'].replace('Player B', 'Player C'))
    monkeypatch.setattr(data, '_get', FakeZenodo(bad, listed={f.name: f for f in pinned}))
    with pytest.raises(data.DataError, match='players.csv.gz'):
        data.download(tmp_path, log=lambda *_: None)
    assert not (tmp_path / 'players.csv.gz').exists()
    assert not list(tmp_path.glob('*.part'))


def test_a_damaged_local_file_is_downloaded_again(tmp_path, monkeypatch, pinned):
    fake = FakeZenodo(BLOBS)
    monkeypatch.setattr(data, '_get', fake)
    data.download(tmp_path, log=lambda *_: None)
    (tmp_path / 'matches.csv.gz').write_bytes(b'not the file')
    data.download(tmp_path, log=lambda *_: None)
    assert (tmp_path / 'matches.csv.gz').read_bytes() == BLOBS['matches.csv.gz']


def test_another_version_of_the_record_is_refused(tmp_path, monkeypatch, pinned):
    monkeypatch.setattr(data, '_get', FakeZenodo(BLOBS, doi='10.5281/zenodo.99999999'))
    with pytest.raises(data.DataError, match='pinned version'):
        data.download(tmp_path, log=lambda *_: None)


def test_a_changed_checksum_on_the_record_is_refused(tmp_path, monkeypatch, pinned):
    listed = {f.name: f for f in pinned}
    listed['matches.csv.gz'] = data.DataFile('matches.csv.gz', 1, '0' * 32, '0' * 64)
    monkeypatch.setattr(data, '_get', FakeZenodo(BLOBS, listed=listed))
    with pytest.raises(data.DataError, match='different size or checksum'):
        data.download(tmp_path, log=lambda *_: None)


def test_a_file_from_another_host_is_refused(tmp_path, pinned):
    with pytest.raises(data.DataError, match='refusing'):
        data._download('https://example.com/matches.csv.gz', tmp_path / 'm.csv.gz', pinned[0])


def test_check_works_offline_and_names_the_missing_file(tmp_path, monkeypatch, pinned):
    with pytest.raises(data.DataError, match='missing'):
        data.check(tmp_path)
    monkeypatch.setattr(data, '_get', FakeZenodo(BLOBS))
    data.download(tmp_path, log=lambda *_: None)
    data.check(tmp_path)
    assert data.main(['--check', '--dir', str(tmp_path)]) == 0


def test_loaders_keep_scores_as_text_and_parse_times(tmp_path, monkeypatch, pinned):
    monkeypatch.setattr(data, '_get', FakeZenodo(BLOBS))
    data.download(tmp_path, log=lambda *_: None)
    pts = data.load_points(tmp_path)
    assert list(pts.points_p1) == ['0', '15', 'AD']
    assert pts.server.isna().tolist() == [False, False, True]
    assert str(pts.timestamp_utc.dtype).startswith('datetime64'), 'a row without a fraction'
    assert str(pts.timestamp_utc.dt.tz) == 'UTC'
    assert pts.timestamp_utc.iloc[2].second == 30
    assert pts.games_p1.iloc[2] == '[6, 6]'
    matches = data.load_matches(tmp_path)
    assert matches.best_of.iloc[0] == 'BO3'
    assert str(matches.scheduled_time_utc.dt.tz) == 'UTC'
    assert matches.tournament_key.iloc[0] == '5'
    assert data.load_players(tmp_path).name.tolist() == ['Player A', 'Player B']


def test_no_network_is_an_error_line_not_a_traceback(tmp_path, monkeypatch, pinned, capsys):
    def offline(url):
        raise OSError('no network')
    monkeypatch.setattr(data, '_get', offline)
    assert data.main(['--dir', str(tmp_path)]) == 1
    assert 'error: no network' in capsys.readouterr().err
    assert not list(tmp_path.glob('*.part'))


def test_redirects_stay_on_https():
    handler = data._HttpsOnlyRedirects()
    with pytest.raises(data.DataError, match='refusing a redirect'):
        handler.redirect_request(None, None, 302, 'Found', {}, 'http://zenodo.org/x')


def test_data_dir_follows_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv('CAPSTONE_DATA_DIR', str(tmp_path))
    assert data._default_dir() == tmp_path


def test_a_download_cut_off_half_way_is_an_error_line(tmp_path, monkeypatch, pinned, capsys):
    import http.client

    class Cut(io.BytesIO):
        def read(self, *args):
            raise http.client.IncompleteRead(b'', 10)

    fake = FakeZenodo(BLOBS)
    monkeypatch.setattr(data, '_get', lambda url: fake(url) if '/files/' not in url else Cut())
    assert data.main(['--dir', str(tmp_path)]) == 1
    assert capsys.readouterr().err.startswith('error: ')
    assert not list(tmp_path.glob('*.part'))
